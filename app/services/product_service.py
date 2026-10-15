from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import Product
from app.schemas import ProductCreate
from app.exceptions import EntityNotFoundError, InvalidQuantityError


def create_product(db: Session, product_in: ProductCreate) -> Product:
    """Create a new product with validated stock quantity."""
    if product_in.stock_quantity < 0:
        raise InvalidQuantityError("Stock quantity cannot be negative.")

    product = Product(
        name=product_in.name,
        stock_quantity=product_in.stock_quantity,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_product_by_id(db: Session, product_id: int) -> Product:
    """Retrieve a single product by ID, raising EntityNotFoundError if missing."""
    product = db.get(Product, product_id)
    if not product:
        raise EntityNotFoundError(f"Product with ID {product_id} not found.")
    return product


def list_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    """List products with pagination."""
    stmt = select(Product).offset(skip).limit(limit).order_by(Product.id.asc())
    return list(db.scalars(stmt).all())
