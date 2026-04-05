"""Phase 9: Image upload API tests."""

import io


def test_upload_image(client, customer_headers):
    data = {
        "file": (io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100), "test.png"),
    }
    res = client.post("/api/upload", data=data, content_type="multipart/form-data",
                      headers=customer_headers)
    assert res.status_code == 201
    body = res.get_json()
    assert body["url"].startswith("/api/uploads/")
    assert body["url"].endswith(".png")


def test_upload_no_file(client, customer_headers):
    res = client.post("/api/upload", data={}, content_type="multipart/form-data",
                      headers=customer_headers)
    assert res.status_code == 400


def test_upload_invalid_type(client, customer_headers):
    data = {
        "file": (io.BytesIO(b"not an image"), "test.txt"),
    }
    res = client.post("/api/upload", data=data, content_type="multipart/form-data",
                      headers=customer_headers)
    assert res.status_code == 400


def test_upload_no_auth(client):
    data = {
        "file": (io.BytesIO(b"\x89PNG\r\n\x1a\n"), "test.png"),
    }
    res = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 401


def test_serve_uploaded_file(client, customer_headers):
    data = {
        "file": (io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50), "serve.png"),
    }
    upload_res = client.post("/api/upload", data=data, content_type="multipart/form-data",
                             headers=customer_headers)
    url = upload_res.get_json()["url"]

    serve_res = client.get(url)
    assert serve_res.status_code == 200


def test_shop_update_with_image(client, owner_headers, shop):
    res = client.patch(f"/api/owner/shops/{shop.id}", json={
        "image_url": "/api/uploads/test.png",
    }, headers=owner_headers)
    assert res.status_code == 200
    assert res.get_json()["image_url"] == "/api/uploads/test.png"


def test_menu_create_with_image(client, owner_headers, shop):
    res = client.post(f"/api/owner/shops/{shop.id}/menus", json={
        "title": "With Image",
        "price": 30000,
        "duration": 45,
        "image_url": "/api/uploads/menu.png",
    }, headers=owner_headers)
    assert res.status_code == 201
    assert res.get_json()["image_url"] == "/api/uploads/menu.png"
