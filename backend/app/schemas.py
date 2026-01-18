from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


ChartType = Literal["line", "bar"]


class Dataset(BaseModel):
    label: str
    data: list[float]


class QueryResponse(BaseModel):
    title: str | None = None
    chartType: ChartType
    labels: list[str]
    datasets: list[Dataset]


class ErrorResponse(BaseModel):
    error: str
    detail: Any | None = None


class Product(BaseModel):
    id: int
    name: str
    category: str


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=200)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=200)


class ProductList(BaseModel):
    items: list[Product]


class Sale(BaseModel):
    id: int
    product_id: int
    year: int
    revenue: float
    product_name: str | None = None
    product_category: str | None = None


class SaleCreate(BaseModel):
    product_id: int
    year: int
    revenue: float


class SaleUpdate(BaseModel):
    product_id: int | None = None
    year: int | None = None
    revenue: float | None = None


class SaleList(BaseModel):
    items: list[Sale]
