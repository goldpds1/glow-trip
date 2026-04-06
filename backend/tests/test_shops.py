"""Shop API tests."""


def test_list_shops(client, shop, customer_headers):
    res = client.get("/api/shops", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1
    assert len(data["shops"]) >= 1
    assert data["shops"][0]["name"] == "Test Spa"


def test_list_shops_includes_min_price_and_review_count(client, shop, menu, customer_headers):
    res = client.get("/api/shops", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    s = data["shops"][0]
    assert "min_price" in s
    assert s["min_price"] == 50000
    assert "review_count" in s
    assert s["review_count"] == 0


def test_list_shops_search(client, shop, customer_headers):
    res = client.get("/api/shops?keyword=Spa", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1

    res2 = client.get("/api/shops?keyword=nonexistent", headers=customer_headers)
    data2 = res2.get_json()
    assert data2["total"] == 0


def test_list_shops_category_filter(client, app, owner, customer_headers):
    from app import db as _db
    from app.models import Shop
    with app.app_context():
        s = Shop(
            owner_id=owner.id, name="Waxing Place", address="Seoul",
            category="waxing", is_active=True,
        )
        _db.session.add(s)
        _db.session.commit()

    res = client.get("/api/shops?category=waxing", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] == 1
    assert data["shops"][0]["category"] == "waxing"

    res2 = client.get("/api/shops?category=body", headers=customer_headers)
    data2 = res2.get_json()
    assert data2["total"] == 0


def test_list_shops_sort_popular(client, shop, customer_headers):
    res = client.get("/api/shops?sort=popular", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1


def test_shop_detail(client, shop, menu, customer_headers):
    res = client.get(f"/api/shops/{shop.id}", headers=customer_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "Test Spa"
    assert len(data["menus"]) == 1
    assert data["menus"][0]["title"] == "Basic Facial"
    assert "avg_rating" in data
    assert "review_count" in data
    assert "category" in data


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
