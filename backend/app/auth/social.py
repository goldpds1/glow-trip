"""소셜 로그인 — 클라이언트에서 받은 ID 토큰/코드를 검증하고 유저를 생성·로그인한다."""

import requests
import jwt as pyjwt
from flask import Blueprint, request, jsonify, current_app

from app import db
from app.models import User
from app.auth.jwt_utils import create_tokens

social_bp = Blueprint("social", __name__, url_prefix="/api/auth/social")


def _find_or_create_user(email, provider, provider_id, name=None, language="en"):
    """provider+provider_id로 유저를 찾거나, 없으면 생성."""
    user = User.query.filter_by(auth_provider=provider, provider_id=provider_id).first()
    if user:
        return user

    # 같은 이메일로 이미 가입된 경우 (다른 provider)
    user = User.query.filter_by(email=email).first()
    if user:
        return user

    user = User(
        email=email,
        auth_provider=provider,
        provider_id=provider_id,
        name=name,
        language=language,
        role="customer",
    )
    db.session.add(user)
    db.session.commit()
    return user


# ── Google ────────────────────────────────────────────────
@social_bp.route("/google", methods=["POST"])
def google_login():
    """클라이언트에서 Google ID Token을 받아 검증."""
    data = request.get_json() or {}
    id_token = data.get("id_token", "")
    if not id_token:
        return jsonify(error="id_token is required"), 400

    # Google 공개키로 토큰 검증
    resp = requests.get(
        "https://oauth2.googleapis.com/tokeninfo",
        params={"id_token": id_token},
        timeout=5,
    )
    if resp.status_code != 200:
        return jsonify(error="Invalid Google token"), 401

    info = resp.json()
    client_id = current_app.config["GOOGLE_CLIENT_ID"]
    if client_id and info.get("aud") != client_id:
        return jsonify(error="Token audience mismatch"), 401

    user = _find_or_create_user(
        email=info["email"],
        provider="google",
        provider_id=info["sub"],
        name=info.get("name"),
        language=data.get("language", "en"),
    )
    tokens = create_tokens(user.id)
    return jsonify(user_id=str(user.id), **tokens), 200


# ── Apple ─────────────────────────────────────────────────
@social_bp.route("/apple", methods=["POST"])
def apple_login():
    """클라이언트에서 Apple ID Token을 받아 검증."""
    data = request.get_json() or {}
    id_token = data.get("id_token", "")
    if not id_token:
        return jsonify(error="id_token is required"), 400

    # Apple 공개키 가져오기
    keys_resp = requests.get("https://appleid.apple.com/auth/keys", timeout=5)
    if keys_resp.status_code != 200:
        return jsonify(error="Failed to fetch Apple keys"), 502

    try:
        header = pyjwt.get_unverified_header(id_token)
        jwk_set = keys_resp.json()
        key = None
        for k in jwk_set.get("keys", []):
            if k["kid"] == header["kid"]:
                key = pyjwt.algorithms.RSAAlgorithm.from_jwk(k)
                break

        if not key:
            return jsonify(error="Apple key not found"), 401

        payload = pyjwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=current_app.config["APPLE_CLIENT_ID"] or None,
            issuer="https://appleid.apple.com",
        )
    except pyjwt.InvalidTokenError:
        return jsonify(error="Invalid Apple token"), 401

    email = payload.get("email", "")
    if not email:
        return jsonify(error="Email not provided by Apple"), 400

    user = _find_or_create_user(
        email=email,
        provider="apple",
        provider_id=payload["sub"],
        name=data.get("name"),
        language=data.get("language", "en"),
    )
    tokens = create_tokens(user.id)
    return jsonify(user_id=str(user.id), **tokens), 200


# ── LINE ──────────────────────────────────────────────────
@social_bp.route("/line", methods=["POST"])
def line_login():
    """클라이언트에서 LINE access_token을 받아 프로필 조회."""
    data = request.get_json() or {}
    access_token = data.get("access_token", "")
    if not access_token:
        return jsonify(error="access_token is required"), 400

    # LINE 토큰으로 프로필 조회
    resp = requests.get(
        "https://api.line.me/v2/profile",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=5,
    )
    if resp.status_code != 200:
        return jsonify(error="Invalid LINE token"), 401

    profile = resp.json()
    line_user_id = profile.get("userId", "")

    # LINE은 이메일을 기본 제공하지 않으므로 placeholder 사용
    email = data.get("email") or f"{line_user_id}@line.placeholder"

    user = _find_or_create_user(
        email=email,
        provider="line",
        provider_id=line_user_id,
        name=profile.get("displayName"),
        language=data.get("language", "ja"),
    )
    tokens = create_tokens(user.id)
    return jsonify(user_id=str(user.id), **tokens), 200
