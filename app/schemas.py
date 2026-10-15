from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import OrderStatus


# ---------------------------------------------------------
# Product Schemas
# ---------------------------------------------------------
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the product")
    stock_quantity: int = Field(..., ge=0, description="Available stock quantity (must be >= 0)")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Product name cannot be empty or whitespace only.")
        return trimmed


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Order Item Schemas
# ---------------------------------------------------------
class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0, description="Valid ID of the product")
    quantity: int = Field(..., gt=0, description="Quantity to order (must be positive integer)")


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_item(cls, item):
        return cls(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else None,
            quantity=item.quantity,
        )


# ---------------------------------------------------------
# Order Schemas
# ---------------------------------------------------------
class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(
        ...,
        min_length=1,
        description="One or more product lines for the order",
    )

    @field_validator("items")
    @classmethod
    def validate_unique_products(cls, items: List[OrderItemCreate]) -> List[OrderItemCreate]:
        if not items:
            raise ValueError("Order must contain at least one item.")
        
        seen = set()
        duplicates = set()
        for item in items:
            if item.product_id in seen:
                duplicates.add(item.product_id)
            seen.add(item.product_id)

        if duplicates:
            sorted_dups = sorted(list(duplicates))
            raise ValueError(
                f"Duplicate product IDs detected in order items: {sorted_dups}. "
                "Each product must be specified once per order with the consolidated quantity."
            )
        return items


class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Error Schemas
# ---------------------------------------------------------
class ErrorDetail(BaseModel):
    error: str
    detail: Optional[str] = None
