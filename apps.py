"""App layout manifest for the Muni Bond OpenBB app.

Served as JSON from GET /apps.json. Date defaults are computed on each request
so Market Activity always ends on the last day of the most recently completed month.
"""

from __future__ import annotations

from typing import Any

from widgets import (
    DEFAULT_CUSIP,
    last_complete_month_end,
    one_year_ago,
    stats_default_start_date,
    today_iso,
)

COVER = "https://raw.githubusercontent.com/Terrapin-Code/openbb-app/refs/heads/main/cover.png"

MARKET_FILTER_GROUPS = [
    "Group 2",
    "Group 5",
    "Group 6",
    "Group 7",
    "Group 8",
    "Group 9",
    "Group 10",
    "Group 11",
    "Group 12",
    "Group 13",
    "Group 14",
    "Group 15",
    "Group 16",
    "Group 17",
    "Group 18",
    "Group 19",
    "Group 20",
]

MARKET_DATE_GROUPS = ["Group 3", "Group 4"]
MARKET_PERIOD_GROUP = ["Group 21"]
MARKET_GROUP_BY = ["Group 22"]


def build_apps() -> dict[str, Any]:
    """Build the apps manifest with fresh date defaults."""
    stats_start = stats_default_start_date()
    stats_end = last_complete_month_end()

    return {
        "name": "Muni Bond Lookup",
        "img": COVER,
        "img_dark": COVER,
        "img_light": COVER,
        "description": (
            "Explore US municipal bonds: reference data, pricing history, "
            "documents, cashflows, bond search, and market statistics."
        ),
        "allowCustomization": True,
        "prompts": [],
        "tabs": {
            "security_details_tab": {
                "id": "security_details_tab",
                "name": "Security Details",
                "layout": [
                    {
                        "i": "muni_bond_search",
                        "x": 0,
                        "y": 2,
                        "w": 40,
                        "h": 20,
                        "state": {
                            "params": {
                                "maturity_date_min": today_iso(),
                            },
                            "chartView": {
                                "enabled": False,
                                "chartType": "line",
                            },
                            "columnState": {
                                "default": {
                                    "columnPinning": {
                                        "leftColIds": ["cusip"],
                                        "rightColIds": [],
                                    }
                                }
                            },
                        },
                        "groups": ["Group 1"],
                    },
                    {
                        "i": "muni_reference",
                        "x": 0,
                        "y": 22,
                        "w": 16,
                        "h": 51,
                        "groups": ["Group 1"],
                    },
                    {
                        "i": "muni_cashflows",
                        "x": 16,
                        "y": 22,
                        "w": 8,
                        "h": 15,
                        "groups": ["Group 1"],
                    },
                    {
                        "i": "muni_pricing_chart",
                        "x": 24,
                        "y": 22,
                        "w": 16,
                        "h": 15,
                        "state": {
                            "params": {
                                "start_date": one_year_ago(),
                                "end_date": today_iso(),
                            }
                        },
                        "groups": ["Group 1"],
                    },
                    {
                        "i": "muni_document_viewer",
                        "x": 16,
                        "y": 37,
                        "w": 24,
                        "h": 36,
                        "groups": ["Group 1"],
                    },
                ],
            },
            "market_overview_tab": {
                "id": "market_overview_tab",
                "name": "Market Activity",
                "layout": [
                    {
                        "i": "muni_stats_filters",
                        "x": 0,
                        "y": 2,
                        "w": 40,
                        "h": 19,
                        "state": {"params": {}},
                        "groups": list(MARKET_FILTER_GROUPS),
                    },
                    {
                        "i": "muni_stats_outstanding",
                        "x": 0,
                        "y": 21,
                        "w": 20,
                        "h": 15,
                        "groups": [
                            *MARKET_FILTER_GROUPS,
                            *MARKET_GROUP_BY,
                        ],
                        "state": {
                            "params": {},
                            "chartModel": {
                                "modelType": "range",
                                "chartType": "donut",
                                "cellRange": {
                                    "columns": ["group_key", "outstanding_par_value"]
                                },
                                "suppressChartRanges": True,
                                "chartOptions": {},
                            },
                            "chartView": {
                                "enabled": True,
                                "chartType": "donut",
                            },
                        },
                    },
                    {
                        "i": "muni_stats_trade_volume_monthly",
                        "x": 20,
                        "y": 21,
                        "w": 20,
                        "h": 15,
                        "state": {
                            "params": {
                                "group_by": "use_sectors",
                                "start_date": stats_start,
                                "end_date": stats_end,
                            },
                            "chartModel": {
                                "modelType": "range",
                                "chartType": "stackedColumn",
                                "suppressChartRanges": True,
                                "chartOptions": {},
                            },
                            "chartView": {
                                "enabled": True,
                                "chartType": "stackedColumn",
                            },
                        },
                        "groups": [
                            *MARKET_FILTER_GROUPS,
                            *MARKET_DATE_GROUPS,
                            *MARKET_PERIOD_GROUP,
                            *MARKET_GROUP_BY,
                        ],
                    },
                    {
                        "i": "muni_stats_issuance",
                        "x": 0,
                        "y": 36,
                        "w": 20,
                        "h": 14,
                        "groups": [
                            *MARKET_FILTER_GROUPS,
                            *MARKET_DATE_GROUPS,
                            *MARKET_PERIOD_GROUP,
                            *MARKET_GROUP_BY,
                        ],
                        "state": {
                            "params": {
                                "group_by": "use_sectors",
                                "start_date": stats_start,
                                "end_date": stats_end,
                            },
                            "chartModel": {
                                "modelType": "range",
                                "chartType": "stackedColumn",
                                "suppressChartRanges": True,
                                "chartOptions": {},
                            },
                            "chartView": {
                                "enabled": True,
                                "chartType": "stackedColumn",
                            },
                        },
                    },
                    {
                        "i": "muni_stats_top_issuers_chart",
                        "x": 20,
                        "y": 36,
                        "w": 20,
                        "h": 14,
                        "state": {
                            "params": {
                                "start_date": stats_start,
                                "end_date": stats_end,
                            },
                            "chartModel": {
                                "modelType": "range",
                                "chartType": "groupedBar",
                                "cellRange": {
                                    "columns": ["issuer_name", "value"]
                                },
                                "suppressChartRanges": True,
                                "chartOptions": {},
                            },
                            "chartView": {
                                "enabled": True,
                                "chartType": "groupedBar",
                            },
                        },
                        "groups": [
                            *MARKET_FILTER_GROUPS,
                            *MARKET_DATE_GROUPS,
                        ],
                    },
                ],
            },
        },
        "groups": [
            {
                "name": "Group 1",
                "type": "param",
                "paramName": "cusip",
                "defaultValue": DEFAULT_CUSIP,
            },
            {
                "name": "Group 2",
                "type": "param",
                "paramName": "states",
                "defaultValue": "ALL",
            },
            {
                "name": "Group 5",
                "type": "param",
                "paramName": "sources_of_repayment",
                "defaultValue": "",
            },
            {
                "name": "Group 6",
                "type": "param",
                "paramName": "sectors",
                "defaultValue": "",
            },
            {
                "name": "Group 7",
                "type": "param",
                "paramName": "use_categories",
                "defaultValue": "",
            },
            {
                "name": "Group 8",
                "type": "param",
                "paramName": "uses_of_proceeds",
                "defaultValue": "",
            },
            {
                "name": "Group 9",
                "type": "param",
                "paramName": "rating_group",
                "defaultValue": "",
            },
            {
                "name": "Group 10",
                "type": "param",
                "paramName": "interest_types",
                "defaultValue": "",
            },
            {
                "name": "Group 11",
                "type": "param",
                "paramName": "seniority",
                "defaultValue": "",
            },
            {
                "name": "Group 12",
                "type": "param",
                "paramName": "capital_purpose",
                "defaultValue": "",
            },
            {
                "name": "Group 13",
                "type": "param",
                "paramName": "is_federally_taxable",
                "defaultValue": "",
            },
            {
                "name": "Group 14",
                "type": "param",
                "paramName": "is_amt",
                "defaultValue": "",
            },
            {
                "name": "Group 15",
                "type": "param",
                "paramName": "is_bank_qualified",
                "defaultValue": "",
            },
            {
                "name": "Group 16",
                "type": "param",
                "paramName": "is_insured",
                "defaultValue": "",
            },
            {
                "name": "Group 17",
                "type": "param",
                "paramName": "is_green",
                "defaultValue": "",
            },
            {
                "name": "Group 18",
                "type": "param",
                "paramName": "is_social",
                "defaultValue": "",
            },
            {
                "name": "Group 19",
                "type": "param",
                "paramName": "is_sustainable",
                "defaultValue": "",
            },
            {
                "name": "Group 20",
                "type": "param",
                "paramName": "is_pac",
                "defaultValue": "",
            },
            {
                "name": "Group 3",
                "type": "param",
                "paramName": "start_date",
                "defaultValue": stats_start,
            },
            {
                "name": "Group 4",
                "type": "param",
                "paramName": "end_date",
                "defaultValue": stats_end,
            },
            {
                "name": "Group 21",
                "type": "param",
                "paramName": "period",
                "defaultValue": "month",
            },
            {
                "name": "Group 22",
                "type": "param",
                "paramName": "group_by",
                "defaultValue": "use_sectors",
            },
        ],
    }
