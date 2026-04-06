import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://glowtrip:glowtrip@localhost:5432/glowtrip",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET = os.environ.get("JWT_SECRET", SECRET_KEY)
    JWT_ACCESS_EXPIRES = int(os.environ.get("JWT_ACCESS_EXPIRES", 3600))  # 1h
    JWT_REFRESH_EXPIRES = int(os.environ.get("JWT_REFRESH_EXPIRES", 604800))  # 7d

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    APPLE_CLIENT_ID = os.environ.get("APPLE_CLIENT_ID", "")
    LINE_CHANNEL_ID = os.environ.get("LINE_CHANNEL_ID", "")
    LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    PLATFORM_FEE_RATE = float(os.environ.get("PLATFORM_FEE_RATE", "0.1"))  # 10%

    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@glowtrip.com")
    SENDGRID_FROM_NAME = os.environ.get("SENDGRID_FROM_NAME", "Glow Trip")
    FCM_SERVER_KEY = os.environ.get("FCM_SERVER_KEY", "")
    NOTIFICATION_REMINDER_HOURS = int(os.environ.get("NOTIFICATION_REMINDER_HOURS", "24"))


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://glowtrip:glowtrip@localhost:5433/glowtrip_test",
    )
    JWT_SECRET = "test-secret-key"
    SECRET_KEY = "test-secret-key"
