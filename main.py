import json
import os
from datetime import date, timedelta
from html import escape
from pathlib import Path
from typing import Optional
import base64


import httpx
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from formatters import fmt, fmt_coupon, fmt_enum, fmt_par, cashflows_markdown, ref_markdown
from widgets import ALL_STATES, WIDGETS, stats_filter_params
from apps import build_apps



load_dotenv()

TERRAPIN_API_KEY = os.getenv("TERRAPIN_API_KEY", "")
TERRAPIN_BASE_URL = "https://terrapinfinance.com"

app = FastAPI(title="Muni Bond App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pro.openbb.co",
        "https://pro.openbb.dev",
        "http://localhost:1420",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import logging

logger = logging.getLogger("uvicorn")

@app.on_event("startup")
async def log_env_check():
    if TERRAPIN_API_KEY:
        masked = TERRAPIN_API_KEY[:4] + "..." + TERRAPIN_API_KEY[-4:] if len(TERRAPIN_API_KEY) > 8 else "****"
        logger.info(f"TERRAPIN_API_KEY is set (masked: {masked}, length: {len(TERRAPIN_API_KEY)})")
    else:
        logger.warning("TERRAPIN_API_KEY is NOT set in environment")

_NO_CACHE_HEADERS = {"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"}

TRADE_TYPE_META = {
    "customer_bought": {"label": "Customer Bought", "color": "#2196F3"},
    "customer_sold":   {"label": "Customer Sold",   "color": "#F44336"},
    "inter_dealer":    {"label": "Inter-Dealer",    "color": "#9C27B0"},
}

MUNI_STATS_PERIODS = {"all", "day", "week", "month", "quarter", "year"}
MUNI_STATS_GROUP_BYS = {
    "none",
    "state",
    "source_of_repayment",
    "rating_group",
    "interest_type",
    "seniority",
    "capital_purpose",
    "use_sectors",
    "use_categories",
    "uses_of_proceeds",
    "is_federally_taxable",
    "is_amt",
    "is_bank_qualified",
    "is_insured",
    "is_green",
    "is_social",
    "is_sustainable",
    "is_pac",
}
OUTSTANDING_METRIC_KEYS = ["outstanding_par_value", "cusip_count", "entity_count"]
ISSUANCE_METRIC_KEYS = ["new_issuance_par_value", "new_cusip_count", "issuer_count"]
TRADE_ACTIVITY_METRIC_KEYS = [
    "trade_volume",
    "trade_count",
    "customer_bought_count",
    "customer_sold_count",
    "inter_dealer_count",
]
TRADE_ACTIVITY_METRIC_LABELS = {
    "trade_volume": "Trade Volume",
    "trade_count": "Trade Count",
    "customer_bought_count": "Customer Bought Count",
    "customer_sold_count": "Customer Sold Count",
    "inter_dealer_count": "Inter-Dealer Count",
}
ISSUANCE_METRIC_LABELS = {
    "new_issuance_par_value": "New Issuance Par Value",
    "new_cusip_count": "New CUSIP Count",
    "issuer_count": "Issuer Count",
}
TOP_ISSUERS_RANK_BY_KEYS = {
    "trade_volume",
    "trade_count",
    "traded_cusip_count",
    "new_issuance_par_value",
    "new_cusip_count",
}
TOP_ISSUERS_RANK_BY_LABELS = {
    "trade_volume": "Trade Volume",
    "trade_count": "Trade Count",
    "traded_cusip_count": "Traded CUSIPs",
    "new_issuance_par_value": "New Issuance Par Value",
    "new_cusip_count": "New CUSIP Count",
}
OUTSTANDING_METRIC_LABELS = {
    "outstanding_par_value": "Outstanding Par Value",
    "cusip_count": "CUSIP Count",
    "entity_count": "Entity Count",
}
OUTPUT_MODES = {"raw", "chart"}
PERIOD_TITLE_LABELS = {
    "all": "All Periods",
    "day": "Day",
    "week": "Week",
    "month": "Month",
    "quarter": "Quarter",
    "year": "Year",
}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_terrapin_api_key(
    x_terrapin_api_key: Optional[str] = Header(None, alias="X-Terrapin-Api-Key"),
) -> str:
    """
    Reads the Terrapin API key from the incoming request header.
    Falls back to the server-side TERRAPIN_API_KEY env var if no header is provided.
    """
    key = x_terrapin_api_key or TERRAPIN_API_KEY
    if not key:
        raise HTTPException(
            status_code=401,
            detail="Missing Terrapin API key. Provide it via the X-Terrapin-Api-Key header or set TERRAPIN_API_KEY.",
        )
    return key


# ---------------------------------------------------------------------------
# Terrapin API helpers
# ---------------------------------------------------------------------------

def terrapin_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


# Reusable client — avoids opening a new TCP connection on every Terrapin call.
_http = httpx.Client(timeout=30)


def terrapin_post(
    path: str,
    api_key: str,
    payload: dict,
    *,
    timeout: float = 15,
) -> httpx.Response:
    """POST to Terrapin; turn network failures into clear HTTP errors."""
    try:
        return _http.post(
            f"{TERRAPIN_BASE_URL}{path}",
            headers=terrapin_headers(api_key),
            json=payload,
            timeout=timeout,
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail=f"Terrapin request timed out for {path}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Terrapin request failed for {path}: {exc}",
        ) from exc


def cusip_to_isin(cusip: str, api_key: str) -> str:
    cusip = cusip.strip().upper()
    resp = terrapin_post("/api/v1/convert_to_isin", api_key, {"identifiers": [cusip]})
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    isin = resp.json()["data"][0]["isin"]
    if isin is None:
        raise HTTPException(status_code=422, detail=f"'{cusip}' is not a valid CUSIP.")
    return isin


def _csv(v: Optional[str]) -> list:
    return [x.strip() for x in v.split(",") if x.strip()] if v else []


def _build_muni_stats_filters(
    states: Optional[str] = None,
    sources_of_repayment: Optional[str] = None,
    sectors: Optional[str] = None,
    interest_types: Optional[str] = None,
    use_categories: Optional[str] = None,
    uses_of_proceeds: Optional[str] = None,
    rating_group: Optional[str] = None,
    seniority: Optional[str] = None,
    capital_purpose: Optional[str] = None,
    is_federally_taxable: Optional[bool] = None,
    is_amt: Optional[bool] = None,
    is_bank_qualified: Optional[bool] = None,
    is_insured: Optional[bool] = None,
    is_green: Optional[bool] = None,
    is_social: Optional[bool] = None,
    is_sustainable: Optional[bool] = None,
    is_pac: Optional[bool] = None,
) -> dict:
    body: dict = {}
    if sl := [s for s in _csv(states) if s.upper() != ALL_STATES]:
        body["states"] = sl
    if sr := _csv(sources_of_repayment):
        body["sources_of_repayment"] = sr
    if sc := _csv(sectors):
        body["use_sectors"] = sc
    if it := _csv(interest_types):
        body["interest_types"] = it
    if uc := _csv(use_categories):
        body["use_categories"] = uc
    if uop := _csv(uses_of_proceeds):
        body["uses_of_proceeds"] = uop
    if rating_group:
        body["rating_group"] = rating_group
    if sn := _csv(seniority):
        body["seniority"] = sn
    if cp := _csv(capital_purpose):
        body["capital_purpose"] = cp
    if is_federally_taxable is not None:
        body["is_federally_taxable"] = is_federally_taxable
    if is_amt is not None:
        body["is_amt"] = is_amt
    if is_bank_qualified is not None:
        body["is_bank_qualified"] = is_bank_qualified
    if is_insured is not None:
        body["is_insured"] = is_insured
    if is_green is not None:
        body["is_green"] = is_green
    if is_social is not None:
        body["is_social"] = is_social
    if is_sustainable is not None:
        body["is_sustainable"] = is_sustainable
    if is_pac is not None:
        body["is_pac"] = is_pac
    return body


def _stats_filters_query(
    states: Optional[str] = Query(None),
    sources_of_repayment: Optional[str] = Query(None),
    sectors: Optional[str] = Query(None),
    interest_types: Optional[str] = Query(None),
    use_categories: Optional[str] = Query(None),
    uses_of_proceeds: Optional[str] = Query(None),
    rating_group: Optional[str] = Query(None),
    seniority: Optional[str] = Query(None),
    capital_purpose: Optional[str] = Query(None),
    is_federally_taxable: Optional[bool] = Query(None),
    is_amt: Optional[bool] = Query(None),
    is_bank_qualified: Optional[bool] = Query(None),
    is_insured: Optional[bool] = Query(None),
    is_green: Optional[bool] = Query(None),
    is_social: Optional[bool] = Query(None),
    is_sustainable: Optional[bool] = Query(None),
    is_pac: Optional[bool] = Query(None),
) -> dict:
    return {
        "states": states,
        "sources_of_repayment": sources_of_repayment,
        "sectors": sectors,
        "interest_types": interest_types,
        "use_categories": use_categories,
        "uses_of_proceeds": uses_of_proceeds,
        "rating_group": rating_group,
        "seniority": seniority,
        "capital_purpose": capital_purpose,
        "is_federally_taxable": is_federally_taxable,
        "is_amt": is_amt,
        "is_bank_qualified": is_bank_qualified,
        "is_insured": is_insured,
        "is_green": is_green,
        "is_social": is_social,
        "is_sustainable": is_sustainable,
        "is_pac": is_pac,
    }


def _post_muni_stats_rows(endpoint: str, body: dict, api_key: str) -> list[dict]:
    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{TERRAPIN_BASE_URL}/api/v1/{endpoint}",
                headers=terrapin_headers(api_key),
                json=body,
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail=f"Terrapin stats request timed out for {endpoint}.") from exc
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json().get("data", [])
    if not data:
        raise HTTPException(status_code=404, detail="No statistics found for the selected filters.")
    return data


