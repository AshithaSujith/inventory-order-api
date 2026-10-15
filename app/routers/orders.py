from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import OrderCreate, OrderResponse
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Creates an order in Draft status containing one or more product lines. Rejects unknown products, duplicate lines, or invalid quantities.",
)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
):
    return order_service.create_order(db=db, order_in=order_in)


@router.get(
    "",
    response_model=List[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="List all orders",
    description="Retrieves a list of all orders with their current statuses and item lines.",
)
def list_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return order_service.list_orders(db=db, skip=skip, limit=limit)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="View order by ID",
    description="Retrieves order details, items, and current status.",
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    return order_service.get_order_by_id(db=db, order_id=order_id)


@router.post(
    "/{order_id}/confirm",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm an order",
    description="Confirms a Draft order if all items exist and have sufficient stock. Atomically deducts stock. Fails without partial changes if any item cannot be fulfilled.",
)
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    return order_service.confirm_order(db=db, order_id=order_id)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel an order",
    description="Cancels an order. Draft orders are cancelled without changing stock. Confirmed orders restore their stock. Cancelled orders cannot be cancelled again.",
)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    return order_service.cancel_order(db=db, order_id=order_id)
