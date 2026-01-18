from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException

from app.db.session import get_engine
from app.mcp.gemini_client import MCPError, parse_intent
from app.query_planner.planner import QueryPlannerError, as_sqlalchemy_text, plan_intent
from app.schemas import ErrorResponse, QueryRequest, QueryResponse

router = APIRouter()


def _year_phrase(filters: dict[str, Any]) -> str:
    year = filters.get("year")
    years = filters.get("years")
    year_from = filters.get("year_from")
    year_to = filters.get("year_to")
    year_count = filters.get("year_count")

    if isinstance(year, int):
        return f"in {year}"
    if isinstance(years, list):
        cleaned = [y for y in years if isinstance(y, int)]
        if len(cleaned) == 2:
            return f"({cleaned[0]} vs {cleaned[1]})"
        if cleaned:
            return f"({', '.join(str(y) for y in cleaned)})"
    if isinstance(year_from, int) and isinstance(year_to, int):
        return f"from {year_from} to {year_to}"
    if isinstance(year_from, int):
        return f"from {year_from}"
    if isinstance(year_to, int):
        return f"up to {year_to}"
    if isinstance(year_count, int) and year_count > 0:
        return f"(last {year_count} years)"
    return ""


# Build a human-readable scope phrase from category/product filters.
def _scope_phrase(filters: dict[str, Any]) -> str:
    parts: list[str] = []
    category = filters.get("category")
    categories = filters.get("categories")
    product_name = filters.get("product_name")
    product_id = filters.get("product_id")

    if isinstance(category, str) and category.strip():
        parts.append(f"category {category.strip()}")
    elif isinstance(categories, list):
        cleaned = [str(c).strip() for c in categories if str(c).strip()]
        if cleaned:
            parts.append("categories " + ", ".join(cleaned[:5]))

    if isinstance(product_name, str) and product_name.strip():
        parts.append(f"product {product_name.strip()}")
    elif isinstance(product_id, int):
        parts.append(f"product #{product_id}")

    if not parts:
        return ""
    return "(" + ", ".join(parts) + ")"


# Generate a chart title based on the intent name and its filters.
def _derive_title(intent_payload: dict[str, Any]) -> str:
    intent = str(intent_payload.get("intent") or "")
    filters = intent_payload.get("filters")
    if not isinstance(filters, dict):
        filters = {}

    year_part = _year_phrase(filters)
    scope_part = _scope_phrase(filters)
    limit = filters.get("limit")
    order = filters.get("order")
    entity = filters.get("entity")
    average = bool(filters.get("average"))

    def _join(base: str) -> str:
        parts = [base]
        if year_part:
            parts.append(year_part)
        if scope_part:
            parts.append(scope_part)
        return " ".join(parts).strip()

    if intent in ("sales_trend", "sales_trend_over_time"):
        return _join("Revenue trend")
    if intent in ("sales_comparison", "sales_comparison_by_year"):
        return _join("Revenue comparison")
    if intent == "total_sales_for_period":
        return _join("Total revenue")
    if intent in ("top_products",):
        n = limit if isinstance(limit, int) else 10
        return _join(f"Top {n} products by revenue")
    if intent in ("sales_by_product",):
        return _join("Revenue by product")
    if intent in ("revenue_by_category", "sales_by_category"):
        return _join("Revenue by category")
    if intent == "product_sales_trend":
        return _join("Product revenue trend")
    if intent == "sales_breakdown_for_year":
        dims = intent_payload.get("dimensions")
        dim0 = dims[0] if isinstance(dims, list) and dims else "product"
        return _join(f"Sales breakdown by {dim0}")
    if intent == "sales_growth_analysis":
        return _join("Year-over-year revenue change")
    if intent == "multi_year_comparison":
        if average:
            return _join("Average yearly revenue")
        return _join("Revenue by year")
    if intent == "top_bottom_performers":
        n = limit if isinstance(limit, int) else 5
        ent = entity if entity in ("product", "category") else "product"
        ord_word = "Top" if order != "bottom" else "Bottom"
        label = "products" if ent == "product" else "categories"
        return _join(f"{ord_word} {n} {label} by revenue")
    if intent == "clarification_required":
        return "Sales overview (needs clarification)"

    return _join("Revenue")


# Normalize DB values (including Decimal) to float for chart data.
def _to_float(v: Any) -> float:
    if v is None:
        return 0.0
    if isinstance(v, float):
        return v
    if isinstance(v, int):
        return float(v)
    if isinstance(v, Decimal):
        return float(v)
    try:
        return float(v)
    except Exception:
        return 0.0


@router.post("/query", response_model=QueryResponse, responses={400: {"model": ErrorResponse}})
# Parse the user question into an intent, plan deterministic SQL, execute it, and return chart-ready data.
def query(req: QueryRequest):
    try:
        intent = parse_intent(req.question)
    except MCPError as e:
        raise HTTPException(status_code=400, detail={"error": "mcp_error", "detail": str(e)})

    try:
        plan = plan_intent(intent)
    except QueryPlannerError as e:
        raise HTTPException(status_code=400, detail={"error": "planner_error", "detail": str(e)})

    engine = get_engine()
    stmt = as_sqlalchemy_text(plan)

    labels: list[str] = []
    values: list[float] = []

    try:
        with engine.connect() as conn:
            rows = conn.execute(stmt, plan.params).mappings().all()
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "db_error", "detail": str(e)})

    for r in rows:
        labels.append(str(r.get(plan.label_field)))
        values.append(_to_float(r.get(plan.value_field)))

    title = _derive_title(intent)

    if not labels:
        # Return empty chart-ready response to prevent crash on frontend
        return QueryResponse(title=title, chartType=plan.chart_type, labels=[], datasets=[])

    return QueryResponse(
        title=title,
        chartType=plan.chart_type,
        labels=labels,
        datasets=[{"label": "total_revenue", "data": values}],
    )