def _validated_period(period: Optional[str]) -> str:
    p = (period or "all").strip().lower()
    if p not in MUNI_STATS_PERIODS:
        raise HTTPException(status_code=422, detail=f"Invalid period '{period}'.")
    return p


def _metric_period_title(metric_label: str, period: str) -> str:
    period_label = PERIOD_TITLE_LABELS.get(period, period.title())
    return f"{metric_label} by {period_label}"


def _validated_group_by(group_by: Optional[str]) -> str:
    g = (group_by or "none").strip().lower()
    if g not in MUNI_STATS_GROUP_BYS:
        raise HTTPException(status_code=422, detail=f"Invalid group_by '{group_by}'.")
    return g


def _group_by_for_api(group_by: str) -> str:
    return group_by


def _validated_rank_by(rank_by: Optional[str]) -> str:
    r = (rank_by or "trade_volume").strip().lower()
    if r not in TOP_ISSUERS_RANK_BY_KEYS:
        raise HTTPException(status_code=422, detail=f"Invalid rank_by '{rank_by}'.")
    return r


def _validated_output_mode(output: Optional[str]) -> str:
    o = (output or "raw").strip().lower()
    if o not in OUTPUT_MODES:
        raise HTTPException(status_code=422, detail=f"Invalid output '{output}'. Use 'raw' or 'chart'.")
    return o


def _selected_metric_keys(metrics: Optional[str], allowed_keys: list[str]) -> list[str]:
    selected = _csv(metrics)
    if not selected:
        return allowed_keys

    allowed_set = set(allowed_keys)
    invalid = [m for m in selected if m not in allowed_set]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Invalid metrics: {', '.join(invalid)}.")

    deduped = []
    seen = set()
    for m in selected:
        if m not in seen:
            deduped.append(m)
            seen.add(m)
    if len(deduped) > 1:
        raise HTTPException(status_code=422, detail="Please select only one metric.")
    return deduped


def _categorical_bar_chart(
    rows: list[dict],
    *,
    metric_key: str,
    metric_label: str,
    group_by: str,
    theme: str = "dark",
    title: Optional[str] = None,
) -> dict:
    if not rows:
        return {"data": [], "layout": {}}

    x_axis = []
    y_vals = []
    for r in rows:
        if group_by != "none":
            x_val = str(r.get("group_key") if r.get("group_key") is not None else "undefined")
        else:
            x_val = "all"
        x_axis.append(x_val)
        y_vals.append(float(r.get(metric_key) or 0))

    is_dark = theme.strip().lower() == "dark"
    bg_color = "#151518" if is_dark else "#FFFFFF"
    grid_color = "#2A2A2A" if is_dark else "#E5E7EB"
    text_color = "#CCCCCC" if is_dark else "#1F2937"
    title_color = "#FFFFFF" if is_dark else "#000000"

    annotations = []
    if title and title.strip():
        annotations.append(
            {
                "text": f"<b>{title.strip()}</b>",
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": 1.1,
                "xanchor": "left",
                "yanchor": "bottom",
                "showarrow": False,
                "font": {"color": title_color, "size": 25},
                "yshift": 8,
            }
        )

    return {
        "data": [
            {
                "type": "bar",
                "name": metric_label,
                "x": x_axis,
                "y": y_vals,
                "hovertemplate": "<b>%{x}</b><br>" + metric_label + ": %{y:,.2f}<extra></extra>",
            }
        ],
        "layout": {
            "plot_bgcolor": bg_color,
            "paper_bgcolor": bg_color,
            "font": {"color": text_color},
            "xaxis": {
                "title": {"text": ""},
                "gridcolor": grid_color,
                "linecolor": grid_color,
                "tickfont": {"color": text_color},
            },
            "yaxis": {
                "title": {"text": metric_label},
                "gridcolor": grid_color,
                "linecolor": grid_color,
                "tickfont": {"color": text_color},
            },
            "hovermode": "x unified",
            "annotations": annotations,
        },
    }


