"""Tests for social login endpoints."""

from unittest.mock import patch, MagicMock
import json


# ── Helper: mock Google tokeninfo response ─────────────
def _mock_google_ok(sub="google-uid-123", email="guser@gmail.com", name="Google User"):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "sub": sub,
        "email": email,
        "name": name,
        "aud": "test-google-client-id",
    }
    return resp


def _mock_google_fail():
    resp = MagicMock()
    resp.status_code = 401
    resp.json.return_value = {"error": "invalid_token"}
    return resp


# ── Helper: mock LINE profile response ─────────────────
def _mock_line_profile_ok(user_id="line-uid-456", name="LINE User"):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"userId": user_id, "displayName": name}
    return resp


def _mock_line_token_ok(access_token="line-access-token-xyz"):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"access_token": access_token}
    return resp


def _mock_fail(status=401):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"error": "failed"}
    return resp


# ════════════════════════════════════════════════════════
# Config API
# ════════════════════════════════════════════════════════

class TestSocialConfig:
    def test_social_config_returns_client_ids(self, client, app):
        app.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"
        app.config["APPLE_CLIENT_ID"] = "test-apple-client-id"
        app.config["LINE_CHANNEL_ID"] = "test-line-channel-id"

        res = client.get("/api/config/social")
        assert res.status_code == 200
        data = res.get_json()
        assert data["google_client_id"] == "test-google-client-id"
        assert data["apple_client_id"] == "test-apple-client-id"
        assert data["line_channel_id"] == "test-line-channel-id"

    def test_social_config_empty_when_not_set(self, client, app):
        app.config["GOOGLE_CLIENT_ID"] = ""
        app.config["APPLE_CLIENT_ID"] = ""
        app.config["LINE_CHANNEL_ID"] = ""

        res = client.get("/api/config/social")
        assert res.status_code == 200
        data = res.get_json()
        assert data["google_client_id"] == ""


# ════════════════════════════════════════════════════════
# Google Login
# ════════════════════════════════════════════════════════

class TestGoogleLogin:
    def test_google_missing_id_token(self, client):
        res = client.post("/api/auth/social/google", json={})
        assert res.status_code == 400
        assert "id_token" in res.get_json()["error"]

    @patch("app.auth.social.requests.get")
    def test_google_invalid_token(self, mock_get, client):
        mock_get.return_value = _mock_google_fail()
        res = client.post("/api/auth/social/google", json={"id_token": "bad-token"})
        assert res.status_code == 401

    @patch("app.auth.social.requests.get")
    def test_google_valid_token_creates_user(self, mock_get, client, app):
        app.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"
        mock_get.return_value = _mock_google_ok()

        res = client.post("/api/auth/social/google", json={"id_token": "valid-token"})
        assert res.status_code == 200
        data = res.get_json()
        assert "access_token" in data
        assert "user_id" in data

    @patch("app.auth.social.requests.get")
    def test_google_audience_mismatch(self, mock_get, client, app):
        app.config["GOOGLE_CLIENT_ID"] = "different-client-id"
        mock_get.return_value = _mock_google_ok()  # aud = test-google-client-id

        res = client.post("/api/auth/social/google", json={"id_token": "valid-token"})
        assert res.status_code == 401
        assert "audience" in res.get_json()["error"].lower()

    @patch("app.auth.social.requests.get")
    def test_google_returns_existing_user_on_relogin(self, mock_get, client, app):
        app.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"
        mock_get.return_value = _mock_google_ok()

        # First login — creates user
        res1 = client.post("/api/auth/social/google", json={"id_token": "valid-token"})
        uid1 = res1.get_json()["user_id"]

        # Second login — same user
        res2 = client.post("/api/auth/social/google", json={"id_token": "valid-token"})
        uid2 = res2.get_json()["user_id"]

        assert uid1 == uid2


# ════════════════════════════════════════════════════════
# Apple Login
# ════════════════════════════════════════════════════════

class TestAppleLogin:
    def test_apple_missing_id_token(self, client):
        res = client.post("/api/auth/social/apple", json={})
        assert res.status_code == 400
        assert "id_token" in res.get_json()["error"]

    @patch("app.auth.social.requests.get")
    def test_apple_key_fetch_failure(self, mock_get, client):
        mock_get.return_value = _mock_fail(502)
        res = client.post("/api/auth/social/apple", json={"id_token": "some-token"})
        assert res.status_code == 502


# ════════════════════════════════════════════════════════
# LINE Login (access_token)
# ════════════════════════════════════════════════════════

