from __future__ import annotations

import json
from typing import Any

from app.query_planner.catalog import INTENTS
from app.settings import settings

class MCPError(RuntimeError):
    pass


_SCHEMA_DESCRIPTION = """
Database schema:
- products(id, name, category)
- features(id, name)
- product_features(product_id, feature_id)
- sales(id, product_id, year, revenue)
""".strip()


def _allowed_guide() -> str:
    intents = list(INTENTS.keys())
    return json.dumps(
        {
            "intents": intents,
            "metrics": ["total_revenue"],
            "dimensions": ["year", "category", "product"],
            "filters": {
                "years": "array of integers",
                "year_from": "integer",
                "year_to": "integer",
                "year": "integer",
                "category": "string",
                "categories": "array of strings",
                "product_id": "integer",
                "product_name": "string",
                "limit": "integer (1-50)",
                "order": "string ('top'|'bottom')",
                "entity": "string ('product'|'category')",
                "year_count": "integer (1-20)",
                "average": "boolean",
            },
            "charts": ["line", "bar"],
        },
        indent=2,
    )


def _normalize_category(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip().strip("\"'")
    s = s.strip(" .,:;()[]{}")
    if not s:
        return None
    return " ".join(w.capitalize() for w in s.split())


def _extract_category(text: str) -> str | None:
    import re

    t = text.strip()
    # Common patterns:
    # - "in Toyota category"
    # - "only in the Nissan category"
    # - "category Nissan" / "category: Toyota"
    m = re.search(r"\b(?:only\s+)?in\s+the\s+([\w &/\-]+?)\s+category\b", t, re.IGNORECASE)
    if not m:
        m = re.search(r"\b(?:only\s+)?in\s+([\w &/\-]+?)\s+category\b", t, re.IGNORECASE)
    if not m:
        m = re.search(r"\bcategory\s*[:=]?\s*([\w &/\-]+)\b", t, re.IGNORECASE)
    if not m:
        return None
    return _normalize_category(m.group(1))


def _mentions_comparison(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in (" vs ", " versus ", "compare ", "comparison"))


# Stub parse is called when there is gemini api keys or if you have reached rate limits on gemini api
# It tries to determine the intent by looking for patterns/keywords in the question text
# This is not 100% reliable and is only used as a fallback alternative.
def _stub_parse(question: str) -> dict[str, Any]:
    q = question.lower()
    category = _extract_category(question)

    def _base_filters() -> dict[str, Any]:
        f: dict[str, Any] = {}
        if category:
            f["category"] = category
        return f

    # Only use revenue_by_category when user asks for a breakdown/grouping.
    if any(k in q for k in ("by category", "per category", "group by category", "grouped by category", "breakdown by category")):
        year = _extract_year(q)
        payload: dict[str, Any] = {
            "intent": "sales_by_category",
            "metrics": ["total_revenue"],
            "dimensions": ["category"],
            "filters": _base_filters(),
            "chart": "bar",
        }
        if year is not None:
            payload["filters"]["year"] = year
        return payload

    if ("top" in q or "best-selling" in q or "best selling" in q) and ("product" in q or "products" in q or "category" in q or "categories" in q):
        year = _extract_year(q)
        limit = _extract_limit(q) or 10     # fallback to limit of 10
        entity = "category" if ("category" in q or "categories" in q) else "product"
        payload = {
            "intent": "top_bottom_performers",
            "metrics": ["total_revenue"],
            "dimensions": [entity],
            "filters": {**_base_filters(), "limit": limit, "order": "top", "entity": entity},
            "chart": "bar",
        }
        if year is not None:
            payload["filters"]["year"] = year
        return payload

    if any(k in q for k in ("worst", "lowest", "bottom")) and ("product" in q or "products" in q or "category" in q or "categories" in q):
        year = _extract_year(q)
        limit = _extract_limit(q) or 5     # fallback to limit of 5
        entity = "category" if ("category" in q or "categories" in q) else "product"
        payload = {
            "intent": "top_bottom_performers",
            "metrics": ["total_revenue"],
            "dimensions": [entity],
            "filters": {**_base_filters(), "limit": limit, "order": "bottom", "entity": entity},
            "chart": "bar",
        }
        if year is not None:
            payload["filters"]["year"] = year
        return payload

    if any(k in q for k in ("break down", "breakdown", "category-wise", "category wise")):
        year = _extract_year(q)
        if year is not None:
            dim = "category" if ("category" in q or "categories" in q) else "product"
            return {
                "intent": "sales_breakdown_for_year",
                "metrics": ["total_revenue"],
                "dimensions": [dim],
                "filters": {**_base_filters(), "year": year},
                "chart": "bar",
            }

    # Prefer interpreting ranges like "2021 to 2026" as a trend.
    year_from, year_to = _extract_year_range(q)
    if year_from is not None or year_to is not None:
        filters: dict[str, Any] = {}
        if year_from is not None:
            filters["year_from"] = year_from
        if year_to is not None:
            filters["year_to"] = year_to
        filters.update(_base_filters())

        import re

        m = re.search(r"\"([^\"]+)\"", question)
        if m and ("trend" in q or "over time" in q or "year by year" in q):
            filters["product_name"] = m.group(1).strip()
            return {
                "intent": "product_sales_trend",
                "metrics": ["total_revenue"],
                "dimensions": ["year"],
                "filters": filters,
                "chart": "line",
            }

        # Growth analysis
        if any(k in q for k in ("year-over-year", "year over year", "yoy", "growth", "declin")):
            return {
                "intent": "sales_growth_analysis",
                "metrics": ["total_revenue"],
                "dimensions": ["year"],
                "filters": filters,
                "chart": "line",
            }

        return {
            "intent": "sales_trend_over_time",
            "metrics": ["total_revenue"],
            "dimensions": ["year"],
            "filters": filters,
            "chart": "line",
        }

    years = _extract_two_years(q)
    if years is not None and _mentions_comparison(question):
        filters: dict[str, Any] = {"years": years, **_base_filters()}
        return {
            "intent": "sales_comparison_by_year",
            "metrics": ["total_revenue"],
            "dimensions": ["year"],
            "filters": filters,
            "chart": "bar",
        }

    if years is not None and any(k in q for k in ("gap", "difference", "increase", "decrease")):
        filters: dict[str, Any] = {"years": years, **_base_filters()}
        return {
            "intent": "sales_comparison_by_year",
            "metrics": ["total_revenue"],
            "dimensions": ["year"],
            "filters": filters,
            "chart": "bar",
        }

    if any(k in q for k in ("last 3 years", "last three years")):
        filters = {**_base_filters(), "year_count": 3}
        return {
            "intent": "multi_year_comparison",
            "metrics": ["total_revenue"],
            "dimensions": ["year"],
            "filters": filters,
            "chart": "bar",
        }

    if "average" in q and ("year" in q or "yearly" in q):
        filters = {**_base_filters(), "year_count": 5, "average": True}
        return {
            "intent": "multi_year_comparison",
            "metrics": ["total_revenue"],
            "dimensions": ["year"],
            "filters": filters,
            "chart": "bar",
        }

    if any(k in q for k in ("total sales", "total revenue", "how much did we sell", "how much revenue")):
        year = _extract_year(q)
        if year is not None:
            return {
                "intent": "total_sales_for_period",
                "metrics": ["total_revenue"],
                "dimensions": ["year"],
                "filters": {**_base_filters(), "year": year},
                "chart": "bar",
            }

    if any(k in q for k in ("which products", "by product", "across all products", "rank products")):
        year = _extract_year(q)
        filters = _base_filters()
        if year is not None:
            filters["year"] = year
        return {
            "intent": "sales_by_product",
            "metrics": ["total_revenue"],
            "dimensions": ["product"],
            "filters": filters,
            "chart": "bar",
        }

    if any(k in q for k in ("category generates", "between categories", "categories performing", "different categories")):
        year = _extract_year(q)
        filters = _base_filters()
        if year is not None:
            filters["year"] = year
        return {
            "intent": "sales_by_category",
            "metrics": ["total_revenue"],
            "dimensions": ["category"],
            "filters": filters,
            "chart": "bar",
        }

    if any(k in q for k in ("overall", "overview", "how are we doing", "sales performance", "business performing")):
        return {
            "intent": "clarification_required",
            "metrics": ["total_revenue"],
            "dimensions": ["year"],
            "filters": {},
            "chart": "line",
        }

    # Default to a sales trend over time
    filters: dict[str, Any] = _base_filters()
    return {
        "intent": "sales_trend_over_time",
        "metrics": ["total_revenue"],
        "dimensions": ["year"],
        "filters": filters,
        "chart": "line",
    }


def _extract_year(text: str) -> int | None:
    for year in range(2015, 2031):
        if str(year) in text:
            return year
    return None


def _extract_two_years(text: str) -> list[int] | None:
    found = []
    for year in range(2015, 2031):
        if str(year) in text:
            found.append(year)
    unique = sorted(set(found))
    if len(unique) >= 2:
        return unique[:2]
    return None


def _extract_year_range(text: str) -> tuple[int | None, int | None]:
    # naive patterns like 2020-2026
    import re

    m = re.search(r"(20\d{2})\s*[-–]\s*(20\d{2})", text)
    if m:
        return int(m.group(1)), int(m.group(2))

    # Patterns like "2021 to 2026" or "2021 through 2026"
    m = re.search(r"(20\d{2})\s+(?:to|through|thru)\s+(20\d{2})", text)
    if m:
        return int(m.group(1)), int(m.group(2))

    # Pattern like "between 2021 and 2026"
    m = re.search(r"between\s+(20\d{2})\s+and\s+(20\d{2})", text)
    if m:
        return int(m.group(1)), int(m.group(2))

    year_from = None
    year_to = None
    m = re.search(r"from\s+(20\d{2})", text)
    if m:
        year_from = int(m.group(1))
    m = re.search(r"to\s+(20\d{2})", text)
    if m:
        year_to = int(m.group(1))

    return year_from, year_to


def _extract_limit(text: str) -> int | None:
    import re

    m = re.search(r"top\s+(\d+)", text)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


# Parses user's question to determine intent. Uses gemini API if available and falls back to pattern primitive recognition if not available
def parse_intent(question: str) -> dict[str, Any]:
    if settings.llm_mode.lower() == "stub":
        print("⚠️  Using stub intent parser (set LLM_MODE=gemini to enable AI)")
        return _stub_parse(question)

    if not settings.gemini_api_key:
        print("⚠️  GEMINI_API_KEY is not set; falling back to stub parser")
        return _stub_parse(question)

    try:
        import google.generativeai as genai
    except Exception:  # pragma: no cover
        print("⚠️  Gemini SDK not available; falling back to stub parser")
        return _stub_parse(question)

    genai.configure(api_key=settings.gemini_api_key)
    print(f"✅  Using Gemini model: {settings.gemini_model}")
    model = genai.GenerativeModel(settings.gemini_model)

    system = (
        "You are a strict JSON intent parser. "
        "You MUST output a single JSON object and nothing else. "
        "No markdown, no code fences, no comments. "
        "Never output SQL. "
        "Only use allowed intents/metrics/dimensions/filters."
    )

    prompt = f"""
{system}

User question:
{question}

{_SCHEMA_DESCRIPTION}

Allowed options (must adhere):
{_allowed_guide()}

Return JSON with shape:
{{
  "intent": string,
  "metrics": [string],
  "dimensions": [string],
  "filters": object,
  "chart": "line"|"bar"
}}
""".strip()
    
    print("Input Token count:", model.count_tokens(prompt).total_tokens)

    try:
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise MCPError("Gemini output must be a JSON object")
        return payload
    except Exception:
        print("⚠️  Gemini unavailable or invalid output; falling back to stub parser")
        return _stub_parse(question)
