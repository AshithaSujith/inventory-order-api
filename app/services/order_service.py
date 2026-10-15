from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import Order, OrderItem, OrderStatus, Product
from app.schemas import OrderCreate
from app.exceptions import (
    EntityNotFoundError,
    InsufficientStockError,
    InvalidOrderStateError,
    InvalidQuantityError,
)


def create_order(db: Session, order_in: OrderCreate) -> Order:
    """
    Create a new order in Draft status with one or more product lines.
    Verifies that all referenced products exist before creating the order.
    """
    if not order_in.items:
        raise InvalidQuantityError("An order must contain at least one item.")

    # Validate that every product exists in DB
    for item_in in order_in.items:
        product = db.get(Product, item_in.product_id)
        if not product:
            raise EntityNotFoundError(
                f"Product with ID {item_in.product_id} does not exist."
            )

    order = Order(status=OrderStatus.DRAFT)
    db.add(order)
    db.flush()  # Generate order.id for foreign keys

    for item_in in order_in.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity,
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)
    return order


def get_order_by_id(db: Session, order_id: int) -> Order:
    """Retrieve an order by ID along with its items."""
    order = db.get(Order, order_id)
    if not order:
        raise EntityNotFoundError(f"Order with ID {order_id} not found.")
    return order


def list_orders(db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
    """List orders with pagination."""
    stmt = select(Order).offset(skip).limit(limit).order_by(Order.id.desc())
    return list(db.scalars(stmt).all())


def confirm_order(db: Session, order_id: int) -> Order:
    """
    Confirm a Draft order.
    Rules:
    - Order must be in Draft status.
    - Cannot confirm an already Confirmed order.
    - Cannot confirm a Cancelled order.
    - Every product in the order must exist and have sufficient stock.
    - If any product cannot be fulfilled, the operation fails atomically with
      zero stock deductions and status unchanged.
    - Deducts stock upon successful confirmation.
    """
    order = db.get(Order, order_id)
    if not order:
        raise EntityNotFoundError(f"Order with ID {order_id} not found.")

    if order.status == OrderStatus.CONFIRMED:
        raise InvalidOrderStateError("Order is already confirmed and cannot be confirmed again.")

    if order.status == OrderStatus.CANCELLED:
        raise InvalidOrderStateError("Cannot confirm an order that has been cancelled.")

    if order.status != OrderStatus.DRAFT:
        raise InvalidOrderStateError(f"Cannot confirm order with current status '{order.status.value}'.")

    try:
        # Step 1: Pre-validation of all items for stock sufficiency
        # We fetch each product and verify availability
        product_map = {}
        for item in order.items:
            product = db.get(Product, item.product_id)
            if not product:
                raise EntityNotFoundError(
                    f"Product with ID {item.product_id} was not found."
                )
            if product.stock_quantity < item.quantity:
                raise InsufficientStockError(
                    f"Insufficient stock for product '{product.name}' (ID: {product.id}). "
                    f"Required: {item.quantity}, Available: {product.stock_quantity}."
                )
            product_map[item.product_id] = product

        # Step 2: Atomic stock deduction
        for item in order.items:
            product = product_map[item.product_id]
            product.stock_quantity -= item.quantity

        # Step 3: Transition status
        order.status = OrderStatus.CONFIRMED
        db.commit()
        db.refresh(order)
        return order

    except Exception:
        db.rollback()
        raise


def cancel_order(db: Session, order_id: int) -> Order:
    """
    Cancel an order.
    Rules:
    - Cancelling a Draft order updates status without touching stock.
    - Cancelling a Confirmed order restores all deducted stock items.
    - A Cancelled order cannot be cancelled again.
    """
    order = db.get(Order, order_id)
    if not order:
        raise EntityNotFoundError(f"Order with ID {order_id} not found.")

    if order.status == OrderStatus.CANCELLED:
        raise InvalidOrderStateError("Order is already cancelled and cannot be cancelled again.")

    try:
        if order.status == OrderStatus.DRAFT:
            # Cancel draft order without modifying stock
            order.status = OrderStatus.CANCELLED
            db.commit()
            db.refresh(order)
            return order

        elif order.status == OrderStatus.CONFIRMED:
            # Restore stock for each item
            for item in order.items:
                product = db.get(Product, item.product_id)
                if product:
                    product.stock_quantity += item.quantity
            order.status = OrderStatus.CANCELLED
            db.commit()
            db.refresh(order)
            return order

        else:
            raise InvalidOrderStateError(f"Cannot cancel order in status '{order.status.value}'.")

    except Exception:
        db.rollback()
        raise
