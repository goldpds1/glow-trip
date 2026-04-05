import bcrypt
import jwt as pyjwt
from flask import Blueprint, request, jsonify, g

from app import db
from app.models import User
from app.auth.jwt_utils import create_tokens, decode_token
from app.auth.decorators import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ── 이메일 회원가입 ──────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "").strip()
    language = data.get("language", "en").strip()

    if not email or not password:
        return jsonify(error="Email and password are required"), 400

    if len(password) < 8:
        return jsonify(error="Password must be at least 8 characters"), 400

    if User.query.filter_by(email=email).first():
        return jsonify(error="Email already registered"), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = User(
        email=email,
        password_hash=hashed,
        name=name or None,
        auth_provider="email",
        language=language,
        role="customer",
    )
    db.session.add(user)
    db.session.commit()

    tokens = create_tokens(user.id)
    return jsonify(user_id=str(user.id), **tokens), 201


# ── 이메일 로그인 ────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify(error="Email and password are required"), 400

    user = User.query.filter_by(email=email, auth_provider="email").first()
    if not user or not user.password_hash:
        return jsonify(error="Invalid credentials"), 401

    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return jsonify(error="Invalid credentials"), 401

    tokens = create_tokens(user.id)
    return jsonify(user_id=str(user.id), **tokens), 200


# ── 토큰 갱신 ────────────────────────────────────────────
@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json() or {}
    refresh_token = data.get("refresh_token", "")

    if not refresh_token:
        return jsonify(error="Refresh token is required"), 400

    try:
        payload = decode_token(refresh_token)
    except pyjwt.ExpiredSignatureError:
        return jsonify(error="Refresh token expired"), 401
    except pyjwt.InvalidTokenError:
        return jsonify(error="Invalid refresh token"), 401

    if payload.get("type") != "refresh":
        return jsonify(error="Invalid token type"), 401

    user = User.query.get(payload["sub"])
    if not user:
        return jsonify(error="User not found"), 401

    tokens = create_tokens(user.id)
    return jsonify(user_id=str(user.id), **tokens), 200


# ── 내 정보 조회 ─────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    u = g.current_user
    return jsonify(
        id=str(u.id),
        email=u.email,
        name=u.name,
        role=u.role,
        language=u.language,
        auth_provider=u.auth_provider,
    ), 200