def _stacked_bar_chart(
    rows: list[dict],
    *,
    metric_key: str,
    metric_label: str,
    period: str,
    group_by: str,
    theme: str = "dark",
    title: Optional[str] = None,
) -> dict:
    if not rows:
        return {"data": [], "layout": {}}

    x_axis: list[str] = []
    grouped: dict[str, dict[str, float]] = {}
    for r in rows:
        x = str(r.get("period") or "all")
        if x not in x_axis:
            x_axis.append(x)
        group = str(r.get("group_key")) if group_by != "none" and r.get("group_key") is not None else "undefined"
        grouped.setdefault(group, {})
        grouped[group][x] = float(r.get(metric_key) or 0)

    traces = []
    for group, values in grouped.items():
        traces.append(
            {
                "type": "bar",
                "name": group,
                "x": x_axis,
                "y": [values.get(x, 0) for x in x_axis],
                "hovertemplate": "<b>%{x}</b><br>" + metric_label + ": %{y:,.2f}<extra>" + group + "</extra>",
            }
        )

    is_dark = theme.strip().lower() == "dark"
    bg_color = "#151518" if is_dark else "#FFFFFF"
    grid_color = "#2A2A2A" if is_dark else "#E5E7EB"
    text_color = "#CCCCCC" if is_dark else "#1F2937"
    title_color = "#FFFFFF" if is_dark else "#000000"

    annotations = []
    if title and title.strip():
        annotations.append(
            {
                "text": f"<b>{title.strip()}</b>",
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": 1.1,
                "xanchor": "left",
                "yanchor": "bottom",
                "showarrow": False,
                "font": {"color": title_color, "size": 25},
                "yshift": 8,
            }
        )

    return {
        "data": traces,
        "layout": {
            "barmode": "stack",
            "plot_bgcolor": bg_color,
            "paper_bgcolor": bg_color,
            "font": {"color": text_color},
            "xaxis": {
                "title": {"text": ""},
                "gridcolor": grid_color,
                "linecolor": grid_color,
                "tickfont": {"color": text_color},
            },
            "yaxis": {
                "title": {"text": metric_label},
                "gridcolor": grid_color,
                "linecolor": grid_color,
                "tickfont": {"color": text_color},
            },
            "legend": {"orientation": "h", "y": -0.2, "font": {"color": text_color}},
            "hovermode": "x unified",
            "annotations": annotations,
        },
    }


def _stats_rows_for_aggrid_chart(
    rows: list[dict],
    *,
    metric_key: str,
    metric_label: str,
    period: str,
    group_by: str,
) -> list[dict]:
    if not rows:
        return []

    period_values: list[str] = []
    group_values: list[str] = []
    grouped_values: dict[str, dict[str, float]] = {}
    for row in rows:
        period_value = str(row.get("period") or "all") if period != "all" else "all"
        group_value = (
            str(row.get("group_key") if row.get("group_key") is not None else "undefined")
            if group_by != "none"
            else metric_label
        )
        if period_value not in period_values:
            period_values.append(period_value)
        if group_value not in group_values:
            group_values.append(group_value)
        grouped_values.setdefault(period_value, {})[group_value] = float(row.get(metric_key) or 0)

    return [
        {
            "period": period_value,
            **{
                group_value: grouped_values.get(period_value, {}).get(group_value, 0)
                for group_value in group_values
            },
        }
        for period_value in period_values
    ]


# ---------------------------------------------------------------------------
# Manifest endpoints
# ---------------------------------------------------------------------------

@app.get("/widgets.json")
def get_widgets():
    return JSONResponse(content=WIDGETS, headers=_NO_CACHE_HEADERS)


@app.get("/apps.json")
def get_apps():
    return JSONResponse(content=build_apps(), headers=_NO_CACHE_HEADERS)


@app.get("/agents.json")
def get_agents():
    return JSONResponse(content={}, headers=_NO_CACHE_HEADERS)


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

@app.get("/muni/reference")
def muni_reference(
    cusip: str = Query(..., description="9-character CUSIP"),
    api_key: str = Depends(get_terrapin_api_key),
):
    isin = cusip_to_isin(cusip, api_key)

    resp = terrapin_post("/api/v1/muni_reference", api_key, {"isins": [isin]})
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json().get("data", [])
    if not data:
        raise HTTPException(status_code=404, detail="No reference data found.")

    return PlainTextResponse(ref_markdown(data[0], cusip))


# ---------------------------------------------------------------------------
# Pricing history chart
# ---------------------------------------------------------------------------

@app.get("/muni/pricing_chart")
def muni_pricing_chart(
    cusip: str = Query(..., description="9-character CUSIP"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    raw: bool = Query(False),
    theme: str = Query("dark", description="OpenBB workspace theme (dark/light)"),
    api_key: str = Depends(get_terrapin_api_key),
):
    today = date.today()
    if not end_date:
        end_date = today.isoformat()
    if not start_date:
        start_date = (today - timedelta(days=365)).isoformat()

    isin = cusip_to_isin(cusip, api_key)

    resp = terrapin_post(
        "/api/v1/muni_pricing_history",
        api_key,
        {"isin": isin, "start_date": start_date, "end_date": end_date},
        timeout=20,
    )
    if resp.status_code != 200:
        logger.warning("muni_pricing_history failed (%s): %s", resp.status_code, resp.text[:200])
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    trades = resp.json().get("data", [])

    if raw:
        return trades

    if not trades:
        raise HTTPException(
            status_code=404,
            detail=f"No pricing history found for {cusip} between {start_date} and {end_date}.",
        )

    trades = sorted(trades, key=lambda t: t["trade_datetime"])

    buckets: dict[str, dict] = {}
    for t in trades:
        tt = t.get("trade_type", "unknown")
        meta = TRADE_TYPE_META.get(tt, {"label": tt.replace("_", " ").title(), "color": "#78909C"})
        if tt not in buckets:
            buckets[tt] = {"x": [], "y": [], "customdata": [], "label": meta["label"], "color": meta["color"]}
        ytm = t.get("ytm_semi_annual")
        amt = t.get("amount")
        buckets[tt]["x"].append(t["trade_datetime"])
        buckets[tt]["y"].append(t["price"])
        buckets[tt]["customdata"].append([
            f"{ytm:.4f}%" if ytm is not None else "n/a",
            f"{int(amt):,}" if amt is not None else "n/a",
        ])

    traces = [
        {
            "type": "scatter",
            "mode": "markers",
            "name": b["label"],
            "x": b["x"],
            "y": b["y"],
            "customdata": b["customdata"],
            "marker": {"size": 8, "color": b["color"], "opacity": 0.85},
            "hovertemplate": (
                "<b>%{x|%Y-%m-%d %H:%M}</b><br>"
                "Price: %{y:.3f}<br>"
                "MSRB Yield: %{customdata[0]}<br>"
                "Volume: %{customdata[1]}"
                "<extra>" + b["label"] + "</extra>"
            ),
        }
        for b in buckets.values()
    ]

    is_dark = theme.strip().lower() == "dark"
    bg_color = "#151518" if is_dark else "#FFFFFF"
    grid_color = "#2A2A2A" if is_dark else "#E5E7EB"
    text_color = "#CCCCCC" if is_dark else "#1F2937"

    return {
        "data": traces,
        "layout": {
            "plot_bgcolor": bg_color,
            "paper_bgcolor": bg_color,
            "font": {"color": text_color},
            "xaxis": {"title": {"text": "Trade Date"}, "gridcolor": grid_color, "linecolor": grid_color, "tickfont": {"color": text_color}},
            "yaxis": {"title": {"text": "Price"}, "gridcolor": grid_color, "linecolor": grid_color, "tickfont": {"color": text_color}},
            "legend": {"orientation": "h", "y": -0.15, "font": {"color": text_color}},
            "hovermode": "closest",
        },
    }


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

@app.get("/muni/documents/options")
def muni_documents_options(
    cusip: str = Query(..., description="9-character CUSIP"),
    api_key: str = Depends(get_terrapin_api_key),
):
    """Returns [{label, value}] for the multi_file_viewer file selector."""
    isin = cusip_to_isin(cusip, api_key)
    rows = []
    upstream_errors: list[str] = []

    for doc_type in ("official_statement", "disclosure_document"):
        resp = terrapin_post(
            "/api/v1/muni_documents",
            api_key,
            {"isin": isin, "document_type": doc_type},
        )
        if resp.status_code == 200:
            rows.extend(resp.json().get("data", []))
        else:
            logger.warning(
                "muni_documents(%s) failed for %s (%s): %s",
                doc_type,
                cusip,
                resp.status_code,
                resp.text[:200],
            )
            upstream_errors.append(f"{doc_type}: HTTP {resp.status_code}")

    options = [
        {"label": d.get("document_name") or d["file_id"], "value": d["file_id"]}
        for d in rows
        if d.get("file_id")
    ]

    if not options and upstream_errors:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch documents for {cusip} ({'; '.join(upstream_errors)}).",
        )
    if not options:
        raise HTTPException(status_code=404, detail=f"No documents found for {cusip}.")

    return options