class TestLineLogin:
    def test_line_missing_access_token(self, client):
        res = client.post("/api/auth/social/line", json={})
        assert res.status_code == 400
        assert "access_token" in res.get_json()["error"]

    @patch("app.auth.social.requests.get")
    def test_line_invalid_token(self, mock_get, client):
        mock_get.return_value = _mock_fail()
        res = client.post("/api/auth/social/line", json={"access_token": "bad"})
        assert res.status_code == 401

    @patch("app.auth.social.requests.get")
    def test_line_valid_token_creates_user(self, mock_get, client):
        mock_get.return_value = _mock_line_profile_ok()

        res = client.post("/api/auth/social/line", json={"access_token": "good-token"})
        assert res.status_code == 200
        data = res.get_json()
        assert "access_token" in data
        assert "user_id" in data


# ════════════════════════════════════════════════════════
# LINE Exchange (code → token)
# ════════════════════════════════════════════════════════

class TestLineExchange:
    def test_line_exchange_missing_code(self, client):
        res = client.post("/api/auth/social/line/exchange", json={})
        assert res.status_code == 400
        assert "code" in res.get_json()["error"]

    @patch("app.auth.social.requests.get")
    @patch("app.auth.social.requests.post")
    def test_line_exchange_token_failure(self, mock_post, mock_get, client):
        mock_post.return_value = _mock_fail()
        res = client.post("/api/auth/social/line/exchange", json={
            "code": "auth-code-123",
            "redirect_uri": "http://localhost/",
        })
        assert res.status_code == 401
        assert "exchange" in res.get_json()["error"].lower()

    @patch("app.auth.social.requests.get")
    @patch("app.auth.social.requests.post")
    def test_line_exchange_success(self, mock_post, mock_get, client, app):
        app.config["LINE_CHANNEL_ID"] = "test-line-id"
        app.config["LINE_CHANNEL_SECRET"] = "test-line-secret"

        mock_post.return_value = _mock_line_token_ok()
        mock_get.return_value = _mock_line_profile_ok()

        res = client.post("/api/auth/social/line/exchange", json={
            "code": "auth-code-123",
            "redirect_uri": "http://localhost/",
        })
        assert res.status_code == 200
        data = res.get_json()
        assert "access_token" in data
        assert "user_id" in data

    @patch("app.auth.social.requests.get")
    @patch("app.auth.social.requests.post")
    def test_line_exchange_profile_failure(self, mock_post, mock_get, client, app):
        app.config["LINE_CHANNEL_ID"] = "test-line-id"
        app.config["LINE_CHANNEL_SECRET"] = "test-line-secret"

        mock_post.return_value = _mock_line_token_ok()
        mock_get.return_value = _mock_fail()  # profile fetch fails

        res = client.post("/api/auth/social/line/exchange", json={
            "code": "auth-code-123",
            "redirect_uri": "http://localhost/",
        })
        assert res.status_code == 401


# ════════════════════════════════════════════════════════
# Account Merge
# ════════════════════════════════════════════════════════

class TestAccountMerge:
    @patch("app.auth.social.requests.get")
    def test_email_user_merged_on_google_login(self, mock_get, client, app, customer):
        """Existing email user should have provider updated on social login."""
        app.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"
        mock_get.return_value = _mock_google_ok(
            email=customer.email,
            sub="google-merge-uid",
        )

        res = client.post("/api/auth/social/google", json={"id_token": "valid"})
        assert res.status_code == 200
        assert res.get_json()["user_id"] == str(customer.id)

        # Verify provider was updated
        from app.models import User
        from app import db
        with app.app_context():
            u = User.query.get(customer.id)
            assert u.auth_provider == "google"
            assert u.provider_id == "google-merge-uid"

    @patch("app.auth.social.requests.get")
    def test_social_user_not_overwritten_by_different_social(self, mock_get, client, app):
        """User created via Google should not have provider changed on LINE login."""
        app.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"

        # First: create via Google
        mock_get.return_value = _mock_google_ok(
            email="shared@test.com",
            sub="google-uid-shared",
        )
        res1 = client.post("/api/auth/social/google", json={"id_token": "valid"})
        uid = res1.get_json()["user_id"]

        # Second: LINE login with same email (via placeholder won't match, use explicit email)
        mock_get.return_value = _mock_line_profile_ok(user_id="line-uid-shared")
        res2 = client.post("/api/auth/social/line", json={
            "access_token": "good",
            "email": "shared@test.com",
        })
        assert res2.status_code == 200
        # Should return same user
        assert res2.get_json()["user_id"] == uid

        # Provider should NOT be changed (already google, not email)
        from app.models import User
        with app.app_context():
            u = User.query.get(uid)
            assert u.auth_provider == "google"

    @patch("app.auth.social.requests.get")
    def test_new_social_user_gets_customer_role(self, mock_get, client, app):
        """New user created via social login should have role=customer."""
        app.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"
        mock_get.return_value = _mock_google_ok(email="newuser@social.com")

        res = client.post("/api/auth/social/google", json={"id_token": "valid"})
        uid = res.get_json()["user_id"]

        from app.models import User
        with app.app_context():
            u = User.query.get(uid)
            assert u.role == "customer"
