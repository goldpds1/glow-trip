"""Phase 11: Google Maps / distance sort tests."""


def test_maps_key_endpoint(client):
    res = client.get("/api/config/maps-key")
    assert res.status_code == 200
    data = res.get_json()
    assert "key" in data


def test_shops_distance_sort(client, shop):
    """Sort by distance with lat/lng params."""
    res = client.get("/api/shops?lat=37.5665&lng=126.978&sort=distance")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1


def test_shops_distance_with_keyword(client, shop):
    res = client.get(f"/api/shops?keyword=Test&lat=37.5665&lng=126.978&sort=distance")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1


def test_shops_default_sort(client, shop):
    """Default sort (no distance) still works."""
    res = client.get("/api/shops")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1
    # No distance_km field in default sort
    if data["shops"]:
        assert "distance_km" not in data["shops"][0]