# ---------------------------------------------------------------------------
# Cashflows
# ---------------------------------------------------------------------------

@app.get("/muni/cashflows")
def muni_cashflows(
    cusip: str = Query(..., description="9-character CUSIP"),
    api_key: str = Depends(get_terrapin_api_key),
):
    isin = cusip_to_isin(cusip, api_key)

    cf_resp = terrapin_post("/api/v1/muni_cashflows", api_key, {"isins": [isin]})

    if cf_resp.status_code != 200:
        raise HTTPException(status_code=cf_resp.status_code, detail=cf_resp.text)

    cf_data = cf_resp.json().get("data", [])
    if not cf_data:
        raise HTTPException(status_code=404, detail=f"No cashflow data available for {cusip}.")

    cashflows = sorted(cf_data[0]["cashflows"], key=lambda c: (c["date"], c["type"]))
    return PlainTextResponse(cashflows_markdown(cashflows))


# ---------------------------------------------------------------------------
# Bond search
# ---------------------------------------------------------------------------

@app.get("/muni/search")
def muni_search(
    issuer_name: Optional[str] = Query(None),
    states: Optional[str] = Query(None),
    sectors: Optional[str] = Query(None),
    coupon_min: Optional[float] = Query(None),
    coupon_max: Optional[float] = Query(None),
    maturity_date_min: Optional[str] = Query(None),
    maturity_date_max: Optional[str] = Query(None),
    interest_types: Optional[str] = Query(None),
    sources_of_repayment: Optional[str] = Query(None),
    is_insured: Optional[bool] = Query(None),
    include_callable: Optional[bool] = Query(None),
    last_traded_since: Optional[str] = Query(None),
    limit: int = Query(100),
    api_key: str = Depends(get_terrapin_api_key),
):
    body: dict = {
        "limit": limit,
        "sort": ["-issue_date"],
        # Terrapin defaults to OS-only; set explicitly so Bond Explorer never
        # returns bonds without a final official statement.
        "include_bonds_without_os": False,
    }
    if issuer_name:                                body["issuer_name"] = issuer_name
    if sl := [s for s in _csv(states) if s.upper() != ALL_STATES]: body["states"] = sl
    if sc := _csv(sectors):                         body["sectors"] = sc
    if coupon_min is not None:                     body["coupon_min"] = coupon_min
    if coupon_max is not None:                     body["coupon_max"] = coupon_max
    if maturity_date_min:                          body["maturity_date_min"] = maturity_date_min
    if maturity_date_max:                          body["maturity_date_max"] = maturity_date_max
    if it := _csv(interest_types):                  body["interest_types"] = it
    if sr := _csv(sources_of_repayment):            body["sources_of_repayment"] = sr
    if is_insured is not None:                     body["is_insured"] = is_insured
    if include_callable is not None:               body["include_callable"] = include_callable
    if last_traded_since:                          body["last_traded_since"] = last_traded_since

    resp = terrapin_post("/api/v1/muni_search", api_key, body, timeout=20)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return [
        {
            "cusip":           b["isin"][2:11],
            "ticker":          b.get("ticker") or "—",
            "issuer_name":     b.get("issuer_name") or "—",
            "state":           b.get("state") or "—",
            "coupon":          fmt_coupon(b.get("interest_rate")),
            "interest_type":   fmt_enum(b.get("interest_type")),
            "maturity_date":   b.get("maturity_date") or "—",
            "callable":        "Yes" if b.get("is_callable") else "No",
            "rating":          fmt_enum(b.get("rating_group")),
            "has_os":          "Yes" if b.get("has_official_statement") else "No",
        }
        for b in resp.json().get("data", [])
    ]


# ---------------------------------------------------------------------------
# Market statistics
# ---------------------------------------------------------------------------

