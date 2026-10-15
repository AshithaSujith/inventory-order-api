import pytest


@pytest.fixture
def sample_products(client):
    """Fixture providing standard products for order tests."""
    p1 = client.post("/products", json={"name": "Smartphone", "stock_quantity": 10}).json()
    p2 = client.post("/products", json={"name": "Headphones", "stock_quantity": 5}).json()
    p3 = client.post("/products", json={"name": "Power Bank", "stock_quantity": 2}).json()
    return {"p1": p1, "p2": p2, "p3": p3}


# =============================================================================
# Requirement 1: Creating an order and confirming it when stock is sufficient
# =============================================================================
def test_create_and_confirm_order_when_stock_is_sufficient(client, sample_products):
    """
    Test creating an order with multiple items and confirming it when stock is sufficient.
    Stock should be deducted from all ordered products.
    """
    p1_id = sample_products["p1"]["id"]
    p2_id = sample_products["p2"]["id"]

    # 1. Create order
    create_resp = client.post(
        "/orders",
        json={
            "items": [
                {"product_id": p1_id, "quantity": 3},
                {"product_id": p2_id, "quantity": 2},
            ]
        },
    )
    assert create_resp.status_code == 201
    order = create_resp.json()
    order_id = order["id"]
    assert order["status"] == "Draft"
    assert len(order["items"]) == 2

    # Verify stock has NOT yet been deducted while in Draft
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 10
    assert client.get(f"/products/{p2_id}").json()["stock_quantity"] == 5

    # 2. Confirm order
    confirm_resp = client.post(f"/orders/{order_id}/confirm")
    assert confirm_resp.status_code == 200
    confirmed_order = confirm_resp.json()
    assert confirmed_order["status"] == "Confirmed"

    # 3. Verify stock is correctly deducted
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 7  # 10 - 3
    assert client.get(f"/products/{p2_id}").json()["stock_quantity"] == 3  # 5 - 2


# =============================================================================
# Requirement 2: Confirmation failing when stock is insufficient, no partial changes
# =============================================================================
def test_confirmation_fails_when_stock_insufficient_no_partial_deductions(client, sample_products):
    """
    Test that if ANY product line cannot be fulfilled due to lack of stock:
    - Confirmation fails with appropriate error (400 Bad Request).
    - Order status remains Draft.
    - NO partial stock deductions occur on other items.
    """
    p1_id = sample_products["p1"]["id"]  # stock: 10
    p3_id = sample_products["p3"]["id"]  # stock: 2

    # Create order requesting 4 of p1 (available: 10) and 5 of p3 (available: 2 - INSUFFICIENT!)
    create_resp = client.post(
        "/orders",
        json={
            "items": [
                {"product_id": p1_id, "quantity": 4},
                {"product_id": p3_id, "quantity": 5},
            ]
        },
    )
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]

    # Attempt to confirm order
    confirm_resp = client.post(f"/orders/{order_id}/confirm")
    assert confirm_resp.status_code == 400
    err_body = confirm_resp.json()
    assert "Insufficient" in err_body["error"] or "insufficient" in err_body["detail"].lower()

    # Crucial check: Order status MUST remain Draft
    order_check = client.get(f"/orders/{order_id}").json()
    assert order_check["status"] == "Draft"

    # Crucial check: NO partial deduction on p1 or p3
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 10
    assert client.get(f"/products/{p3_id}").json()["stock_quantity"] == 2


# =============================================================================
# Requirement 3: Rejecting invalid quantities or unknown products
# =============================================================================
def test_reject_zero_or_negative_quantity_in_order(client, sample_products):
    """Reject orders containing items with zero or negative quantities."""
    p1_id = sample_products["p1"]["id"]

    # Zero quantity
    resp_zero = client.post(
        "/orders",
        json={"items": [{"product_id": p1_id, "quantity": 0}]},
    )
    assert resp_zero.status_code == 422

    # Negative quantity
    resp_neg = client.post(
        "/orders",
        json={"items": [{"product_id": p1_id, "quantity": -3}]},
    )
    assert resp_neg.status_code == 422


def test_reject_unknown_product_in_order(client):
    """Reject order creation referencing a non-existent product ID."""
    resp = client.post(
        "/orders",
        json={"items": [{"product_id": 999999, "quantity": 1}]},
    )
    assert resp.status_code in (400, 404)
    err = resp.json()
    assert "not exist" in err["detail"].lower() or "not found" in err["detail"].lower()


def test_reject_order_with_empty_items(client):
    """Reject order creation with no items."""
    resp = client.post("/orders", json={"items": []})
    assert resp.status_code == 422


def test_reject_duplicate_product_lines_in_order(client, sample_products):
    """Reject order containing duplicate lines for the same product."""
    p1_id = sample_products["p1"]["id"]
    resp = client.post(
        "/orders",
        json={
            "items": [
                {"product_id": p1_id, "quantity": 2},
                {"product_id": p1_id, "quantity": 3},
            ]
        },
    )
    assert resp.status_code == 422
    err_text = str(resp.json())
    assert "Duplicate product" in err_text


