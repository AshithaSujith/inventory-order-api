# Inventory Order API

A robust, production-ready backend JSON API built with **FastAPI**, **SQLite**, and **SQLAlchemy** for managing products, inventory stock, and sales orders. Designed to adhere strictly to domain business rules, atomic transaction semantics, and comprehensive test coverage.

---

## Table of Contents

- [Overview](#overview)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Setup](#installation--setup)
  - [Database Seeding (Optional)](#database-seeding-optional)
  - [Running the Server](#running-the-server)
- [Interactive API Documentation](#interactive-api-documentation)
- [API Endpoints & Examples](#api-endpoints--examples)
  - [Products](#products)
  - [Orders](#orders)
- [Business Rules & Design Decisions](#business-rules--design-decisions)
  - [Order State Transitions](#order-state-transitions)
  - [Stock Deduction & Restoral Rules](#stock-deduction--restoral-rules)
  - [Atomic All-or-Nothing Confirmation](#atomic-all-or-nothing-confirmation)
  - [Duplicate Product Line Decision](#duplicate-product-line-decision)
- [Automated Tests](#automated-tests)
- [Assumptions & Known Limitations](#assumptions--known-limitations)
- [AI Tools Disclosure](#ai-tools-disclosure)

---

## Overview

This project was built for the **Junior Backend Developer Take-Home Project**. It provides a reliable service to:
- Create and list inventory products with validated non-negative stock.
- Place multi-item orders in `Draft` status.
- Atomically confirm orders if and only if sufficient inventory exists across all line items.
- Cancel draft or confirmed orders, accurately restoring stock where applicable while preventing illegal repeated operations.

---

## Architecture & Tech Stack

- **Language:** Python 3.10+ (tested with Python 3.13)
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (modern ASGI web framework with automatic OpenAPI documentation and Pydantic validation)
- **Database / ORM:** SQLite with [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (relational data modeling with foreign key integrity enabled via `PRAGMA foreign_keys = ON`)
- **Validation:** [Pydantic v2](https://docs.pydantic.dev/) for request/response serialization and schema enforcement.
- **Testing:** [pytest](https://docs.pytest.org/) and `HTTPX` / Starlette `TestClient` using isolated in-memory SQLite databases.

### Separation of Concerns
The application follows a clean layered architecture:
- **`app/routers/`**: Transport layer handling HTTP requests, query parameters, status codes, and input/output contracts.
- **`app/services/`**: Core business and domain logic layer where transactional rules, state machines, and inventory mutations are executed.
- **`app/models.py`**: Relational persistence schema defining table constraints, relationships, and cascading rules.
- **`app/schemas.py`**: Strongly typed data transfer objects (DTOs) with input normalization and validation constraints.
- **`app/exceptions.py`**: Domain-specific error types mapped to standard HTTP status codes (`400`, `404`, `422`).

---

## Project Structure

```text
task1/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint and global exception handlers
│   ├── config.py                # Environment configuration and settings
│   ├── database.py              # SQLite engine, session factory, and foreign key pragma
│   ├── exceptions.py            # Domain-specific exceptions
│   ├── models.py                # SQLAlchemy ORM models (Product, Order, OrderItem, OrderStatus)
│   ├── schemas.py               # Pydantic schemas and validators
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── products.py          # /products endpoints
│   │   └── orders.py            # /orders endpoints
│   └── services/
│       ├── __init__.py
│       ├── product_service.py   # Product domain operations
│       └── order_service.py     # Order lifecycle, stock validation, and atomic state transitions
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Isolated in-memory SQLite fixtures and test client
│   ├── test_products.py         # Product endpoint and validation tests
│   └── test_orders.py           # Order lifecycle, atomicity, idempotency, and stock tests
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Dependency manifest
├── seed_data.py                 # Optional script to pre-populate database with sample products
├── .gitignore                   # Ignore virtual environment, pycache, SQLite files
└── README.md                    # Project documentation
```

---

## Getting Started

### Prerequisites
- Python 3.10 or higher (Python 3.13 recommended)
- `pip` package manager
- `git`

### Installation & Setup

1. **Clone or navigate to the repository directory:**
   ```bash
   cd task1
   ```

2. **Create and activate a virtual environment:**
   - **On Windows (PowerShell / Command Prompt):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **On macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Database Seeding (Optional)
To quickly populate the local database with sample products for testing, run:
```bash
python seed_data.py
```
This inserts 5 sample items (Keyboards, Mice, Monitors, etc.) into `inventory.db`.

### Running the Server

Start the development server using `uvicorn`:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at: `http://127.0.0.1:8000`

---

## Interactive API Documentation

FastAPI provides interactive API documentation out of the box:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints & Examples

### Products

#### 1. Create a Product
- **Endpoint:** `POST /products`
- **Body:**
  ```json
  {
    "name": "Mechanical Keyboard",
    "stock_quantity": 25
  }
  ```
- **Example cURL:**
  ```bash
  curl -X POST "http://127.0.0.1:8000/products" \
       -H "Content-Type: application/json" \
       -d '{"name": "Mechanical Keyboard", "stock_quantity": 25}'
  ```
- **Response:** `201 Created`
  ```json
  {
    "name": "Mechanical Keyboard",
    "stock_quantity": 25,
    "id": 1,
    "created_at": "2026-10-13T10:45:00Z"
  }
  ```

#### 2. List All Products
- **Endpoint:** `GET /products`
- **Example cURL:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/products"
  ```
- **Response:** `200 OK`
  ```json
  [
    {
      "id": 1,
      "name": "Mechanical Keyboard",
      "stock_quantity": 25,
      "created_at": "2026-10-13T10:45:00Z"
    }
  ]
  ```

#### 3. View Product by ID
- **Endpoint:** `GET /products/{id}`
- **Example cURL:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/products/1"
  ```

---

### Orders

#### 1. Create an Order
- **Endpoint:** `POST /orders`
- **Body:**
  ```json
  {
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      }
    ]
  }
  ```
- **Example cURL:**
  ```bash
  curl -X POST "http://127.0.0.1:8000/orders" \
       -H "Content-Type: application/json" \
       -d '{"items": [{"product_id": 1, "quantity": 2}]}'
  ```
- **Response:** `201 Created`
  ```json
  {
    "id": 1,
    "status": "Draft",
    "created_at": "2026-10-13T10:46:00Z",
    "updated_at": "2026-10-13T10:46:00Z",
    "items": [
      {
        "id": 1,
        "product_id": 1,
        "product_name": "Mechanical Keyboard",
        "quantity": 2
      }
    ]
  }
  ```

#### 2. View Order by ID
- **Endpoint:** `GET /orders/{id}`
- **Example cURL:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/orders/1"
  ```
- **Response:** `200 OK`

#### 3. List All Orders
- **Endpoint:** `GET /orders`
- **Example cURL:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/orders"
  ```

#### 4. Confirm an Order
- **Endpoint:** `POST /orders/{id}/confirm`
- **Example cURL:**
  ```bash
  curl -X POST "http://127.0.0.1:8000/orders/1/confirm"
  ```
- **Response (Success):** `200 OK`
  ```json
  {
    "id": 1,
    "status": "Confirmed",
    "created_at": "2026-10-13T10:46:00Z",
    "updated_at": "2026-10-13T10:47:00Z",
    "items": [
      {
        "id": 1,
        "product_id": 1,
        "product_name": "Mechanical Keyboard",
        "quantity": 2
      }
    ]
  }
  ```
- **Response (Insufficient Stock):** `400 Bad Request`
  ```json
  {
    "error": "Insufficient Stock",
    "detail": "Insufficient stock for product 'Mechanical Keyboard' (ID: 1). Required: 50, Available: 25."
  }
  ```

#### 5. Cancel an Order
- **Endpoint:** `POST /orders/{id}/cancel`
- **Example cURL:**
  ```bash
  curl -X POST "http://127.0.0.1:8000/orders/1/cancel"
  ```
- **Response:** `200 OK`
  ```json
  {
    "id": 1,
    "status": "Cancelled",
    "created_at": "2026-10-13T10:46:00Z",
    "updated_at": "2026-10-13T10:48:00Z",
    "items": [ ... ]
  }
  ```

---

## Business Rules & Design Decisions

### Order State Transitions

```
               [Create Order]
                     │
                     ▼
                 ┌───────┐
                 │ Draft │
                 └───┬───┘
          Confirm    │    Cancel
         ┌───────────┴───────────┐
         ▼                       ▼
   ┌───────────┐           ┌───────────┐
   │ Confirmed │           │ Cancelled │
   └─────┬─────┘           └───────────┘
         │                       ▲
         │        Cancel         │
         └───────────────────────┘
```

1. **`Draft` $\rightarrow$ `Confirmed`**:
   - Stock is evaluated for every line item.
   - If all items have sufficient stock, stock is deducted and order becomes `Confirmed`.
2. **`Draft` $\rightarrow$ `Cancelled`**:
   - Status changes to `Cancelled`. Stock was never deducted, so stock remains untouched.
3. **`Confirmed` $\rightarrow$ `Cancelled`**:
   - Status changes to `Cancelled`. Deducted inventory is restored to the respective products.
4. **Invalid Transitions (Rejected with HTTP 400)**:
   - Repeated confirmation: An already `Confirmed` order cannot be confirmed again (prevents duplicate stock deductions).
   - Confirming a cancelled order: A `Cancelled` order cannot be confirmed.
   - Repeated cancellation: A `Cancelled` order cannot be cancelled again (prevents duplicate stock restorations).

### Stock Deduction & Restoral Rules
- **At creation**: Stock is **not** reserved or deducted while in `Draft`.
- **At confirmation**: Stock is deducted immediately.
- **At cancellation**: If previously `Confirmed`, stock is restored. If in `Draft`, stock is untouched.

### Atomic All-or-Nothing Confirmation
If an order contains multiple product lines and **even one** product lacks sufficient inventory or fails validation:
- The confirmation fails completely with HTTP `400 Bad Request`.
- **Zero** stock deductions are made (no partial deduction on any item).
- The order status remains `Draft`.
- Backed by SQLite transaction rollback semantics.

### Duplicate Product Line Decision
**Decision:** Duplicate `product_id` lines in a single order payload are **strictly rejected** with HTTP `422 Unprocessable Content`.

**Rationale:**
In standard e-commerce and inventory ordering systems, repeating the same product across different lines in a single draft order introduces ambiguity (e.g., conflicting notes, unclear pricing/discount targets, or accidental multi-clicks). Enforcing a single line per product with the consolidated total quantity keeps orders clean, predictable, and unambiguous.

---

## Automated Tests

The automated test suite is built with `pytest` and uses an isolated in-memory SQLite database (`sqlite:///:memory:`) for each test run to ensure complete test isolation and zero side-effects.

### Running Tests
Make sure your virtual environment is activated:
```bash
pytest -v
```

### Coverage Highlights
The test suite validates:
1. **Successful Order Confirmation**: Multi-item orders confirmed when stock is sufficient; stock is correctly deducted from each product.
2. **Atomic Rollback on Insufficient Stock**: Confirmation fails when any product line has inadequate stock, verifying **no partial stock deductions** and status remains `Draft`.
3. **Data Validation & Error Handling**:
   - Rejecting unknown `product_id`.
   - Rejecting zero (`0`) or negative quantities.
   - Rejecting negative stock on product creation.
   - Rejecting empty or whitespace-only product names.
   - Rejecting orders with empty items list.
   - Rejecting orders with duplicate product line items.
4. **Stock Restoral on Cancellation**: Cancelling a confirmed order restores inventory to exact previous levels.
5. **Draft Cancellation**: Cancelling a draft order updates status to `Cancelled` without modifying inventory.
6. **State Machine Idempotency & Protection**:
   - Preventing repeated confirmation (stock is not deducted twice).
   - Preventing repeated cancellation (stock is not restored twice).
   - Preventing confirmation of already cancelled orders.
7. **Resource Inspection & 404s**: Correct 404 responses for missing products or orders.

---

## Assumptions & Known Limitations

1. **Pricing and Currency**: As outlined in the project requirements, product prices, discounts, and order totals are not implemented.
2. **Concurrency / Distributed Locks**: SQLite handles database-level locking for transactions. For high-throughput enterprise deployments with multiple application worker processes, transitioning to PostgreSQL with `SELECT ... FOR UPDATE` row-level locks is recommended.
3. **Authentication & Authorization**: No user roles or auth tokens are required as per the prompt specification.
4. **Soft Deletion**: Products and orders are not deleted in this scope.

---

## AI Tools Disclosure

In accordance with the project guidelines:
- **Tools Used**: AI assistant (Antigravity IDE / Gemini 3.8 Flash) was used as a pair-programming partner to scaffold directory layout, generate initial boilerplate schema code, and formulate pytest edge-case matrices.
- **Verification Method**: All generated code was manually inspected, verified against the take-home specification checklist, and rigorously tested using automated pytest suites covering 100% of the functional acceptance criteria.