@app.get("/muni/stats/filters_summary", response_class=HTMLResponse)
def muni_stats_filters_summary(
    filters: dict = Depends(_stats_filters_query),
    theme: str = Query("dark", description="OpenBB workspace theme (dark/light)"),
):
    filter_sections = [
        ("Geography & Credit", ["states", "sources_of_repayment", "rating_group"]),
        ("Use of Funds", ["sectors", "use_categories", "uses_of_proceeds"]),
        ("Structure", ["interest_types", "seniority", "capital_purpose"]),
        (
            "Flags",
            [
                "is_federally_taxable",
                "is_amt",
                "is_bank_qualified",
                "is_insured",
                "is_green",
                "is_social",
                "is_sustainable",
                "is_pac",
            ],
        ),
    ]
    param_defs = {param["paramName"]: param for param in stats_filter_params()}

    def _normalise_value(param_name: str, value: object) -> str:
        if param_name == "states":
            return str(value or ALL_STATES)
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return ""
        return str(value)

    def _default_value(param_name: str) -> str:
        return ALL_STATES if param_name == "states" else ""

    def _control(param_name: str) -> dict:
        param = param_defs[param_name]
        options = []
        for option in param.get("options", []):
            options.append(
                {
                    "label": option.get("label") or option.get("value") or "All",
                    "value": option.get("value") or "",
                    "description": (option.get("extraInfo") or {}).get("description", ""),
                }
            )

        if not param.get("multiSelect") and not any(option["value"] == "" for option in options):
            options.insert(
                0,
                {
                    "label": f"All {param.get('label', param_name)}",
                    "value": "",
                    "description": f"Do not filter by {param.get('label', param_name).lower()}.",
                },
            )

        option_values = {option["value"] for option in options}
        return {
            "name": param_name,
            "label": param.get("label", param_name),
            "description": param.get("description", ""),
            "multiSelect": bool(param.get("multiSelect")),
            "isTernaryBoolean": option_values == {"", "true", "false"},
            "defaultValue": _default_value(param_name),
            "value": _normalise_value(param_name, filters.get(param_name)),
            "options": options,
        }

    controls = [
        {
            "title": section_title,
            "controls": [_control(param_name) for param_name in param_names],
        }
        for section_title, param_names in filter_sections
    ]
    controls_json = json.dumps(controls)
    initial_state = {
        control["name"]: control["value"]
        for section in controls
        for control in section["controls"]
    }
    initial_state_json = json.dumps(initial_state)
    resolved_theme = "light" if theme.strip().lower() == "light" else "dark"

    html = f"""<!doctype html>
<html lang="en" data-theme="{resolved_theme}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
  color-scheme: dark light;
  --bg: #131417;
  --surface: #1c1e23;
  --surface-soft: #252932;
  --border: rgba(255,255,255,.12);
  --text: #f5f5f5;
  --muted: #a9adb8;
  --accent: #4da3ff;
  --accent-soft: rgba(77,163,255,.16);
  --danger: #ff6f61;
}}
:root[data-theme="light"] {{
  --bg: #ffffff;
  --surface: #f5f7fa;
  --surface-soft: #eef2f7;
  --border: rgba(24,31,42,.14);
  --text: #1f2937;
  --muted: #596273;
  --accent: #0b66c3;
  --accent-soft: rgba(11,102,195,.12);
  --danger: #b42318;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  padding: 8px 10px 10px;
  background: var(--bg);
  color: var(--text);
  font: 12px/1.3 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  overflow: auto;
}}
.header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}}
.count {{
  color: var(--text);
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 7px;
}}
.filter-section {{
  min-width: 0;
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: 7px;
  padding: 6px;
}}
.filter-section.flags {{
  grid-column: 1 / -1;
}}
.filter-section.flags .controls {{
  grid-template-columns: repeat(4, minmax(0, 1fr));
}}
.filter-section.flags .description {{
  -webkit-line-clamp: 1;
}}
h2 {{
  margin: 0 0 4px;
  color: var(--muted);
  font-size: 10px;
  font-weight: 650;
  letter-spacing: .04em;
  text-transform: uppercase;
}}
.controls {{
  display: grid;
  gap: 5px;
}}
.control {{
  min-width: 0;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface-soft);
  padding: 5px;
}}
.control.active {{
  border-color: color-mix(in srgb, var(--accent) 58%, transparent);
  background: var(--accent-soft);
}}
.control-head {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 6px;
  align-items: center;
}}
.label {{
  color: var(--text);
  font-weight: 620;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.value {{
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: right;
}}
.description {{
  color: var(--muted);
  font-size: 10.5px;
  margin: 3px 0 5px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}
.select-row {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 5px;
}}
select {{
  width: 100%;
  min-width: 0;
  height: 24px;
  border: 1px solid var(--border);
  border-radius: 5px;
  background: var(--bg);
  color: var(--text);
  font: inherit;
  padding: 0 6px;
}}
button {{
  height: 24px;
  border: 1px solid var(--border);
  border-radius: 5px;
  background: var(--surface);
  color: var(--text);
  font: inherit;
  cursor: pointer;
}}
button:hover, select:hover {{
  border-color: color-mix(in srgb, var(--accent) 52%, var(--border));
}}
.segments {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 4px;
}}
.segments.boolean {{
  grid-template-columns: repeat(2, minmax(0, 1fr));
}}
.segments button {{
  min-width: 0;
  padding: 0 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.segments button.selected {{
  border-color: var(--accent);
  background: var(--accent-soft);
}}
.chips {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 5px;
}}
.selected-chip {{
  max-width: 100%;
  height: 20px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 5px;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
}}
.selected-chip span {{
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.selected-chip b {{
  color: var(--danger);
  font-weight: 700;
}}
.clear {{
  padding: 0 7px;
  color: var(--muted);
}}
.clear-all {{
  padding: 0 8px;
  color: var(--muted);
}}
.header-actions {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
}}
@media (max-width: 760px) {{
  .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .filter-section.flags .controls {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
@media (max-width: 520px) {{
  body {{ padding: 8px; }}
  .grid {{ grid-template-columns: 1fr; }}
  .filter-section.flags .controls {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
  <div class="header">
    <div class="count" id="count">0 active filters</div>
    <div class="header-actions">
      <button class="clear-all" data-action="clear-all">Clear all</button>
    </div>
  </div>
  <main class="grid" id="filters"></main>
  <script>
    (() => {{
      const sections = {controls_json};
      const state = {initial_state_json};
      const controls = sections.flatMap((section) => section.controls);
      const byName = new Map(controls.map((control) => [control.name, control]));
      const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\\"": "&quot;",
        "'": "&#39;"
      }}[char]));
      const splitValues = (value) => String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
      const selectedValues = (control) => {{
        const raw = state[control.name] ?? control.defaultValue ?? "";
        if (control.name === "states" && (!raw || raw === "ALL")) return [];
        if (!raw) return [];
        return splitValues(raw).filter((value) => value !== "ALL");
      }};
      const optionLabel = (control, value) => {{
        const option = control.options.find((item) => item.value === value);
        return option?.label || value || `All ${{control.label}}`;
      }};
      const isActive = (control) => {{
        const raw = state[control.name] ?? control.defaultValue ?? "";
        if (control.name === "states") return Boolean(raw && raw !== "ALL");
        return raw !== "";
      }};
      const displayValue = (control) => {{
        if (control.multiSelect) {{
          const values = selectedValues(control);
          if (values.length === 0) return control.name === "states" ? "All States" : "All";
          return values.map((value) => optionLabel(control, value)).join(", ");
        }}
        if (control.isTernaryBoolean && !(state[control.name] ?? "")) return "Any";
        return optionLabel(control, state[control.name] ?? control.defaultValue ?? "");
      }};
      const activeCount = () => controls.reduce((count, control) => count + (isActive(control) ? 1 : 0), 0);
      const serialiseParams = () => Object.fromEntries(
        controls.map((control) => [control.name, state[control.name] ?? control.defaultValue ?? ""])
      );
      const emitParams = (paramName) => {{
        const params = serialiseParams();
        const message = {{
          type: "openbb:widget-params:update",
          paramName,
          value: paramName === "*" ? undefined : params[paramName],
          params
        }};
        window.dispatchEvent(new CustomEvent("openbb:widget-params:update", {{ detail: message }}));
        if (window.parent && window.parent !== window) {{
          window.parent.postMessage(message, "*");
        }}
      }};
      const setValue = (control, value) => {{
        state[control.name] = value || control.defaultValue || "";
        if (control.name === "states" && !state[control.name]) state[control.name] = "ALL";
      }};
      const toggleMultiValue = (control, value) => {{
        if (!value || value === control.defaultValue) {{
          setValue(control, control.defaultValue);
          return;
        }}
        const values = selectedValues(control);
        const next = values.includes(value)
          ? values.filter((item) => item !== value)
          : [...values, value];
        setValue(control, next.length ? next.join(",") : control.defaultValue);
      }};
      const multiControl = (control) => {{
        const chips = selectedValues(control).map((value) => `
          <button class="selected-chip" data-action="remove" data-param="${{esc(control.name)}}" data-value="${{esc(value)}}" title="Remove ${{esc(optionLabel(control, value))}}">
            <span>${{esc(optionLabel(control, value))}}</span><b>x</b>
          </button>
        `).join("");
        const options = control.options.map((option) => `
          <option value="${{esc(option.value)}}" title="${{esc(option.description)}}">${{esc(option.label)}}</option>
        `).join("");
        return `
          <div class="chips">${{chips || `<span class="value">${{control.name === "states" ? "All States" : "All values"}}</span>`}}</div>
          <div class="select-row">
            <select data-action="select" data-param="${{esc(control.name)}}" aria-label="${{esc(control.label)}}">
              <option value="">Add or toggle...</option>
              ${{options}}
            </select>
            <button class="clear" data-action="clear" data-param="${{esc(control.name)}}">Clear</button>
          </div>
        `;
      }};
      const singleOptions = (control) => control.isTernaryBoolean
        ? control.options.filter((option) => option.value !== "")
        : control.options;
      const singleOptionLabel = (control, option) => control.isTernaryBoolean
        ? option.label.replace(/^(Yes|No):.*$/, "$1")
        : option.label.replace(/^All /, "All ");
      const segmentControl = (control) => `
        <div class="segments ${{control.isTernaryBoolean ? "boolean" : ""}}">
          ${{singleOptions(control).map((option) => `
            <button data-action="set" data-param="${{esc(control.name)}}" data-value="${{esc(option.value)}}"
              class="${{(state[control.name] ?? "") === option.value ? "selected" : ""}}"
              title="${{esc(option.description)}}">
              ${{esc(singleOptionLabel(control, option))}}
            </button>
          `).join("")}}
        </div>
      `;
      const singleSelectControl = (control) => {{
        const selected = state[control.name] ?? control.defaultValue ?? "";
        const hasBlankOption = control.options.some((option) => option.value === "");
        const blankOption = control.name === "states" || hasBlankOption
          ? ""
          : `<option value="" ${{!selected ? "selected" : ""}}>All ${{esc(control.label)}}</option>`;
        const options = control.options.map((option) => `
          <option value="${{esc(option.value)}}"
            ${{selected === option.value ? "selected" : ""}}
            title="${{esc(option.description)}}">
            ${{esc(option.label)}}
          </option>
        `).join("");
        return `
          <div class="select-row">
            <select data-action="single-select" data-param="${{esc(control.name)}}" aria-label="${{esc(control.label)}}">
              ${{blankOption}}
              ${{options}}
            </select>
            <button class="clear" data-action="clear" data-param="${{esc(control.name)}}">Clear</button>
          </div>
        `;
      }};
      const singleControl = (control) => control.isTernaryBoolean
        ? segmentControl(control)
        : singleSelectControl(control);
      const controlMarkup = (control) => `
        <article class="control ${{isActive(control) ? "active" : ""}}" data-control="${{esc(control.name)}}">
          <div class="control-head">
            <div class="label" title="${{esc(control.label)}}">${{esc(control.label)}}</div>
            <div class="value" title="${{esc(displayValue(control))}}">${{esc(displayValue(control))}}</div>
          </div>
          <p class="description" title="${{esc(control.description)}}">${{esc(control.description)}}</p>
          ${{control.multiSelect ? multiControl(control) : singleControl(control)}}
        </article>
      `;
      const render = () => {{
        document.getElementById("count").textContent = `${{activeCount()}} active filters`;
        document.getElementById("filters").innerHTML = sections.map((section) => `
          <section class="filter-section ${{section.title === "Flags" ? "flags" : ""}}">
            <h2>${{esc(section.title)}}</h2>
            <div class="controls">${{section.controls.map(controlMarkup).join("")}}</div>
          </section>
        `).join("");
      }};
      document.addEventListener("change", (event) => {{
        const target = event.target.closest("[data-action='select'], [data-action='single-select']");
        if (!target) return;
        const control = byName.get(target.dataset.param);
        if (!control) return;
        if (target.dataset.action === "single-select") {{
          setValue(control, target.value);
        }} else {{
          toggleMultiValue(control, target.value);
          target.value = "";
        }}
        render();
        emitParams(control.name);
      }});
      document.addEventListener("click", (event) => {{
        const target = event.target.closest("[data-action]");
        if (!target || target.dataset.action === "select" || target.dataset.action === "single-select") return;
        if (target.dataset.action === "clear-all") {{
          controls.forEach((control) => setValue(control, control.defaultValue));
          render();
          emitParams("*");
          return;
        }}
        const control = byName.get(target.dataset.param);
        if (!control) return;
        if (target.dataset.action === "clear") setValue(control, control.defaultValue);
        if (target.dataset.action === "remove") toggleMultiValue(control, target.dataset.value);
        if (target.dataset.action === "set") {{
          const nextValue = control.isTernaryBoolean && (state[control.name] ?? "") === target.dataset.value
            ? control.defaultValue
            : target.dataset.value;
          setValue(control, nextValue);
        }}
        render();
        emitParams(control.name);
      }});
      render();
    }})();
  </script>
</body>
</html>"""
    return HTMLResponse(content=html, headers=_NO_CACHE_HEADERS)


