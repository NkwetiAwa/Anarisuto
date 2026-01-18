from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


IntentName = Literal[
    "sales_trend",
    "sales_comparison",
    "revenue_by_category",
    "top_products",
    "sales_comparison_by_year",
    "sales_trend_over_time",
    "total_sales_for_period",
    "sales_by_product",
    "product_sales_trend",
    "sales_by_category",
    "top_bottom_performers",
    "sales_breakdown_for_year",
    "sales_growth_analysis",
    "clarification_required",
    "multi_year_comparison",
]

MetricName = Literal[
    "total_revenue",
]

DimensionName = Literal[
    "year",
    "category",
    "product",
]


@dataclass(frozen=True)
class IntentSpec:
    name: IntentName
    allowed_metrics: set[MetricName]
    allowed_dimensions: set[DimensionName]
    default_chart: Literal["line", "bar"]


INTENTS: dict[IntentName, IntentSpec] = {
    # Show general sales trends for specified years
    "sales_trend": IntentSpec(
        name="sales_trend",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"year"},
        default_chart="line",
    ),
    # Compare two years
    "sales_comparison": IntentSpec(
        name="sales_comparison",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"year"},
        default_chart="bar",
    ),
    # Show sales for different categories
    "revenue_by_category": IntentSpec(
        name="revenue_by_category",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"category"},
        default_chart="bar",
    ),
    # Get top products by revenue
    "top_products": IntentSpec(
        name="top_products",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"product"},
        default_chart="bar",
    ),

    # Compare 2 years (vs/compare/gap/increase)
    "sales_comparison_by_year": IntentSpec(
        name="sales_comparison_by_year",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"year"},
        default_chart="bar",
    ),

    # Trend over time (year-by-year)
    "sales_trend_over_time": IntentSpec(
        name="sales_trend_over_time",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"year"},
        default_chart="line",
    ),

    # Total for a given period (single value)
    "total_sales_for_period": IntentSpec(
        name="total_sales_for_period",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"year"},
        default_chart="bar",
    ),

    # Revenue by product (rank/compare across products)
    "sales_by_product": IntentSpec(
        name="sales_by_product",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"product"},
        default_chart="bar",
    ),

    # One product over time
    "product_sales_trend": IntentSpec(
        name="product_sales_trend",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"year"},
        default_chart="line",
    ),

    # Revenue by category (optionally over a period)
    "sales_by_category": IntentSpec(
        name="sales_by_category",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"category"},
        default_chart="bar",
    ),

    # Top/bottom performers (products or categories)
    "top_bottom_performers": IntentSpec(
        name="top_bottom_performers",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"product", "category"},
        default_chart="bar",
    ),

    # Breakdown for a specific year by product/category
    "sales_breakdown_for_year": IntentSpec(
        name="sales_breakdown_for_year",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"product", "category"},
        default_chart="bar",
    ),

    # Year-over-year growth (diff)
    "sales_growth_analysis": IntentSpec(
        name="sales_growth_analysis",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"year"},
        default_chart="line",
    ),

    # Generic/ambiguous: we should ask a follow-up
    "clarification_required": IntentSpec(
        name="clarification_required",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"year"},
        default_chart="line",
    ),

    # Aggregated comparisons like last N years / average yearly
    "multi_year_comparison": IntentSpec(
        name="multi_year_comparison",
        allowed_metrics={"total_revenue"},
        allowed_dimensions={"year"},
        default_chart="bar",
    ),
}