# =============================================================================
# Requirement 4: Cancelling a confirmed order and restoring stock
# =============================================================================
def test_cancel_confirmed_order_restores_stock(client, sample_products):
    """
    Cancelling a Confirmed order must restore its stock back to the original quantities.
    """
    p1_id = sample_products["p1"]["id"]  # initial: 10
    p2_id = sample_products["p2"]["id"]  # initial: 5

    # Create and confirm
    order = client.post(
        "/orders",
        json={
            "items": [
                {"product_id": p1_id, "quantity": 4},
                {"product_id": p2_id, "quantity": 3},
            ]
        },
    ).json()
    order_id = order["id"]

    client.post(f"/orders/{order_id}/confirm")
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 6
    assert client.get(f"/products/{p2_id}").json()["stock_quantity"] == 2

    # Cancel confirmed order
    cancel_resp = client.post(f"/orders/{order_id}/cancel")
    assert cancel_resp.status_code == 200
    cancelled_order = cancel_resp.json()
    assert cancelled_order["status"] == "Cancelled"

    # Stock must be fully restored!
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 10
    assert client.get(f"/products/{p2_id}").json()["stock_quantity"] == 5


def test_cancel_draft_order_without_changing_stock(client, sample_products):
    """
    Cancelling a Draft order marks it Cancelled without modifying stock.
    """
    p1_id = sample_products["p1"]["id"]  # stock: 10
    order = client.post(
        "/orders",
        json={"items": [{"product_id": p1_id, "quantity": 4}]},
    ).json()
    order_id = order["id"]

    # Cancel draft order
    cancel_resp = client.post(f"/orders/{order_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "Cancelled"

    # Stock should remain untouched at 10
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 10


# =============================================================================
# Requirement 5: Preventing repeated confirmation or cancellation from applying changes twice
# =============================================================================
def test_prevent_repeated_confirmation(client, sample_products):
    """
    Prevent an order from being confirmed more than once, avoiding double deduction.
    """
    p1_id = sample_products["p1"]["id"]  # stock: 10
    order = client.post(
        "/orders",
        json={"items": [{"product_id": p1_id, "quantity": 2}]},
    ).json()
    order_id = order["id"]

    # First confirmation succeeds
    resp1 = client.post(f"/orders/{order_id}/confirm")
    assert resp1.status_code == 200
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 8

    # Second confirmation MUST FAIL
    resp2 = client.post(f"/orders/{order_id}/confirm")
    assert resp2.status_code == 400
    assert "already confirmed" in resp2.json()["detail"].lower()

    # Stock must NOT be deducted again (still 8, not 6)
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 8


def test_prevent_repeated_cancellation(client, sample_products):
    """
    A Cancelled order cannot be cancelled again; stock must not be restored twice.
    """
    p1_id = sample_products["p1"]["id"]  # stock: 10
    order = client.post(
        "/orders",
        json={"items": [{"product_id": p1_id, "quantity": 3}]},
    ).json()
    order_id = order["id"]

    # Confirm order -> stock becomes 7
    client.post(f"/orders/{order_id}/confirm")
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 7

    # Cancel confirmed order -> stock restored to 10
    resp_cancel1 = client.post(f"/orders/{order_id}/cancel")
    assert resp_cancel1.status_code == 200
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 10

    # Second cancellation MUST FAIL
    resp_cancel2 = client.post(f"/orders/{order_id}/cancel")
    assert resp_cancel2.status_code == 400
    assert "already cancelled" in resp_cancel2.json()["detail"].lower()

    # Stock must NOT be restored again (still 10, not 13)
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 10


def test_prevent_confirmation_after_cancellation(client, sample_products):
    """
    Prevent an order from being confirmed after it has been cancelled.
    """
    p1_id = sample_products["p1"]["id"]  # stock: 10
    order = client.post(
        "/orders",
        json={"items": [{"product_id": p1_id, "quantity": 2}]},
    ).json()
    order_id = order["id"]

    # Cancel draft order
    client.post(f"/orders/{order_id}/cancel")
    assert client.get(f"/orders/{order_id}").json()["status"] == "Cancelled"

    # Try to confirm cancelled order -> must fail
    confirm_resp = client.post(f"/orders/{order_id}/confirm")
    assert confirm_resp.status_code == 400
    assert "cancelled" in confirm_resp.json()["detail"].lower()

    # Stock unaffected
    assert client.get(f"/products/{p1_id}").json()["stock_quantity"] == 10


def test_view_order_details_and_items(client, sample_products):
    """Test retrieving order by ID with line items and current status."""
    p1_id = sample_products["p1"]["id"]
    order = client.post(
        "/orders",
        json={"items": [{"product_id": p1_id, "quantity": 2}]},
    ).json()
    order_id = order["id"]

    resp = client.get(f"/orders/{order_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == order_id
    assert data["status"] == "Draft"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == p1_id
    assert data["items"][0]["product_name"] == "Smartphone"
    assert data["items"][0]["quantity"] == 2


def test_get_nonexistent_order_returns_404(client):
    """Retrieving a non-existent order returns 404."""
    resp = client.get("/orders/99999")
    assert resp.status_code == 404