@app.get("/muni/stats/outstanding")
def muni_stats_outstanding(
    metrics: Optional[str] = Query(None, description="Single metric key"),
    output: str = Query("raw", description="Response mode: raw rows or chart"),
    group_by: str = Query("none"),
    filters: dict = Depends(_stats_filters_query),
    theme: str = Query("dark", description="OpenBB workspace theme (dark/light)"),
    title: Optional[str] = Query(None, description="Optional chart title annotation"),
    api_key: str = Depends(get_terrapin_api_key),
):
    output = _validated_output_mode(output)
    group_by = _validated_group_by(group_by)
    api_group_by = _group_by_for_api(group_by)
    metric_key = _selected_metric_keys(metrics, OUTSTANDING_METRIC_KEYS)[0]
    body = _build_muni_stats_filters(**filters)
    body["group_by"] = api_group_by

    rows = _post_muni_stats_rows("muni_stats_outstanding", body, api_key)
    raw_rows = [
        {
            **({"group_key": r.get("group_key")} if group_by != "none" and r.get("group_key") is not None else {}),
            metric_key: r.get(metric_key),
        }
        for r in rows
    ]
    if output == "chart":
        return _categorical_bar_chart(
            raw_rows,
            metric_key=metric_key,
            metric_label=OUTSTANDING_METRIC_LABELS[metric_key],
            group_by=group_by,
            theme=theme,
            title=title,
        )
    return raw_rows


