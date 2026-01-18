from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import text

from app.query_planner.catalog import INTENTS, DimensionName, IntentName, MetricName


@dataclass(frozen=True)
class PlannedQuery:
    sql: str
    params: dict[str, Any]
    chart_type: Literal["line", "bar"]
    label_field: str
    value_field: str
    series_field: str | None = None


class QueryPlannerError(ValueError):
    pass


def _validate_list(values: list[str], allowed: set[str], what: str) -> None:
    for v in values:
        if v not in allowed:
            raise QueryPlannerError(f"Unsupported {what}: {v}")

# Based on payload and payload data, plan an SQL query
def plan_intent(intent_payload: dict[str, Any]) -> PlannedQuery:
    intent = intent_payload.get("intent")
    if intent not in INTENTS:
        raise QueryPlannerError(f"Unsupported intent: {intent}")

    spec = INTENTS[intent]

    metrics = intent_payload.get("metrics") or []
    dimensions = intent_payload.get("dimensions") or []
    filters = intent_payload.get("filters") or {}

    if not isinstance(metrics, list) or not isinstance(dimensions, list) or not isinstance(filters, dict):
        raise QueryPlannerError("Invalid intent JSON: metrics/dimensions/filters types")

    _validate_list(metrics, set(spec.allowed_metrics), "metric")
    _validate_list(dimensions, set(spec.allowed_dimensions), "dimension")

    chart = intent_payload.get("chart") or spec.default_chart
    if chart not in ("line", "bar"):
        chart = spec.default_chart

    intent_name: IntentName = intent
    # metric0: MetricName = metrics[0] if metrics else "total_revenue"
    dim0: DimensionName = dimensions[0] if dimensions else list(spec.allowed_dimensions)[0]

    if intent_name in ("sales_trend", "sales_comparison", "sales_trend_over_time"):
        years = filters.get("years")
        year_from = filters.get("year_from")
        year_to = filters.get("year_to")
        category = filters.get("category")
        categories = filters.get("categories")
        product_id = filters.get("product_id")
        product_name = filters.get("product_name")

        where = []
        params: dict[str, Any] = {}

        join_products = bool(category or categories or product_name)

        if isinstance(years, list) and years:
            where.append("s.year = ANY(:years)")
            params["years"] = years
        else:
            if isinstance(year_from, int):
                where.append("s.year >= :year_from")
                params["year_from"] = year_from
            if isinstance(year_to, int):
                where.append("s.year <= :year_to")
                params["year_to"] = year_to

        if isinstance(product_id, int):
            where.append("s.product_id = :product_id")
            params["product_id"] = product_id

        if isinstance(category, str) and category.strip():
            join_products = True
            where.append("lower(p.category) = lower(:category)")
            params["category"] = category.strip()
        elif isinstance(categories, list) and categories:
            # Compare lower-cased values to be case-insensitive.
            cleaned = [str(c).strip().lower() for c in categories if str(c).strip()]
            if cleaned:
                join_products = True
                where.append("lower(p.category) = ANY(:categories)")
                params["categories"] = cleaned

        if isinstance(product_name, str) and product_name.strip():
            join_products = True
            name = product_name.strip()

            if "%" not in name:
                name = f"%{name}%"
            where.append("p.name ILIKE :product_name")
            params["product_name"] = name

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        join_sql = "JOIN products p ON p.id = s.product_id" if join_products else ""

        sql = f"""
            SELECT s.year::TEXT AS label,
                   SUM(s.revenue)::NUMERIC AS value
            FROM sales s
            {join_sql}
            {where_sql}
            GROUP BY s.year
            ORDER BY s.year ASC
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "sales_comparison_by_year":
        years = filters.get("years")
        year_from = filters.get("year_from")
        year_to = filters.get("year_to")
        category = filters.get("category")
        product_id = filters.get("product_id")
        product_name = filters.get("product_name")

        where = []
        params: dict[str, Any] = {}
        join_products = bool(category or product_name)

        if isinstance(years, list) and years:
            where.append("s.year = ANY(:years)")
            params["years"] = years
        else:
            yr_list = []
            if isinstance(year_from, int):
                yr_list.append(year_from)
            if isinstance(year_to, int):
                yr_list.append(year_to)
            yr_list = sorted(set(yr_list))
            if yr_list:
                where.append("s.year = ANY(:years)")
                params["years"] = yr_list

        if isinstance(product_id, int):
            where.append("s.product_id = :product_id")
            params["product_id"] = product_id

        if isinstance(category, str) and category.strip():
            join_products = True
            where.append("lower(p.category) = lower(:category)")
            params["category"] = category.strip()

        if isinstance(product_name, str) and product_name.strip():
            join_products = True
            name = product_name.strip()
            if "%" not in name:
                name = f"%{name}%"
            where.append("p.name ILIKE :product_name")
            params["product_name"] = name

        join_sql = "JOIN products p ON p.id = s.product_id" if join_products else ""
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        sql = f"""
            SELECT s.year::TEXT AS label,
                   SUM(s.revenue)::NUMERIC AS value
            FROM sales s
            {join_sql}
            {where_sql}
            GROUP BY s.year
            ORDER BY s.year ASC
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "total_sales_for_period":
        year = filters.get("year")
        year_from = filters.get("year_from")
        year_to = filters.get("year_to")
        category = filters.get("category")
        product_id = filters.get("product_id")
        product_name = filters.get("product_name")

        where = []
        params: dict[str, Any] = {}
        join_products = bool(category or product_name)

        if isinstance(year, int):
            where.append("s.year = :year")
            params["year"] = year
            label = str(year)
        else:
            if isinstance(year_from, int):
                where.append("s.year >= :year_from")
                params["year_from"] = year_from
            if isinstance(year_to, int):
                where.append("s.year <= :year_to")
                params["year_to"] = year_to
            if isinstance(year_from, int) and isinstance(year_to, int):
                label = f"{year_from}-{year_to}"
            else:
                label = "total"

        if isinstance(product_id, int):
            where.append("s.product_id = :product_id")
            params["product_id"] = product_id

        if isinstance(category, str) and category.strip():
            join_products = True
            where.append("lower(p.category) = lower(:category)")
            params["category"] = category.strip()

        if isinstance(product_name, str) and product_name.strip():
            join_products = True
            name = product_name.strip()
            if "%" not in name:
                name = f"%{name}%"
            where.append("p.name ILIKE :product_name")
            params["product_name"] = name

        join_sql = "JOIN products p ON p.id = s.product_id" if join_products else ""
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        sql = f"""
            SELECT :label::TEXT AS label,
                   COALESCE(SUM(s.revenue), 0)::NUMERIC AS value
            FROM sales s
            {join_sql}
            {where_sql}
        """
        params["label"] = label
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "sales_by_product":
        year = filters.get("year")
        year_from = filters.get("year_from")
        year_to = filters.get("year_to")
        category = filters.get("category")
        limit = filters.get("limit")
        if not isinstance(limit, int) or limit <= 0 or limit > 100:
            limit = 20

        where = []
        params: dict[str, Any] = {"limit": limit}

        if isinstance(year, int):
            where.append("s.year = :year")
            params["year"] = year
        else:
            if isinstance(year_from, int):
                where.append("s.year >= :year_from")
                params["year_from"] = year_from
            if isinstance(year_to, int):
                where.append("s.year <= :year_to")
                params["year_to"] = year_to

        if isinstance(category, str) and category.strip():
            where.append("lower(p.category) = lower(:category)")
            params["category"] = category.strip()

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        sql = f"""
            SELECT p.name AS label,
                   SUM(s.revenue)::NUMERIC AS value
            FROM sales s
            JOIN products p ON p.id = s.product_id
            {where_sql}
            GROUP BY p.name
            ORDER BY value DESC
            LIMIT :limit
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "product_sales_trend":
        year_from = filters.get("year_from")
        year_to = filters.get("year_to")
        product_id = filters.get("product_id")
        product_name = filters.get("product_name")

        where = []
        params: dict[str, Any] = {}

        if isinstance(year_from, int):
            where.append("s.year >= :year_from")
            params["year_from"] = year_from
        if isinstance(year_to, int):
            where.append("s.year <= :year_to")
            params["year_to"] = year_to

        if isinstance(product_id, int):
            where.append("s.product_id = :product_id")
            params["product_id"] = product_id
        elif isinstance(product_name, str) and product_name.strip():
            name = product_name.strip()
            if "%" not in name:
                name = f"%{name}%"
            where.append("p.name ILIKE :product_name")
            params["product_name"] = name
        else:
            raise QueryPlannerError("product_sales_trend requires product_id or product_name")

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        sql = f"""
            SELECT s.year::TEXT AS label,
                   SUM(s.revenue)::NUMERIC AS value
            FROM sales s
            JOIN products p ON p.id = s.product_id
            {where_sql}
            GROUP BY s.year
            ORDER BY s.year ASC
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "sales_by_category":
        year = filters.get("year")
        year_from = filters.get("year_from")
        year_to = filters.get("year_to")

        where = []
        params: dict[str, Any] = {}

        if isinstance(year, int):
            where.append("s.year = :year")
            params["year"] = year
        else:
            if isinstance(year_from, int):
                where.append("s.year >= :year_from")
                params["year_from"] = year_from
            if isinstance(year_to, int):
                where.append("s.year <= :year_to")
                params["year_to"] = year_to

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        sql = f"""
            SELECT p.category AS label,
                   SUM(s.revenue)::NUMERIC AS value
            FROM sales s
            JOIN products p ON p.id = s.product_id
            {where_sql}
            GROUP BY p.category
            ORDER BY value DESC
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "top_bottom_performers":
        year = filters.get("year")
        year_from = filters.get("year_from")
        year_to = filters.get("year_to")
        entity = filters.get("entity")  # 'product' or 'category'
        order = filters.get("order")  # 'top' or 'bottom'
        limit = filters.get("limit")

        if entity not in ("product", "category"):
            # Allow dimensions to guide the grouping
            entity = dim0 if dim0 in ("product", "category") else "product"

        if order not in ("top", "bottom"):
            order = "top"

        if not isinstance(limit, int) or limit <= 0 or limit > 50:
            limit = 5

        where = []
        params: dict[str, Any] = {"limit": limit}

        if isinstance(year, int):
            where.append("s.year = :year")
            params["year"] = year
        else:
            if isinstance(year_from, int):
                where.append("s.year >= :year_from")
                params["year_from"] = year_from
            if isinstance(year_to, int):
                where.append("s.year <= :year_to")
                params["year_to"] = year_to

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        if entity == "category":
            label_expr = "p.category"
            group_expr = "p.category"
        else:
            label_expr = "p.name"
            group_expr = "p.name"

        order_sql = "DESC" if order == "top" else "ASC"

        sql = f"""
            SELECT {label_expr} AS label,
                   SUM(s.revenue)::NUMERIC AS value
            FROM sales s
            JOIN products p ON p.id = s.product_id
            {where_sql}
            GROUP BY {group_expr}
            ORDER BY value {order_sql}
            LIMIT :limit
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "sales_breakdown_for_year":
        year = filters.get("year")
        if not isinstance(year, int):
            raise QueryPlannerError("sales_breakdown_for_year requires filter.year")

        params: dict[str, Any] = {"year": year}

        if dim0 == "category":
            label_expr = "p.category"
            group_expr = "p.category"
        else:
            label_expr = "p.name"
            group_expr = "p.name"

        sql = f"""
            SELECT {label_expr} AS label,
                   SUM(s.revenue)::NUMERIC AS value
            FROM sales s
            JOIN products p ON p.id = s.product_id
            WHERE s.year = :year
            GROUP BY {group_expr}
            ORDER BY value DESC
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "sales_growth_analysis":
        year_from = filters.get("year_from")
        year_to = filters.get("year_to")
        category = filters.get("category")

        where = []
        params: dict[str, Any] = {}
        join_products = bool(category)

        if isinstance(year_from, int):
            where.append("s.year >= :year_from")
            params["year_from"] = year_from
        if isinstance(year_to, int):
            where.append("s.year <= :year_to")
            params["year_to"] = year_to
        if isinstance(category, str) and category.strip():
            join_products = True
            where.append("lower(p.category) = lower(:category)")
            params["category"] = category.strip()

        join_sql = "JOIN products p ON p.id = s.product_id" if join_products else ""
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        sql = f"""
            WITH yearly AS (
              SELECT s.year,
                     SUM(s.revenue)::NUMERIC AS revenue
              FROM sales s
              {join_sql}
              {where_sql}
              GROUP BY s.year
            )
            SELECT y.year::TEXT AS label,
                   (y.revenue - LAG(y.revenue) OVER (ORDER BY y.year))::NUMERIC AS value
            FROM yearly y
            ORDER BY y.year ASC
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "multi_year_comparison":
        year_count = filters.get("year_count")
        average = filters.get("average")
        category = filters.get("category")

        if not isinstance(year_count, int) or year_count <= 0 or year_count > 20:
            year_count = 3

        params: dict[str, Any] = {"year_count": year_count}

        join_products = bool(category)
        extra_where = ""
        if isinstance(category, str) and category.strip():
            join_products = True
            extra_where = "AND lower(p.category) = lower(:category)"
            params["category"] = category.strip()

        join_sql = "JOIN products p ON p.id = s.product_id" if join_products else ""

        if bool(average):
            sql = f"""
                WITH max_year AS (SELECT MAX(year) AS y FROM sales),
                     yearly AS (
                       SELECT s.year,
                              SUM(s.revenue)::NUMERIC AS revenue
                       FROM sales s
                       {join_sql}
                       WHERE s.year >= (SELECT y FROM max_year) - :year_count + 1
                       {extra_where}
                       GROUP BY s.year
                     )
                SELECT 'avg'::TEXT AS label,
                       AVG(revenue)::NUMERIC AS value
                FROM yearly
            """
            return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

        sql = f"""
            WITH max_year AS (SELECT MAX(year) AS y FROM sales)
            SELECT s.year::TEXT AS label,
                   SUM(s.revenue)::NUMERIC AS value
            FROM sales s
            {join_sql}
            WHERE s.year >= (SELECT y FROM max_year) - :year_count + 1
            {extra_where}
            GROUP BY s.year
            ORDER BY s.year ASC
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "clarification_required":
        # Deterministic, safe fallback: return an empty chart.
        sql = "SELECT 1::TEXT AS label, 0::NUMERIC AS value WHERE FALSE"
        return PlannedQuery(sql=sql, params={}, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "revenue_by_category":
        year = filters.get("year")
        where_sql = ""
        params = {}
        if isinstance(year, int):
            where_sql = "WHERE s.year = :year"
            params["year"] = year

        sql = f"""
            SELECT p.category AS label,
                   SUM(s.revenue)::NUMERIC AS value
            FROM sales s
            JOIN products p ON p.id = s.product_id
            {where_sql}
            GROUP BY p.category
            ORDER BY value DESC
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    if intent_name == "top_products":
        year = filters.get("year")
        limit = filters.get("limit")
        if not isinstance(limit, int) or limit <= 0 or limit > 50:
            limit = 10

        where_sql = ""
        params = {"limit": limit}
        if isinstance(year, int):
            where_sql = "WHERE s.year = :year"
            params["year"] = year

        sql = f"""
            SELECT p.name AS label,
                   SUM(s.revenue)::NUMERIC AS value
            FROM sales s
            JOIN products p ON p.id = s.product_id
            {where_sql}
            GROUP BY p.name
            ORDER BY value DESC
            LIMIT :limit
        """
        return PlannedQuery(sql=sql, params=params, chart_type=chart, label_field="label", value_field="value")

    raise QueryPlannerError(f"No planner mapping for intent: {intent_name}")


def as_sqlalchemy_text(plan: PlannedQuery):
    return text(plan.sql)
