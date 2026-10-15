import pytest


def test_create_product_success(client):
    """Test creating a valid product."""
    response = client.post(
        "/products",
        json={"name": "Wireless Keyboard", "stock_quantity": 25},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Wireless Keyboard"
    assert data["stock_quantity"] == 25
    assert "created_at" in data


def test_create_product_with_zero_stock(client):
    """Zero stock is valid (non-negative)."""
    response = client.post(
        "/products",
        json={"name": "Out of Stock Item", "stock_quantity": 0},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["stock_quantity"] == 0


def test_create_product_negative_stock_rejected(client):
    """Negative stock quantity must be rejected."""
    response = client.post(
        "/products",
        json={"name": "Gaming Mouse", "stock_quantity": -10},
    )
    assert response.status_code == 422


def test_create_product_empty_or_whitespace_name_rejected(client):
    """Blank or whitespace-only names must be rejected."""
    # Blank name
    response = client.post(
        "/products",
        json={"name": "", "stock_quantity": 10},
    )
    assert response.status_code == 422

    # Whitespace-only name
    response = client.post(
        "/products",
        json={"name": "   ", "stock_quantity": 10},
    )
    assert response.status_code == 422


def test_create_product_missing_fields_rejected(client):
    """Missing required fields must return 422."""
    response = client.post("/products", json={"name": "Monitor"})
    assert response.status_code == 422

    response = client.post("/products", json={"stock_quantity": 5})
    assert response.status_code == 422


def test_list_products(client):
    """Test listing all products."""
    client.post("/products", json={"name": "Monitor", "stock_quantity": 15})
    client.post("/products", json={"name": "Desk Mat", "stock_quantity": 30})

    response = client.get("/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 2
    names = [p["name"] for p in products]
    assert "Monitor" in names
    assert "Desk Mat" in names


def test_get_product_by_id(client):
    """Test getting single product by ID."""
    created = client.post("/products", json={"name": "USB Cable", "stock_quantity": 50}).json()
    prod_id = created["id"]

    response = client.get(f"/products/{prod_id}")
    assert response.status_code == 200
    assert response.json()["id"] == prod_id
    assert response.json()["name"] == "USB Cable"


def test_get_nonexistent_product_returns_404(client):
    """Accessing non-existent product returns 404."""
    response = client.get("/products/99999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
