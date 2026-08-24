def _create_user(client):
    return client.post(
        "/api/v1/users",
        json={"email": "reports@example.com", "full_name": "Reports User", "password": "supersecret123"},
    ).json()


def _create_product(client):
    return client.post(
        "/api/v1/products",
        json={"sku": "REPORT-100", "name": "Report Product", "price": "10.00", "stock_quantity": 10},
    ).json()


def test_monthly_report_groups_orders_by_status(client):
    user = _create_user(client)
    product = _create_product(client)
    first_order = client.post(
        "/api/v1/orders",
        json={"user_id": user["id"], "items": [{"product_id": product["id"], "quantity": 1}]},
    ).json()
    second_order = client.post(
        "/api/v1/orders",
        json={"user_id": user["id"], "items": [{"product_id": product["id"], "quantity": 2}]},
    ).json()
    client.patch(f"/api/v1/orders/{second_order['id']}/status", json={"status": "confirmed"})

    response = client.get("/api/v1/reports/monthly")

    assert response.status_code == 200
    totals = {row["status"]: row for row in response.json()}
    assert totals["pending"] == {"status": "pending", "order_count": 1, "total_amount": "10.00"}
    assert totals["confirmed"] == {"status": "confirmed", "order_count": 1, "total_amount": "20.00"}
