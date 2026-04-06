import os

from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app(test_config=None):
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'frontend')
    frontend_dir = os.path.abspath(frontend_dir)

    app = Flask(
        __name__,
        static_folder=frontend_dir,
        static_url_path='/static',
    )
    app.config.from_object("app.config.Config")

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from app import models  # noqa: F401

    from app.auth.routes import auth_bp
    from app.auth.social import social_bp
    from app.api.shops import shops_bp
    from app.api.bookings import bookings_bp
    from app.api.owner import owner_bp
    from app.api.payments import payments_bp
    from app.api.upload import upload_bp
    from app.api.reviews import reviews_bp
    from app.api.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(shops_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(admin_bp)

    from app.cli import send_reminders_command
    app.cli.add_command(send_reminders_command)

    @app.route("/api/config/maps-key")
    def maps_key():
        key = app.config.get("GOOGLE_MAPS_API_KEY", "")
        return jsonify(key=key), 200

    @app.route("/health")
    def health():
        try:
            db.session.execute(db.text("SELECT 1"))
            return jsonify(status="ok")
        except Exception as e:
            return jsonify(status="error", message=str(e)), 500

    @app.route("/owner")
    def owner_page():
        return send_from_directory(frontend_dir, "owner.html")

    @app.route("/admin")
    def admin_page():
        return send_from_directory(frontend_dir, "admin.html")

    # SPA fallback — all frontend routes serve index.html
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def spa_fallback(path):
        return send_from_directory(frontend_dir, "index.html")

    return app