@app.get("/muni/stats/issuance")
def muni_stats_issuance(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    metrics: Optional[str] = Query(None, description="Single metric key"),
    output: str = Query("raw", description="Response mode: raw rows or chart"),
    period: str = Query("month"),
    group_by: str = Query("none"),
    filters: dict = Depends(_stats_filters_query),
    theme: str = Query("dark", description="OpenBB workspace theme (dark/light)"),
    title: Optional[str] = Query(None, description="Optional chart title annotation"),
    api_key: str = Depends(get_terrapin_api_key),
):
    output = _validated_output_mode(output)
    period = _validated_period(period)
    group_by = _validated_group_by(group_by)
    api_group_by = _group_by_for_api(group_by)
    metric_key = _selected_metric_keys(metrics, ISSUANCE_METRIC_KEYS)[0]
    body = _build_muni_stats_filters(**filters)
    body["start_date"] = start_date
    body["end_date"] = end_date
    body["period"] = period
    body["group_by"] = api_group_by

    rows = _post_muni_stats_rows("muni_stats_issuance", body, api_key)
    raw_rows = [
        {
            **({"period": r.get("period")} if period != "all" and r.get("period") is not None else {}),
            **({"group_key": r.get("group_key")} if period != "all" and group_by != "none" and r.get("group_key") is not None else {}),
            metric_key: r.get(metric_key),
        }
        for r in rows
    ]
    if output == "chart":
        dynamic_title = _metric_period_title(ISSUANCE_METRIC_LABELS[metric_key], period)
        resolved_title = title.strip() if title and title.strip() else dynamic_title
        return _stacked_bar_chart(
            rows,
            metric_key=metric_key,
            metric_label=ISSUANCE_METRIC_LABELS[metric_key],
            period=period,
            group_by=group_by,
            theme=theme,
            title=resolved_title,
        )
    return raw_rows


@app.get("/muni/stats/trade_activity")
def muni_stats_trade_activity(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    metrics: Optional[str] = Query(None, description="Single metric key"),
    output: str = Query("raw", description="Response mode: raw rows or chart"),
    period: str = Query("month"),
    group_by: str = Query("none"),
    filters: dict = Depends(_stats_filters_query),
    theme: str = Query("dark", description="OpenBB workspace theme (dark/light)"),
    title: Optional[str] = Query(None, description="Optional chart title annotation"),
    api_key: str = Depends(get_terrapin_api_key),
):
    output = _validated_output_mode(output)
    period = _validated_period(period)
    group_by = _validated_group_by(group_by)
    api_group_by = _group_by_for_api(group_by)
    metric_key = _selected_metric_keys(metrics, TRADE_ACTIVITY_METRIC_KEYS)[0]
    body = _build_muni_stats_filters(**filters)
    body["start_date"] = start_date
    body["end_date"] = end_date
    body["period"] = period
    body["group_by"] = api_group_by

    rows = _post_muni_stats_rows("muni_stats_trade_activity", body, api_key)
    raw_rows = [
        {
            **({"period": r.get("period")} if period != "all" and r.get("period") is not None else {}),
            **({"group_key": r.get("group_key")} if period != "all" and group_by != "none" and r.get("group_key") is not None else {}),
            metric_key: r.get(metric_key),
        }
        for r in rows
    ]
    if output == "chart":
        dynamic_title = _metric_period_title(TRADE_ACTIVITY_METRIC_LABELS[metric_key], period)
        resolved_title = title.strip() if title and title.strip() else dynamic_title
        return _stacked_bar_chart(
            rows,
            metric_key=metric_key,
            metric_label=TRADE_ACTIVITY_METRIC_LABELS[metric_key],
            period=period,
            group_by=group_by,
            theme=theme,
            title=resolved_title,
        )
    return raw_rows


@app.get("/muni/stats/issuance_chart")
def muni_stats_issuance_chart(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    metrics: Optional[str] = Query(None, description="Single metric key"),
    period: str = Query("month"),
    group_by: str = Query("none"),
    filters: dict = Depends(_stats_filters_query),
    title: Optional[str] = Query(None, description="Optional chart title annotation"),
    theme: str = Query("dark", description="OpenBB workspace theme (dark/light)"),
    api_key: str = Depends(get_terrapin_api_key),
):
    period = _validated_period(period)
    group_by = _validated_group_by(group_by)
    api_group_by = _group_by_for_api(group_by)
    metric_key = _selected_metric_keys(metrics, ISSUANCE_METRIC_KEYS)[0]

    body = _build_muni_stats_filters(**filters)
    body.update({"start_date": start_date, "end_date": end_date, "period": period, "group_by": api_group_by})
    rows = _post_muni_stats_rows("muni_stats_issuance", body, api_key)
    dynamic_title = _metric_period_title(ISSUANCE_METRIC_LABELS[metric_key], period)
    resolved_title = title.strip() if title and title.strip() else dynamic_title
    return _stacked_bar_chart(
        rows,
        metric_key=metric_key,
        metric_label=ISSUANCE_METRIC_LABELS[metric_key],
        period=period,
        group_by=group_by,
        theme=theme,
        title=resolved_title,
    )


@app.get("/muni/stats/issuance_aggrid_chart")
def muni_stats_issuance_aggrid_chart(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    metrics: Optional[str] = Query(None, description="Single metric key"),
    period: str = Query("month"),
    group_by: str = Query("none"),
    filters: dict = Depends(_stats_filters_query),
    api_key: str = Depends(get_terrapin_api_key),
):
    period = _validated_period(period)
    group_by = _validated_group_by(group_by)
    api_group_by = _group_by_for_api(group_by)
    metric_key = _selected_metric_keys(metrics, ISSUANCE_METRIC_KEYS)[0]

    body = _build_muni_stats_filters(**filters)
    body.update({"start_date": start_date, "end_date": end_date, "period": period, "group_by": api_group_by})
    rows = _post_muni_stats_rows("muni_stats_issuance", body, api_key)
    return _stats_rows_for_aggrid_chart(
        rows,
        metric_key=metric_key,
        metric_label=ISSUANCE_METRIC_LABELS[metric_key],
        period=period,
        group_by=group_by,
    )


@app.get("/muni/stats/trade_activity_chart")
def muni_stats_trade_activity_chart(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    metrics: Optional[str] = Query(None, description="Single metric key"),
    period: str = Query("month"),
    group_by: str = Query("none"),
    filters: dict = Depends(_stats_filters_query),
    title: Optional[str] = Query(None, description="Optional chart title annotation"),
    theme: str = Query("dark", description="OpenBB workspace theme (dark/light)"),
    api_key: str = Depends(get_terrapin_api_key),
):
    period = _validated_period(period)
    group_by = _validated_group_by(group_by)
    api_group_by = _group_by_for_api(group_by)
    metric_key = _selected_metric_keys(metrics, TRADE_ACTIVITY_METRIC_KEYS)[0]

    body = _build_muni_stats_filters(**filters)
    body.update({"start_date": start_date, "end_date": end_date, "period": period, "group_by": api_group_by})
    rows = _post_muni_stats_rows("muni_stats_trade_activity", body, api_key)
    dynamic_title = _metric_period_title(TRADE_ACTIVITY_METRIC_LABELS[metric_key], period)
    resolved_title = title.strip() if title and title.strip() else dynamic_title
    return _stacked_bar_chart(
        rows,
        metric_key=metric_key,
        metric_label=TRADE_ACTIVITY_METRIC_LABELS[metric_key],
        period=period,
        group_by=group_by,
        theme=theme,
        title=resolved_title,
    )


