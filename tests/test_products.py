def test_create_and_list_products(client):
    response = client.post(
        "/api/v1/products",
        json={
            "sku": "SKU-001",
            "name": "Wireless Mouse",
            "description": "Ergonomic wireless mouse",
            "price": "29.99",
            "stock_quantity": 50,
        },
    )
    assert response.status_code == 201
    product = response.json()
    assert product["stock_quantity"] == 50

    listing = client.get("/api/v1/products")
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_duplicate_sku_rejected(client):
    payload = {"sku": "SKU-DUP", "name": "Widget", "price": "9.99", "stock_quantity": 5}
    first = client.post("/api/v1/products", json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/products", json=payload)
    assert second.status_code == 409


def test_update_product_stock(client):
    created = client.post(
        "/api/v1/products",
        json={"sku": "SKU-002", "name": "Keyboard", "price": "49.99", "stock_quantity": 10},
    ).json()

    updated = client.patch(f"/api/v1/products/{created['id']}", json={"stock_quantity": 25})
    assert updated.status_code == 200
    assert updated.json()["stock_quantity"] == 25
