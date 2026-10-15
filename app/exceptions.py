class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundError(AppException):
    """Raised when a requested resource (product, order) does not exist."""
    pass


class InsufficientStockError(AppException):
    """Raised when an order cannot be confirmed due to lack of available stock."""
    pass


class InvalidOrderStateError(AppException):
    """Raised when an action is invalid for the order's current status."""
    pass


class DuplicateProductLineError(AppException):
    """Raised when an order contains multiple lines referencing the same product."""
    pass


class InvalidQuantityError(AppException):
    """Raised when a quantity provided violates business constraints."""
    pass
