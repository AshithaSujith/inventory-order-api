from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import engine, Base
from app.routers import products, orders
from app.exceptions import (
    EntityNotFoundError,
    InsufficientStockError,
    InvalidOrderStateError,
    DuplicateProductLineError,
    InvalidQuantityError,
    AppException,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Inventory Order Management API for managing products, stock, "
        "and sales orders with transactional confirmation and cancellation."
    ),
    lifespan=lifespan,
)

# Include API routers
app.include_router(products.router)
app.include_router(orders.router)


# -----------------------------------------------------------------------------
# Exception Handlers
# -----------------------------------------------------------------------------
@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Not Found", "detail": exc.message},
    )


@app.exception_handler(InsufficientStockError)
async def insufficient_stock_handler(request: Request, exc: InsufficientStockError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Insufficient Stock", "detail": exc.message},
    )


@app.exception_handler(InvalidOrderStateError)
async def invalid_order_state_handler(request: Request, exc: InvalidOrderStateError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid Order State", "detail": exc.message},
    )


@app.exception_handler(DuplicateProductLineError)
async def duplicate_product_handler(request: Request, exc: DuplicateProductLineError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Duplicate Product Line", "detail": exc.message},
    )


@app.exception_handler(InvalidQuantityError)
async def invalid_quantity_handler(request: Request, exc: InvalidQuantityError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid Quantity", "detail": exc.message},
    )


@app.exception_handler(AppException)
async def generic_app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request", "detail": exc.message},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", []) if x != "body"]
        field = " -> ".join(loc) if loc else "body"
        msg = err.get("msg")
        errors.append(f"{field}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": "Validation Error",
            "detail": errors,
        },
    )


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint indicating API operational status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
    }
