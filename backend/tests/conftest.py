import pytest
import bcrypt

from app import create_app, db as _db
from app.models import User, Shop, Menu
from app.auth.jwt_utils import create_tokens


import os

TEST_CONFIG = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://glowtrip:glowtrip@localhost:5433/glowtrip_test",
    ),
    "JWT_SECRET": "test-secret-key",
    "SECRET_KEY": "test-secret-key",
}


@pytest.fixture(scope="session")
def app():
    """Create Flask app with test config (once per session)."""
    app = create_app(test_config=TEST_CONFIG)
    yield app


@pytest.fixture(autouse=True)
def setup_db(app):
    """Create all tables before each test, drop after."""
    with app.app_context():
        _db.create_all()
        yield
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Database session."""
    return _db


# ── User Fixtures ───────────────────────────────────────

@pytest.fixture
def customer(app):
    """Create a customer user."""
    with app.app_context():
        user = User(
            email="customer@test.com",
            password_hash=bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode(),
            name="Test Customer",
            role="customer",
            language="en",
            auth_provider="email",
        )
        _db.session.add(user)
        _db.session.commit()
        _db.session.refresh(user)
        return user


@pytest.fixture
def owner(app):
    """Create an owner user."""
    with app.app_context():
        user = User(
            email="owner@test.com",
            password_hash=bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode(),
            name="Test Owner",
            role="owner",
            language="ko",
            auth_provider="email",
        )
        _db.session.add(user)
        _db.session.commit()
        _db.session.refresh(user)
        return user


@pytest.fixture
def admin(app):
    """Create an admin user."""
    with app.app_context():
        user = User(
            email="admin@test.com",
            password_hash=bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode(),
            name="Test Admin",
            role="admin",
            language="ko",
            auth_provider="email",
        )
        _db.session.add(user)
        _db.session.commit()
        _db.session.refresh(user)
        return user


# ── Auth Header Fixtures ────────────────────────────────

@pytest.fixture
def customer_headers(app, customer):
    """Authorization headers for customer."""
    with app.app_context():
        tokens = create_tokens(str(customer.id))
        return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def owner_headers(app, owner):
    """Authorization headers for owner."""
    with app.app_context():
        tokens = create_tokens(str(owner.id))
        return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def admin_headers(app, admin):
    """Authorization headers for admin."""
    with app.app_context():
        tokens = create_tokens(str(admin.id))
        return {"Authorization": f"Bearer {tokens['access_token']}"}


# ── Shop & Menu Fixtures ────────────────────────────────

@pytest.fixture
def shop(app, owner):
    """Create a shop owned by owner."""
    with app.app_context():
        s = Shop(
            owner_id=owner.id,
            name="Test Spa",
            description="A test spa shop",
            address="Seoul, Korea",
            phone="010-1234-5678",
            is_active=True,
        )
        _db.session.add(s)
        _db.session.commit()
        _db.session.refresh(s)
        return s


@pytest.fixture
def menu(app, shop):
    """Create a menu for the shop."""
    with app.app_context():
        m = Menu(
            shop_id=shop.id,
            title="Basic Facial",
            description="60min facial treatment",
            price=50000,
            duration=60,
            is_active=True,
        )
        _db.session.add(m)
        _db.session.commit()
        _db.session.refresh(m)
        return m
