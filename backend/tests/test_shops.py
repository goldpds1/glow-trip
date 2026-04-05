"""Shop API tests."""


def test_list_shops(client, shop, customer_headers):
    res = client.get("/api/shops", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1
    assert len(data["shops"]) >= 1
    assert data["shops"][0]["name"] == "Test Spa"


def test_list_shops_search(client, shop, customer_headers):
    res = client.get("/api/shops?keyword=Spa", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1

    res2 = client.get("/api/shops?keyword=nonexistent", headers=customer_headers)
    data2 = res2.get_json()
    assert data2["total"] == 0


def test_shop_detail(client, shop, menu, customer_headers):
    res = client.get(f"/api/shops/{shop.id}", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "Test Spa"
    assert len(data["menus"]) == 1
    assert data["menus"][0]["title"] == "Basic Facial"


def test_shop_detail_not_found(client, customer_headers):
    import uuid
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/shops/{fake_id}", headers=customer_headers)
    assert res.status_code == 404


def test_shop_menus(client, shop, menu, customer_headers):
    res = client.get(f"/api/shops/{shop.id}/menus", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["menus"]) == 1
    assert data["menus"][0]["price"] == 50000
    assert data["menus"][0]["duration"] == 60
