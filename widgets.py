"""Widget manifest for the Muni Bond OpenBB app."""

from __future__ import annotations

import copy
from typing import Any

DEFAULT_CUSIP = "74445MAB5"
ALL_STATES = "ALL"

# ---------------------------------------------------------------------------
# Shared option catalogs
# ---------------------------------------------------------------------------

US_STATE_CODES = [
    "ALL",
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO",
    "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA",
    "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

ISSUER_SECTORS = [
    ("Education", "education"),
    ("Healthcare", "healthcare"),
    ("Housing", "housing"),
    ("Industrial", "industrial"),
    ("Local", "local"),
    ("State", "state"),
    ("Tobacco", "tobacco"),
    ("Transportation", "transportation"),
    ("Utilities", "utilities"),
]

USE_SECTORS = [
    ("Development", "development"),
    ("Education", "education"),
    ("Government", "government"),
    ("Healthcare", "healthcare"),
    ("Housing", "housing"),
    ("Miscellaneous", "miscellaneous"),
    ("Recreation", "recreation"),
    ("Securitized", "securitized"),
    ("Transportation", "transportation"),
    ("Utility", "utility"),
]

INTEREST_TYPES = [
    ("Fixed Rate", "fixed rate"),
    ("Variable Rate", "variable rate"),
    ("CAB", "cab"),
    ("CAB-to-Fixed", "cab-to-fixed"),
    ("Step Rate", "step rate"),
    ("Term Rate", "term rate"),
    ("Zero / Discount", "zero rate / discount rate"),
]

SOURCES_OF_REPAYMENT = [
    ("Revenue", "Revenue"),
    ("General Obligation", "General Obligation"),
    ("Double Barrel", "Double Barrel"),
]

RANK_BY_OPTIONS = [
    ("Trade Volume", "trade_volume"),
    ("Trade Count", "trade_count"),
    ("Traded CUSIPs", "traded_cusip_count"),
    ("New Issuance Par", "new_issuance_par_value"),
    ("New CUSIPs", "new_cusip_count"),
]

PERIOD_OPTIONS = [
    ("All", "all"),
    ("Day", "day"),
    ("Week", "week"),
    ("Month", "month"),
    ("Quarter", "quarter"),
    ("Year", "year"),
]

GROUP_BY_OPTIONS = [
    ("None", "none"),
    ("Basic: State", "state"),
    ("Basic: Source of Repayment", "source_of_repayment"),
    ("Basic: Rating Group", "rating_group"),
    ("Basic: Interest Type", "interest_type"),
    ("Basic: Seniority", "seniority"),
    ("Basic: Capital Purpose", "capital_purpose"),
    ("Use of Funds: Use Sectors", "use_sectors"),
    ("Use of Funds: Use Categories", "use_categories"),
    ("Use of Funds: Uses of Proceeds", "uses_of_proceeds"),
    ("Flags: Federally Taxable", "is_federally_taxable"),
    ("Flags: AMT", "is_amt"),
    ("Flags: Bank Qualified", "is_bank_qualified"),
    ("Flags: Insured", "is_insured"),
    ("Flags: Green", "is_green"),
    ("Flags: Social", "is_social"),
    ("Flags: Sustainable", "is_sustainable"),
    ("Flags: PAC", "is_pac"),
]

TRADE_METRIC_OPTIONS = [
    ("Trade Volume", "trade_volume"),
    ("Trade Count", "trade_count"),
    ("Customer Bought Count", "customer_bought_count"),
    ("Customer Sold Count", "customer_sold_count"),
    ("Inter-Dealer Count", "inter_dealer_count"),
]

ISSUANCE_METRIC_OPTIONS = [
    ("New Issuance Par Value", "new_issuance_par_value"),
    ("New CUSIP Count", "new_cusip_count"),
    ("Issuer Count", "issuer_count"),
]

OUTSTANDING_METRIC_OPTIONS = [
    ("Outstanding Par Value", "outstanding_par_value"),
    ("CUSIP Count", "cusip_count"),
    ("Entity Count", "entity_count"),
]
SHARED_STATS_PARAM_NAMES = {
    "states",
    "sources_of_repayment",
    "sectors",
    "use_categories",
    "uses_of_proceeds",
    "rating_group",
    "interest_types",
    "seniority",
    "capital_purpose",
    "is_federally_taxable",
    "is_amt",
    "is_bank_qualified",
    "is_insured",
    "is_green",
    "is_social",
    "is_sustainable",
    "is_pac",
}

RATING_GROUP_OPTIONS = [
    ("Investment Grade", "investment_grade"),
    ("High Yield", "high_yield"),
]

SENIORITY_OPTIONS = [
    ("Senior", "senior"),
    ("First Lien", "first_lien"),
    ("Second Lien", "second_lien"),
    ("Subordinate", "subordinate"),
    ("Junior", "junior"),
]

CAPITAL_PURPOSE_OPTIONS = [
    ("New Money", "new money"),
    ("Refunding", "refunding"),
    ("Mixed", "mixed"),
]

USE_CATEGORY_OPTIONS = [
    ("General Purpose", "general purpose"),
    ("Essential Services", "essential services"),
    ("Higher Education", "higher education"),
    ("Primary and Secondary Education", "primary and secondary education"),
    ("Pre-School", "pre-school"),
    ("Airport", "airport"),
    ("Port", "port"),
    ("Public Transit", "public transit"),
    ("Roads", "roads"),
    ("Bridges", "bridges"),
    ("Parking", "parking"),
    ("Economic Development", "economic development"),
    ("Industrial Development", "industrial development"),
    ("Recreational", "recreational"),
    ("Culture", "culture"),
    ("Health System", "health system"),
    ("Hospitals", "hospitals"),
    ("Senior Living", "senior living"),
    ("Single Family Housing", "single family housing"),
    ("Multi-Family Housing", "multi-family housing"),
    ("Military Housing", "military housing"),
    ("Public Housing", "public housing"),
    ("Power", "power"),
    ("Water and Sewer", "water and sewer"),
    ("Waste Removal", "waste removal"),
    ("Gas", "gas"),
    ("Electrical", "electrical"),
    ("Communication", "communication"),
    ("Gas Prepay", "gas prepay"),
    ("Student Loan", "student loan"),
    ("Miscellaneous", "miscellaneous"),
]

USES_OF_PROCEEDS_OPTIONS = [
    ("Tribal", "tribal"),
    ("Police", "police"),
    ("Fire", "fire"),
    ("Courts", "courts"),
    ("Correctional Facilities", "correctional facilities"),
    ("Public College", "public college"),
    ("Private College", "private college"),
    ("Community College", "community college"),
    ("Student Housing", "student housing"),
    ("Charter School", "charter school"),
    ("Standalone Public School", "standalone public school"),
    ("Public School District", "public school district"),
    ("Pre-School and Daycare", "pre-school and daycare"),
    ("Airport", "airport"),
    ("Combined Port Authority", "combined port authority"),
    ("Standalone Port", "standalone port"),
    ("Trains", "trains"),
    ("Buses", "buses"),
    ("Ferries", "ferries"),
    ("State Toll Roads", "state toll roads"),
    ("Regional Toll Roads", "regional toll roads"),
    ("Non-Toll Roads", "non-toll roads"),
    ("State Toll Bridges", "state toll bridges"),
    ("Regional Toll Bridges", "regional toll bridges"),
    ("Non-Toll Bridges", "non-toll bridges"),
    ("Parking Facilities", "parking facilities"),
    ("Hospitality", "hospitality"),
    ("Office Buildings", "office buildings"),
    ("Public Buildings", "public buildings"),
    ("Shopping Centres", "shopping centres"),
    ("Development District", "development district"),
    ("Industrial Development", "industrial development"),
    ("Pollution Control", "pollution control"),
    ("Stadium", "stadium"),
    ("Parks", "parks"),
    ("Library", "library"),
    ("Museum", "museum"),
    ("Community Centre", "community centre"),
    ("Health System", "health system"),
    ("Critical Access Hospital", "critical access hospital"),
    ("Standalone Hospital", "standalone hospital"),
    ("Specialty Hospital", "specialty hospital"),
    ("Assisted Living", "assisted living"),
    ("Independent Living", "independent living"),
    ("Continuing Care Retirement Community", "continuing care retirement community"),
    ("Nursing Home", "nursing home"),
    ("State HFA Single Family Housing", "state hfa single family housing"),
    ("Local HFA Single Family Housing", "local hfa single family housing"),
    ("Local Standalone Single Family Housing", "local standalone single family housing"),
    ("State HFA Multi-Family Housing", "state hfa multi-family housing"),
    ("Local HFA Multi-Family Housing", "local hfa multi-family housing"),
    ("Local Standalone Multi-Family Housing", "local standalone multi-family housing"),
    ("Military Housing", "military housing"),
    ("Public Housing", "public housing"),
    ("Nuclear Power", "nuclear power"),
    ("Coal Power", "coal power"),
    ("Gas Power", "gas power"),
    ("Wind Power", "wind power"),
    ("Solar Power", "solar power"),
    ("Alternative Source Power", "alternative source power"),
    ("Water", "water"),
    ("Sewer", "sewer"),
    ("Storm Water", "storm water"),
    ("Flood Control", "flood control"),
    ("Irrigation", "irrigation"),
    ("Waste Removal", "waste removal"),
    ("Gas Infrastructure", "gas infrastructure"),
    ("Electrical Infrastructure", "electrical infrastructure"),
    ("Telephone", "telephone"),
    ("Broadband", "broadband"),
    ("Gas Prepay", "gas prepay"),
    ("Student Loan", "student loan"),
    ("Miscellaneous", "miscellaneous"),
]


# ---------------------------------------------------------------------------
# Param builders
# ---------------------------------------------------------------------------

OptionPair = tuple[str, str] | tuple[str, str, str] | tuple[str, str, str, str]


OPTION_DESCRIPTIONS = {
    "ALL": "Use the nationwide municipal bond universe.",
    "Revenue": "Repaid from specific project revenues such as tolls or utilities.",
    "General Obligation": "Repaid from the issuer's general fund.",
    "Double Barrel": "Combines General Obligation and Revenue repayment sources.",
    "development": "Economic and industrial development projects.",
    "education": "Schools, colleges, universities, and student-related facilities.",
    "government": "Essential services and general government purpose projects.",
    "healthcare": "Healthcare systems, hospitals, and senior living facilities.",
    "housing": "Single-family, multi-family, military, and public housing.",
    "miscellaneous": "Uses that do not map cleanly to another use-of-funds sector.",
    "recreation": "Cultural and recreational public facilities.",
    "securitized": "Securitized municipal uses such as gas prepay and student loans.",
    "transportation": "Airports, roads, bridges, ports, transit, and parking.",
    "utility": "Water, sewer, power, gas, electrical, waste, and communications infrastructure.",
    "fixed rate": "Pays a fixed interest rate throughout the bond's life.",
    "variable rate": "Interest rate can change over time based on a reference rate or formula.",
    "cab": "Capital Appreciation Bond; interest accrues and is paid at maturity.",
    "cab-to-fixed": "Starts as a capital appreciation bond and converts to fixed rate.",
    "step rate": "Interest rate increases at predetermined intervals.",
    "term rate": "Pays interest at a rate set for a specific term or period.",
    "zero rate / discount rate": "Does not pay or accrue periodic interest.",
    "investment_grade": "Higher credit quality, generally BBB- and above.",
    "high_yield": "Lower credit quality, generally BB+ and below.",
    "senior": "Most senior repayment priority in the series structure.",
    "first_lien": "First-lien claim within the bond's security structure.",
    "second_lien": "Second-lien claim behind first-lien obligations.",
    "subordinate": "Subordinate claim behind senior obligations.",
    "junior": "Junior claim, generally the lowest seniority bucket.",
    "new money": "Proceeds fund new projects or capital needs.",
    "refunding": "Proceeds refinance or repay prior bonds.",
    "mixed": "Proceeds combine new-money and refunding purposes.",
    "is_federally_taxable": "Bonds whose interest is federally taxable.",
    "is_amt": "Alternative Minimum Tax bond status.",
    "is_bank_qualified": "Bank-qualified municipal bond status.",
    "is_insured": "Covered by a bond insurance company.",
    "is_green": "Designated green bond status.",
    "is_social": "Designated social bond status.",
    "is_sustainable": "Designated sustainable bond status.",
    "is_pac": "Planned Amortization Class bond status.",
    "trade_volume": "Total secondary-market par value traded.",
    "trade_count": "Number of secondary-market trades.",
    "customer_bought_count": "Customer-bought trade count.",
    "customer_sold_count": "Customer-sold trade count.",
    "inter_dealer_count": "Inter-dealer trade count.",
    "new_issuance_par_value": "Total newly issued par value in the selected period.",
    "new_cusip_count": "Number of newly issued CUSIPs.",
    "issuer_count": "Number of issuing entities.",
    "outstanding_par_value": "Total outstanding par value matching the filters.",
    "cusip_count": "Number of outstanding CUSIPs matching the filters.",
    "entity_count": "Number of unique issuing entities matching the filters.",
    "traded_cusip_count": "Number of distinct CUSIPs traded.",
}

CATEGORY_DESCRIPTIONS = {
    value: "Middle level of the Terrapin use-of-funds hierarchy."
    for _, value in USE_CATEGORY_OPTIONS
}

PROCEEDS_DESCRIPTIONS = {
    value: "Most granular use-of-proceeds classification in the Terrapin taxonomy."
    for _, value in USES_OF_PROCEEDS_OPTIONS
}

GROUP_BY_DESCRIPTIONS = {
    "none": "No grouping; return aggregate results.",
    "state": "Group by state or territory.",
    "source_of_repayment": "Group by how the bond is repaid.",
    "rating_group": "Group by investment grade versus high yield.",
    "interest_type": "Group by interest-rate structure.",
    "seniority": "Group by repayment seniority.",
    "capital_purpose": "Group by new money, refunding, or mixed purpose.",
    "use_sectors": "Group by top-level use-of-funds sector.",
    "use_categories": "Group by middle-level use-of-funds category.",
    "uses_of_proceeds": "Group by most granular use-of-proceeds value.",
    "is_federally_taxable": "Group federally taxable versus tax-exempt bonds.",
    "is_amt": "Group AMT versus non-AMT bonds.",
    "is_bank_qualified": "Group bank-qualified versus non-bank-qualified bonds.",
    "is_insured": "Group insured versus uninsured bonds.",
    "is_green": "Group green versus non-green bonds.",
    "is_social": "Group social versus non-social bonds.",
    "is_sustainable": "Group sustainable versus non-sustainable bonds.",
    "is_pac": "Group PAC versus non-PAC bonds.",
}


def _option(label: str, value: str, description: str = "", right: str = "") -> dict[str, Any]:
    option: dict[str, Any] = {"label": label, "value": value}
    if description or right:
        extra: dict[str, str] = {}
        if description:
            extra["description"] = description
        if right:
            extra["rightOfDescription"] = right
        option["extraInfo"] = extra
    return option


def _options(pairs: list[OptionPair], descriptions: dict[str, str] | None = None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for pair in pairs:
        label, value = pair[0], pair[1]
        description = pair[2] if len(pair) >= 3 else (descriptions or OPTION_DESCRIPTIONS).get(value, "")
        right = pair[3] if len(pair) >= 4 else ""
        result.append(_option(label, value, description, right))
    return result


def _state_options() -> list[dict[str, Any]]:
    return [
        _option(
            "All States" if code == ALL_STATES else code,
            code,
            OPTION_DESCRIPTIONS["ALL"] if code == ALL_STATES else "ANSI two-letter state or territory code.",
        )
        for code in US_STATE_CODES
    ]


def _param(
    param_name: str,
    *,
    type: str = "text",
    label: str,
    description: str = "",
    value: str | None = "",
    options: list[dict[str, Any]] | None = None,
    multi_select: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    p: dict[str, Any] = {
        "paramName": param_name,
        "type": type,
        "label": label,
        "description": description,
        "value": value,
    }
    if options is not None:
        p["options"] = options
    if multi_select:
        p["multiSelect"] = True
    p.update(extra)
    return p


def cusip_param(value: str = DEFAULT_CUSIP) -> dict[str, Any]:
    return _param(
        "cusip",
        label="CUSIP",
        description="9-character US CUSIP",
        value=value,
    )


def states_param(
    *,
    value: str = ALL_STATES,
    description: str = "Filter by state, or All States for nationwide",
    multi_select: bool = False,
) -> dict[str, Any]:
    return _param(
        "states",
        label="States",
        description=description,
        value=value,
        options=_state_options(),
        multi_select=multi_select,
    )


def sources_of_repayment_param(*, value: str = "") -> dict[str, Any]:
    return _param(
        "sources_of_repayment",
        label="Source of Repayment",
        description="How the bond is repaid.",
        value=value,
        options=_options(SOURCES_OF_REPAYMENT),
    )


def issuer_sectors_param(*, value: str = "") -> dict[str, Any]:
    return _param(
        "sectors",
        label="Sectors",
        description="Bond issuer sectors",
        value=value,
        options=_options(ISSUER_SECTORS),
        multi_select=True,
    )


def use_sectors_param(*, value: str = "") -> dict[str, Any]:
    return _param(
        "sectors",
        label="Use Sectors",
        description="Top-level use-of-funds sector.",
        value=value,
        options=_options(USE_SECTORS),
        multi_select=True,
    )


def interest_types_param(*, value: str = "") -> dict[str, Any]:
    return _param(
        "interest_types",
        label="Interest Types",
        description="Interest-rate structure.",
        value=value,
        options=_options(INTEREST_TYPES),
    )


def date_range_params(
    *,
    start: str = "$currentDate-3m",
    end: str = "$currentDate",
    start_label: str = "Start Date",
    end_label: str = "End Date",
    start_description: str = "Period start",
    end_description: str = "Period end",
) -> list[dict[str, Any]]:
    return [
        _param("start_date", type="date", label=start_label, description=start_description, value=start),
        _param("end_date", type="date", label=end_label, description=end_description, value=end),
    ]


def stats_non_boolean_filter_params(*, states: str = ALL_STATES) -> list[dict[str, Any]]:
    return [
        states_param(value=states),
        sources_of_repayment_param(),
        use_sectors_param(),
        interest_types_param(),
        _param(
            "use_categories",
            label="Use Categories",
            description="Middle level of the use-of-funds hierarchy.",
            options=_options(USE_CATEGORY_OPTIONS, CATEGORY_DESCRIPTIONS),
            multi_select=True,
        ),
        _param(
            "uses_of_proceeds",
            label="Uses of Proceeds",
            description="Most granular use-of-proceeds classification.",
            options=_options(USES_OF_PROCEEDS_OPTIONS, PROCEEDS_DESCRIPTIONS),
            multi_select=True,
        ),
        _param(
            "rating_group",
            label="Rating Group",
            description="Investment grade or high yield.",
            options=_options(RATING_GROUP_OPTIONS),
        ),
        _param(
            "seniority",
            label="Seniority",
            description="Bond seniority derived from the series name.",
            options=_options(SENIORITY_OPTIONS),
        ),
        _param(
            "capital_purpose",
            label="Capital Purpose",
            description="Whether proceeds fund new projects, refund prior bonds, or both.",
            options=_options(CAPITAL_PURPOSE_OPTIONS),
        ),
    ]


def stats_compact_filter_params(*, states: str = ALL_STATES) -> list[dict[str, Any]]:
    """Keep only the most intuitive, high-signal stats filters."""
    return [
        states_param(value=states),
        sources_of_repayment_param(),
        use_sectors_param(),
    ]


def _boolean_filter_options(default_label: str, param_name: str) -> list[dict[str, Any]]:
    return [
        _option(f"All {default_label}", "", f"Do not filter on {default_label.lower()} status."),
        _option(f"Yes: {default_label}", "true", OPTION_DESCRIPTIONS.get(param_name, "")),
        _option(f"No: {default_label}", "false", f"Exclude bonds where {default_label.lower()} is true."),
    ]


def stats_yes_no_filter_params() -> list[dict[str, Any]]:
    return [
        _param(
            "is_federally_taxable",
            label="Federally Taxable",
            description=OPTION_DESCRIPTIONS["is_federally_taxable"],
            value="",
            options=_boolean_filter_options("Federally Taxable", "is_federally_taxable"),
        ),
        _param(
            "is_amt",
            label="AMT",
            description=OPTION_DESCRIPTIONS["is_amt"],
            value="",
            options=_boolean_filter_options("AMT", "is_amt"),
        ),
        _param(
            "is_bank_qualified",
            label="Bank Qualified",
            description=OPTION_DESCRIPTIONS["is_bank_qualified"],
            value="",
            options=_boolean_filter_options("Bank Qualified", "is_bank_qualified"),
        ),
        _param(
            "is_insured",
            label="Insured",
            description=OPTION_DESCRIPTIONS["is_insured"],
            value="",
            options=_boolean_filter_options("Insured", "is_insured"),
        ),
        _param(
            "is_green",
            label="Green",
            description=OPTION_DESCRIPTIONS["is_green"],
            value="",
            options=_boolean_filter_options("Green", "is_green"),
        ),
        _param(
            "is_social",
            label="Social",
            description=OPTION_DESCRIPTIONS["is_social"],
            value="",
            options=_boolean_filter_options("Social", "is_social"),
        ),
        _param(
            "is_sustainable",
            label="Sustainable",
            description=OPTION_DESCRIPTIONS["is_sustainable"],
            value="",
            options=_boolean_filter_options("Sustainable", "is_sustainable"),
        ),
        _param(
            "is_pac",
            label="PAC",
            description=OPTION_DESCRIPTIONS["is_pac"],
            value="",
            options=_boolean_filter_options("PAC", "is_pac"),
        ),
    ]


def stats_filter_params(*, states: str = ALL_STATES) -> list[dict[str, Any]]:
    return [
        *stats_non_boolean_filter_params(states=states),
        *stats_yes_no_filter_params(),
    ]


def stats_filter_param_rows(*, states: str = ALL_STATES) -> list[list[dict[str, Any]]]:
    filters = {param["paramName"]: param for param in stats_filter_params(states=states)}
    return [
        [
            filters["states"],
            filters["sources_of_repayment"],
            filters["rating_group"],
        ],
        [
            filters["sectors"],
            filters["use_categories"],
            filters["uses_of_proceeds"],
        ],
        [
            filters["interest_types"],
            filters["seniority"],
            filters["capital_purpose"],
        ],
        [
            filters["is_federally_taxable"],
            filters["is_amt"],
            filters["is_bank_qualified"],
            filters["is_insured"],
        ],
        [
            filters["is_green"],
            filters["is_social"],
            filters["is_sustainable"],
            filters["is_pac"],
        ],
    ]


def hidden_shared_stats_param_rows(*, states: str = ALL_STATES) -> list[list[dict[str, Any]]]:
    rows = hide_shared_stats_params(stats_filter_param_rows(states=states))
    return [[param for row in rows for param in row]]


def hidden_stats_filter_param_row(*, states: str = ALL_STATES) -> list[list[dict[str, Any]]]:
    params = copy.deepcopy(stats_filter_params(states=states))
    for param in params:
        param["show"] = False
    return [params]


def stats_metrics_param(*, options: list[tuple[str, str]], value: str) -> dict[str, Any]:
    return _param(
        "metrics",
        label="Metrics",
        description="Choose one metric to display",
        value=value,
        options=_options(options),
    )


def stats_period_param(*, value: str = "all") -> dict[str, Any]:
    return _param(
        "period",
        label="Period",
        description="Aggregation period for time series stats",
        value=value,
        options=_options(PERIOD_OPTIONS),
    )


def stats_group_by_param(*, value: str = "none") -> dict[str, Any]:
    return _param(
        "group_by",
        label="Group By",
        description="Optional dimension for grouped stats",
        value=value,
        options=_options(GROUP_BY_OPTIONS, GROUP_BY_DESCRIPTIONS),
    )


def hide_shared_stats_params(params: list[Any]) -> list[Any]:
    hidden = copy.deepcopy(params)

    def walk(node: Any):
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if isinstance(node, dict) and node.get("paramName") in SHARED_STATS_PARAM_NAMES:
            node["show"] = False

    walk(hidden)
    return hidden


def stats_core_params(
    *,
    metric_options: list[tuple[str, str]],
    metric_value: str,
    include_period: bool = False,
) -> list[dict[str, Any]]:
    params: list[dict[str, Any]] = [
        stats_metrics_param(options=metric_options, value=metric_value),
        stats_group_by_param(),
    ]
    if include_period:
        params.append(stats_period_param(value="month"))
    return params


def document_selector_param() -> dict[str, Any]:
    return _param(
        "file_id",
        type="endpoint",
        label="Documents",
        show=False,
        multiSelect=True,
        roles=["fileSelector"],
        optionsEndpoint="/muni/documents/options",
        optionsParams={"cusip": "$cusip"},
    )


def table_col(field: str, header: str, **extra: Any) -> dict[str, Any]:
    return {"field": field, "headerName": header, **extra}


def stats_kv_table() -> dict[str, Any]:
    return {
        "table": {
            "columnsDefs": [
                table_col("metric", "Metric", cellDataType="text", flex=2),
                table_col("value", "Value", cellDataType="text", flex=2),
            ],
        },
    }


def aggrid_stacked_stats_chart_data() -> dict[str, Any]:
    return {
        "table": {
            "chartView": {
                "enabled": True,
                "chartType": "stackedColumn",
            },
        },
    }


def aggrid_top_issuers_chart_data() -> dict[str, Any]:
    return {
        "table": {
            "chartView": {
                "enabled": True,
                "chartType": "groupedBar",
            },
            "columnsDefs": [
                table_col("issuer_name", "Issuer", cellDataType="text", chartDataType="category", flex=3),
                table_col("value", "Value", cellDataType="number", chartDataType="series", flex=2),
            ],
        },
    }


def cusip_click_col() -> dict[str, Any]:
    return table_col(
        "cusip",
        "CUSIP",
        cellDataType="text",
        pinned="left",
        width=110,
        renderFn="cellOnClick",
        renderFnParams={
            "actionType": "groupBy",
            "groupBy": {"paramName": "cusip", "valueField": "cusip"},
        },
    )


# ---------------------------------------------------------------------------
# Widget definitions
# ---------------------------------------------------------------------------

WIDGETS: dict[str, dict[str, Any]] = {
    "muni_reference": {
        "name": "Muni Bond Reference Data",
        "description": "Full reference data for a US municipal bond, organised by section.",
        "type": "markdown",
        "endpoint": "/muni/reference",
        "gridData": {"w": 10, "h": 28},
        "params": [cusip_param()],
    },

    "muni_pricing_chart": {
        "name": "Muni Bond Pricing History",
        "description": "Trade prices over time for a US municipal bond, coloured by trade type.",
        "type": "chart",
        "endpoint": "/muni/pricing_chart",
        "gridData": {"w": 20, "h": 16},
        "runButton": True,
        "params": [
            cusip_param(),
            *date_range_params(
                start="$currentDate-1y",
                start_description="Defaults to 1 year ago",
                end_description="Defaults to today",
            ),
        ],
    },

    "muni_document_viewer": {
        "name": "Bond Documents",
        "description": "Official statements and disclosure documents viewer. Select a document from the dropdown to open it.",
        "type": "multi_file_viewer",
        "endpoint": "/muni/document/view",
        "gridData": {"w": 30, "h": 24},
        "params": [cusip_param(), document_selector_param()],
    },

    "muni_cashflows": {
        "name": "Muni Bond Cashflows",
        "description": "Cashflow schedules to maturity and to next call for a US municipal bond.",
        "type": "markdown",
        "endpoint": "/muni/cashflows",
        "gridData": {"w": 20, "h": 14},
        "params": [cusip_param()],
    },

    "muni_bond_search": {
        "name": "Bond Explorer",
        "description": "Search and filter US municipal bonds. Click a CUSIP to load the bond in Security Details.",
        "type": "table",
        "endpoint": "/muni/search",
        "gridData": {"w": 40, "h": 22},
        "params": [
            [
                _param("issuer_name", label="Issuer Name", description="Filter by issuer name (partial match)"),
                states_param(),
                issuer_sectors_param(),
                interest_types_param(),
                sources_of_repayment_param(),
            ],
            [
                _param("coupon_min", label="Coupon Min (%)", description="Minimum coupon rate"),
                _param("coupon_max", label="Coupon Max (%)", description="Maximum coupon rate"),
                _param("maturity_date_min", type="date", label="Maturity From", description="Minimum maturity date", value=""),
                _param("maturity_date_max", type="date", label="Maturity To", description="Maximum maturity date", value=""),
                _param("last_traded_since", type="date", label="Last Traded Since", description="Only include bonds traded since this date", value=""),
                _param("limit", label="Result Limit", description="Maximum number of results (default 100)", value="100"),
            ],
        ],
        "data": {
            "table": {
                "columnsDefs": [
                    cusip_click_col(),
                    table_col("ticker", "Ticker", cellDataType="text", flex=2),
                    table_col("issuer_name", "Issuer", cellDataType="text", flex=3),
                    table_col("state", "State", cellDataType="text", width=70),
                    table_col("coupon", "Coupon", cellDataType="text", width=90),
                    table_col("interest_type", "Type", cellDataType="text", width=110),
                    table_col("maturity_date", "Maturity", cellDataType="dateString", width=110),
                    table_col("callable", "Callable", cellDataType="text", width=80),
                    table_col("rating", "Rating", cellDataType="text", width=130),
                    table_col("has_os", "Official Stmt", cellDataType="text", width=100),
                ],
            },
        },
    },

    "muni_stats_filters": {
        "name": "Market Activity Filters",
        "description": "Shared filters for the Market Activity widgets.",
        "type": "html",
        "endpoint": "/muni/stats/filters_summary",
        "gridData": {"w": 40, "h": 19},
        "runButton": False,
        "params": hidden_stats_filter_param_row(),
    },

    "muni_stats_outstanding": {
        "name": "Outstanding Universe",
        "description": "Cross-sectional outstanding par value, CUSIP count, and issuer count for the filtered universe.",
        "type": "table",
        "endpoint": "/muni/stats/outstanding",
        "gridData": {"w": 13, "h": 12},
        "runButton": False,
        "params": [
            *hidden_shared_stats_param_rows(),
            [
                stats_group_by_param(value="use_sectors"),
                stats_metrics_param(
                    options=OUTSTANDING_METRIC_OPTIONS,
                    value="outstanding_par_value",
                ),
            ],
        ],
        "data": {
            "table": {
                "columnsDefs": [
                    table_col("group_key", "Group", cellDataType="text", width=180),
                    table_col("outstanding_par_value", "Outstanding Par Value", cellDataType="number", width=180),
                    table_col("cusip_count", "CUSIP Count", cellDataType="number", width=120),
                    table_col("entity_count", "Entity Count", cellDataType="number", width=120),
                ],
            },
        },
    },

    "muni_stats_issuance": {
        "name": "Issuance",
        "description": "Time series issuance stats over the selected date range and filters.",
        "type": "table",
        "endpoint": "/muni/stats/issuance_aggrid_chart",
        "gridData": {"w": 13, "h": 12},
        "runButton": False,
        "params": [
            *hidden_shared_stats_param_rows(),
            [
                stats_group_by_param(),
                stats_metrics_param(
                    options=ISSUANCE_METRIC_OPTIONS,
                    value="new_issuance_par_value",
                ),
                stats_period_param(value="month"),
                *date_range_params(start="2025-01-01"),
            ],
        ],
        "data": aggrid_stacked_stats_chart_data(),
    },

    "muni_stats_trade_activity": {
        "name": "Trade Activity",
        "description": "Time series secondary-market trade stats for the selected date range and filters.",
        "type": "chart",
        "endpoint": "/muni/stats/trade_activity_chart",
        "gridData": {"w": 14, "h": 12},
        "runButton": False,
        "params": [
            *hidden_shared_stats_param_rows(),
            [
                stats_group_by_param(),
                stats_metrics_param(
                    options=TRADE_METRIC_OPTIONS,
                    value="trade_volume",
                ),
                stats_period_param(value="month"),
                *date_range_params(start="2025-01-01"),
            ],
        ],
    },

    "muni_stats_outstanding_seniority": {
        "name": "Outstanding Universe: Seniority",
        "description": "Outstanding universe breakdown grouped by seniority.",
        "type": "table",
        "endpoint": "/muni/stats/outstanding",
        "gridData": {"w": 20, "h": 16},
        "runButton": False,
        "params": [
            *hidden_shared_stats_param_rows(),
            [
                stats_group_by_param(value="seniority"),
                stats_metrics_param(
                    options=OUTSTANDING_METRIC_OPTIONS,
                    value="outstanding_par_value",
                ),
            ],
        ],
        "data": {
            "table": {
                "columnsDefs": [
                    table_col("group_key", "Group", cellDataType="text", width=180),
                    table_col("outstanding_par_value", "Outstanding Par Value", cellDataType="number", width=180),
                    table_col("cusip_count", "CUSIP Count", cellDataType="number", width=120),
                    table_col("entity_count", "Entity Count", cellDataType="number", width=120),
                ],
            },
        },
    },

    "muni_stats_trade_volume_monthly": {
        "name": "Trade Activity: Volume Trend",
        "description": "Trade volume trend for the selected period.",
        "type": "table",
        "endpoint": "/muni/stats/trade_activity_aggrid_chart",
        "gridData": {"w": 20, "h": 16},
        "runButton": False,
        "params": [
            *hidden_shared_stats_param_rows(),
            [
                stats_group_by_param(value="none"),
                stats_metrics_param(
                    options=TRADE_METRIC_OPTIONS,
                    value="trade_volume",
                ),
                stats_period_param(value="month"),
                *date_range_params(start="2025-01-01"),
            ],
        ],
        "data": aggrid_stacked_stats_chart_data(),
    },

    "muni_stats_trade_customer_bought_monthly": {
        "name": "Trade Activity: Customer Bought by Month",
        "description": "Monthly customer-bought trade count trend.",
        "type": "chart",
        "endpoint": "/muni/stats/trade_activity_chart",
        "gridData": {"w": 20, "h": 16},
        "runButton": False,
        "params": [
            *hidden_shared_stats_param_rows(),
            [
                stats_group_by_param(value="none"),
                stats_metrics_param(
                    options=TRADE_METRIC_OPTIONS,
                    value="customer_bought_count",
                ),
                stats_period_param(value="month"),
                *date_range_params(start="2025-01-01"),
            ],
        ],
    },

    "muni_stats_issuance_interest_type": {
        "name": "Issuance: Interest Type",
        "description": "Monthly issuance split by interest type.",
        "type": "chart",
        "endpoint": "/muni/stats/issuance_chart",
        "gridData": {"w": 20, "h": 16},
        "runButton": False,
        "params": [
            *hidden_shared_stats_param_rows(),
            [
                stats_group_by_param(value="interest_type"),
                stats_metrics_param(
                    options=ISSUANCE_METRIC_OPTIONS,
                    value="new_issuance_par_value",
                ),
                stats_period_param(value="month"),
                *date_range_params(start="2025-01-01"),
            ],
        ],
    },

    "muni_stats_issuance_sector": {
        "name": "Issuance: Sector",
        "description": "Monthly issuance split by sector.",
        "type": "chart",
        "endpoint": "/muni/stats/issuance_chart",
        "gridData": {"w": 20, "h": 16},
        "runButton": False,
        "params": [
            *hidden_shared_stats_param_rows(),
            [
                stats_group_by_param(value="use_sectors"),
                stats_metrics_param(
                    options=ISSUANCE_METRIC_OPTIONS,
                    value="new_issuance_par_value",
                ),
                stats_period_param(value="month"),
                *date_range_params(start="2025-01-01"),
            ],
        ],
    },

    "muni_stats_top_issuers": {
        "name": "Top Issuers",
        "description": "Issuers ranked by trade volume, trade count, new issuance, or traded CUSIP count.",
        "type": "table",
        "endpoint": "/muni/stats/top_issuers",
        "gridData": {"w": 40, "h": 18},
        "runButton": False,
        "params": [
            *hidden_shared_stats_param_rows(),
            [
                _param(
                    "rank_by",
                    label="Rank By",
                    description="Metric used to rank issuers",
                    value="trade_volume",
                    options=_options(RANK_BY_OPTIONS),
                ),
                _param("limit", label="Limit", description="Maximum number of issuers", value="25"),
                *date_range_params(start="2025-01-01"),
            ],
        ],
        "data": {
            "table": {
                "columnsDefs": [
                    table_col("rank", "#", cellDataType="text", width=50, pinned="left"),
                    table_col("issuer_name", "Issuer", cellDataType="text", flex=3),
                    table_col("trade_volume", "Trade Volume", cellDataType="text", width=130),
                    table_col("trade_count", "Trades", cellDataType="text", width=90),
                    table_col("traded_cusip_count", "Traded CUSIPs", cellDataType="text", width=120),
                    table_col("new_issuance_par_value", "New Issuance", cellDataType="text", width=130),
                    table_col("new_cusip_count", "New CUSIPs", cellDataType="text", width=100),
                    table_col("last_trade_date", "Last Trade", cellDataType="dateString", width=110),
                ],
            },
        },
    },

    "muni_stats_top_issuers_chart": {
        "name": "Top Issuers Chart",
        "description": "Bar chart of top issuers by selected metric.",
        "type": "table",
        "endpoint": "/muni/stats/top_issuers_aggrid_chart",
        "gridData": {"w": 20, "h": 18},
        "runButton": False,
        "params": [
            *hidden_shared_stats_param_rows(),
            [
                _param(
                    "rank_by",
                    label="Rank By",
                    description="Metric used to rank issuers",
                    value="trade_volume",
                    options=_options(RANK_BY_OPTIONS),
                ),
                _param("limit", label="Limit", description="Maximum number of issuers", value="25"),
                *date_range_params(start="2025-01-01"),
            ],
        ],
        "data": aggrid_top_issuers_chart_data(),
    },
}
