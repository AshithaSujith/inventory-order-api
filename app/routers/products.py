from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ProductCreate, ProductResponse
from app.services import product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Creates a product with a unique ID, non-empty name, and non-negative stock quantity.",
)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
):
    return product_service.create_product(db=db, product_in=product_in)


@router.get(
    "",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="List all products",
    description="Retrieves a list of all products along with their available stock quantities.",
)
def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return product_service.list_products(db=db, skip=skip, limit=limit)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
    description="Retrieves product details including current stock quantity.",
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    return product_service.get_product_by_id(db=db, product_id=product_id)
