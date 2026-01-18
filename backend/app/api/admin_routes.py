from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.session import get_engine
from app.schemas import (
    ErrorResponse,
    Product,
    ProductCreate,
    ProductList,
    ProductUpdate,
    Sale,
    SaleCreate,
    SaleList,
    SaleUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _to_float(v):
    if v is None:
        return 0.0
    if isinstance(v, float):
        return v
    if isinstance(v, int):
        return float(v)
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


# --- Products Management ---


@router.get("/products", response_model=ProductList)
def list_products():
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, category
                FROM products
                ORDER BY id ASC
                """
            )
        ).mappings().all()

    return {"items": [Product(**r) for r in rows]}


@router.post("/products", response_model=Product, responses={400: {"model": ErrorResponse}})
def create_product(payload: ProductCreate):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    INSERT INTO products (name, category)
                    VALUES (:name, :category)
                    RETURNING id, name, category
                    """
                ),
                {"name": payload.name, "category": payload.category},
            ).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "db_error", "detail": str(e)})

    if not row:
        raise HTTPException(status_code=400, detail={"error": "db_error", "detail": "Insert failed"})

    return Product(**row)


@router.patch(
    "/products/{product_id}", response_model=Product, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def update_product(product_id: int, payload: ProductUpdate):
    updates = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.category is not None:
        updates["category"] = payload.category

    if not updates:
        raise HTTPException(status_code=400, detail={"error": "validation", "detail": "No fields to update"})

    set_sql = ", ".join([f"{k} = :{k}" for k in updates.keys()])
    params = {**updates, "id": product_id}

    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    f"""
                    UPDATE products
                    SET {set_sql}
                    WHERE id = :id
                    RETURNING id, name, category
                    """
                ),
                params,
            ).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "db_error", "detail": str(e)})

    if not row:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": "Product not found"})

    return Product(**row)


@router.delete(
    "/products/{product_id}", response_model=dict, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def delete_product(product_id: int):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    DELETE FROM products
                    WHERE id = :id
                    RETURNING id
                    """
                ),
                {"id": product_id},
            ).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "db_error", "detail": str(e)})

    if not row:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": "Product not found"})

    return {"ok": True}


# --- Sales Management ---


@router.get("/sales", response_model=SaleList)
def list_sales(limit: int = 200, offset: int = 0):
    limit = max(1, min(int(limit), 1000))
    offset = max(0, int(offset))

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT s.id,
                       s.product_id,
                       s.year,
                       s.revenue,
                       p.name AS product_name,
                       p.category AS product_category
                FROM sales s
                JOIN products p ON p.id = s.product_id
                ORDER BY s.year DESC, s.id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"limit": limit, "offset": offset},
        ).mappings().all()

    items = []
    for r in rows:
        r = dict(r)
        r["revenue"] = _to_float(r.get("revenue"))
        items.append(Sale(**r))

    return {"items": items}


@router.post("/sales", response_model=Sale, responses={400: {"model": ErrorResponse}})
def create_sale(payload: SaleCreate):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    INSERT INTO sales (product_id, year, revenue)
                    VALUES (:product_id, :year, :revenue)
                    RETURNING id, product_id, year, revenue
                    """
                ),
                {"product_id": payload.product_id, "year": payload.year, "revenue": payload.revenue},
            ).mappings().first()
            if not row:
                raise RuntimeError("Insert failed")

            prod = conn.execute(
                text("""SELECT name, category FROM products WHERE id = :id"""),
                {"id": row["product_id"]},
            ).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "db_error", "detail": str(e)})

    data = dict(row)
    data["revenue"] = _to_float(data.get("revenue"))
    if prod:
        data["product_name"] = prod.get("name")
        data["product_category"] = prod.get("category")
    return Sale(**data)


@router.patch(
    "/sales/{sale_id}", response_model=Sale, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def update_sale(sale_id: int, payload: SaleUpdate):
    updates = {}
    if payload.product_id is not None:
        updates["product_id"] = payload.product_id
    if payload.year is not None:
        updates["year"] = payload.year
    if payload.revenue is not None:
        updates["revenue"] = payload.revenue

    if not updates:
        raise HTTPException(status_code=400, detail={"error": "validation", "detail": "No fields to update"})

    set_sql = ", ".join([f"{k} = :{k}" for k in updates.keys()])
    params = {**updates, "id": sale_id}

    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    f"""
                    UPDATE sales
                    SET {set_sql}
                    WHERE id = :id
                    RETURNING id, product_id, year, revenue
                    """
                ),
                params,
            ).mappings().first()
            if not row:
                raise KeyError("not_found")

            prod = conn.execute(
                text("""SELECT name, category FROM products WHERE id = :id"""),
                {"id": row["product_id"]},
            ).mappings().first()
    except KeyError:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": "Sale not found"})
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "db_error", "detail": str(e)})

    data = dict(row)
    data["revenue"] = _to_float(data.get("revenue"))
    if prod:
        data["product_name"] = prod.get("name")
        data["product_category"] = prod.get("category")
    return Sale(**data)


@router.delete(
    "/sales/{sale_id}", response_model=dict, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
def delete_sale(sale_id: int):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    DELETE FROM sales
                    WHERE id = :id
                    RETURNING id
                    """
                ),
                {"id": sale_id},
            ).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "db_error", "detail": str(e)})

    if not row:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": "Sale not found"})

    return {"ok": True}
