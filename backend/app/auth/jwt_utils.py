from datetime import datetime, timezone, timedelta

import jwt
from flask import current_app


def create_token(user_id: str, token_type: str = "access") -> str:
    if token_type == "refresh":
        expires = current_app.config["JWT_REFRESH_EXPIRES"]
    else:
        expires = current_app.config["JWT_ACCESS_EXPIRES"]

    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET"],
        algorithms=["HS256"],
    )


def create_tokens(user_id: str) -> dict:
    return {
        "access_token": create_token(user_id, "access"),
        "refresh_token": create_token(user_id, "refresh"),
    }