@app.get("/muni/stats/trade_activity_aggrid_chart")
def muni_stats_trade_activity_aggrid_chart(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    metrics: Optional[str] = Query(None, description="Single metric key"),
    period: str = Query("month"),
    group_by: str = Query("none"),
    filters: dict = Depends(_stats_filters_query),
    api_key: str = Depends(get_terrapin_api_key),
):
    period = _validated_period(period)
    group_by = _validated_group_by(group_by)
    api_group_by = _group_by_for_api(group_by)
    metric_key = _selected_metric_keys(metrics, TRADE_ACTIVITY_METRIC_KEYS)[0]

    body = _build_muni_stats_filters(**filters)
    body.update({"start_date": start_date, "end_date": end_date, "period": period, "group_by": api_group_by})
    rows = _post_muni_stats_rows("muni_stats_trade_activity", body, api_key)
    return _stats_rows_for_aggrid_chart(
        rows,
        metric_key=metric_key,
        metric_label=TRADE_ACTIVITY_METRIC_LABELS[metric_key],
        period=period,
        group_by=group_by,
    )


@app.get("/muni/stats/top_issuers")
def muni_stats_top_issuers(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    rank_by: str = Query("trade_volume"),
    limit: int = Query(25),
    filters: dict = Depends(_stats_filters_query),
    api_key: str = Depends(get_terrapin_api_key),
):
    rank_by = _validated_rank_by(rank_by)
    body = _build_muni_stats_filters(**filters)
    body.update({"start_date": start_date, "end_date": end_date, "rank_by": rank_by, "limit": limit})

    rows = _post_top_issuers_rows(body, api_key)
    return [
        {
            "rank":                   i + 1,
            "issuer_name":            r.get("issuer_name") or "—",
            "trade_volume":           fmt_par(r.get("trade_volume")),
            "trade_count":            fmt(r.get("trade_count")),
            "traded_cusip_count":     fmt(r.get("traded_cusip_count")),
            "new_issuance_par_value": fmt_par(r.get("new_issuance_par_value")),
            "new_cusip_count":        fmt(r.get("new_cusip_count")),
            "last_trade_date":        r.get("last_trade_date") or "—",
        }
        for i, r in enumerate(rows)
    ]


def _post_top_issuers_rows(body: dict, api_key: str) -> list[dict]:
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{TERRAPIN_BASE_URL}/api/v1/muni_stats_top_issuers",
            headers=terrapin_headers(api_key),
            json=body
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    rows = resp.json().get("data", [])
    if not rows:
        raise HTTPException(status_code=404, detail="No top issuers found for the selected filters.")
    return rows


@app.get("/muni/stats/top_issuers_aggrid_chart")
def muni_stats_top_issuers_aggrid_chart(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    rank_by: str = Query("trade_volume"),
    limit: int = Query(25),
    filters: dict = Depends(_stats_filters_query),
    api_key: str = Depends(get_terrapin_api_key),
):
    rank_by = _validated_rank_by(rank_by)
    body = _build_muni_stats_filters(**filters)
    body.update({"start_date": start_date, "end_date": end_date, "rank_by": rank_by, "limit": limit})

    rows = _post_top_issuers_rows(body, api_key)
    return [
        {
            "issuer_name": r.get("issuer_name") or "—",
            "value": float(r.get(rank_by) or 0),
        }
        for r in rows
    ]


@app.get("/muni/stats/top_issuers_chart")
def muni_stats_top_issuers_chart(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    rank_by: str = Query("trade_volume"),
    limit: int = Query(25),
    filters: dict = Depends(_stats_filters_query),
    title: Optional[str] = Query(None, description="Optional chart title annotation"),
    theme: str = Query("dark", description="OpenBB workspace theme (dark/light)"),
    api_key: str = Depends(get_terrapin_api_key),
):
    rank_by = _validated_rank_by(rank_by)
    body = _build_muni_stats_filters(**filters)
    body.update({"start_date": start_date, "end_date": end_date, "rank_by": rank_by, "limit": limit})

    rows = _post_top_issuers_rows(body, api_key)
    x_axis = [r.get("issuer_name") or "—" for r in rows]
    y_axis = [float(r.get(rank_by) or 0) for r in rows]

    is_dark = theme.strip().lower() == "dark"
    bg_color = "#151518" if is_dark else "#FFFFFF"
    grid_color = "#2A2A2A" if is_dark else "#E5E7EB"
    text_color = "#CCCCCC" if is_dark else "#1F2937"
    title_color = "#FFFFFF" if is_dark else "#000000"

    dynamic_title = f"Top Issuers by {TOP_ISSUERS_RANK_BY_LABELS[rank_by]}"
    resolved_title = title.strip() if title and title.strip() else dynamic_title

    annotations = []
    if resolved_title:
        annotations.append(
            {
                "text": f"<b>{resolved_title}</b>",
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": 1,
                "xanchor": "left",
                "yanchor": "bottom",
                "showarrow": False,
                "font": {"color": title_color, "size": 20},
                "yshift": 8,
            }
        )

    return {
        "data": [
            {
                "type": "bar",
                "orientation": "h",
                "x": y_axis,
                "y": x_axis,
                "hovertemplate": "<b>%{y}</b><br>" + TOP_ISSUERS_RANK_BY_LABELS[rank_by] + ": %{x:,.2f}<extra></extra>",
            }
        ],
        "layout": {
            "plot_bgcolor": bg_color,
            "paper_bgcolor": bg_color,
            "font": {"color": text_color},
            "xaxis": {
                "title": {"text": ""},
                "gridcolor": grid_color,
                "linecolor": grid_color,
                "tickfont": {"color": text_color},
            },
            "yaxis": {
                "title": {"text": ""},
                "gridcolor": grid_color,
                "linecolor": grid_color,
                "tickfont": {"color": text_color},
                "automargin": True,
            },
            "hovermode": "closest",
            "annotations": annotations,
            "margin": {"l": 190},
        },
    }


# ---------------------------------------------------------------------------
# Document viewer
# ---------------------------------------------------------------------------

@app.post("/muni/document/view")
def muni_document_view(
    file_id: list = Body(default=[], embed=True),
    api_key: str = Depends(get_terrapin_api_key),
):
    """POST endpoint for the multi_file_viewer widget.
    Accepts {"file_id": ["..."]} and returns a list of base64-encoded PDFs.
    """
    import base64

    if not file_id:
        return JSONResponse(
            content=[{"error_type": "not_found", "content": "Select a document to view."}]
        )

    results = []
    for fid in file_id:
        try:
            resp = terrapin_post(
                "/api/v1/download_document",
                api_key,
                {"file_id": fid},
                timeout=60,
            )
            if resp.status_code != 200:
                results.append(
                    {
                        "error_type": "not_found",
                        "content": f"Failed to download {fid}: HTTP {resp.status_code}",
                    }
                )
                continue
            results.append(
                {
                    "content": base64.b64encode(resp.content).decode("utf-8"),
                    "data_format": {"data_type": "pdf", "filename": fid},
                }
            )
        except Exception as exc:
            results.append(
                {
                    "error_type": "download_error",
                    "content": f"Failed to download {fid}: {exc}",
                }
            )
    return JSONResponse(content=results)