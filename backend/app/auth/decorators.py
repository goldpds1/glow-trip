from functools import wraps

import jwt as pyjwt
from flask import request, jsonify, g

from app.auth.jwt_utils import decode_token
from app.models import User


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify(error="Missing or invalid token"), 401

        token = header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except pyjwt.ExpiredSignatureError:
            return jsonify(error="Token expired"), 401
        except pyjwt.InvalidTokenError:
            return jsonify(error="Invalid token"), 401

        if payload.get("type") != "access":
            return jsonify(error="Invalid token type"), 401

        user = User.query.get(payload["sub"])
        if not user:
            return jsonify(error="User not found"), 401

        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            if g.current_user.role not in roles:
                return jsonify(error="Forbidden"), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
