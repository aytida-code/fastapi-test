def _create_user(client):
    return client.post(
        "/api/v1/users",
        json={"email": "buyer@example.com", "full_name": "Buyer One", "password": "supersecret123"},
    ).json()


def _create_product(client, stock=10):
    return client.post(
        "/api/v1/products",
        json={"sku": "SKU-100", "name": "Notebook", "price": "9.99", "stock_quantity": stock},
    ).json()


def test_create_order_publishes_event(client, fake_event_publisher):
    user = _create_user(client)
    product = _create_product(client)

    response = client.post(
        "/api/v1/orders",
        json={"user_id": user["id"], "items": [{"product_id": product["id"], "quantity": 2}]},
    )
    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "pending"
    assert float(order["total_amount"]) == 19.98

    assert len(fake_event_publisher.published) == 1
    topic, event = fake_event_publisher.published[0]
    assert topic == "order.created"
    assert event.order_id == order["id"]


def test_create_order_with_insufficient_stock_fails(client):
    user = _create_user(client)
    product = _create_product(client, stock=1)

    response = client.post(
        "/api/v1/orders",
        json={"user_id": user["id"], "items": [{"product_id": product["id"], "quantity": 5}]},
    )
    assert response.status_code == 422


def test_create_order_with_missing_product_fails(client):
    user = _create_user(client)

    response = client.post(
        "/api/v1/orders",
        json={"user_id": user["id"], "items": [{"product_id": 9999, "quantity": 1}]},
    )
    assert response.status_code == 404


def test_order_status_transition(client):
    user = _create_user(client)
    product = _create_product(client)
    order = client.post(
        "/api/v1/orders",
        json={"user_id": user["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
    ).json()

    confirmed = client.patch(f"/api/v1/orders/{order['id']}/status", json={"status": "confirmed"})
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"

    invalid = client.patch(f"/api/v1/orders/{order['id']}/status", json={"status": "delivered"})
    assert invalid.status_code == 409
