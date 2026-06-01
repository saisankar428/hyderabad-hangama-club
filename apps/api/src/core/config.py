from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Hyderabad Hangama Club"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: SecretStr = Field(default="dev-secret-key-change-in-production")

    DATABASE_URL: str = "postgresql+asyncpg://hangama:hangama_secret@db:5432/hangama"
    REDIS_URL: str = "redis://localhost:6379/0"

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: SecretStr = Field(default="")
    RAZORPAY_WEBHOOK_SECRET: SecretStr = Field(default="")

    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "no-reply@hyderabadhangamaclub.com"
    EMAIL_FROM_NAME: str = "Hyderabad Hangama Club"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    AISENSY_API_KEY: str = ""
    AISENSY_CAMPAIGN_NAME: str = "ticket_confirmation"

    API_BASE_URL: str = ""

    # Comma-separated browser origins (your Vercel URL). Use * only for local dev.
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Allowed CORS origins, comma-separated",
    )

    # Payment mode: "RAZORPAY" (online checkout) or "UPI_MANUAL" (QR + admin approval)
    PAYMENT_MODE: str = Field(default="UPI_MANUAL")
    UPI_ID: str = Field(default="")
    UPI_MERCHANT_NAME: str = Field(default="Hyderabad Hangama Club")

    ADMIN_API_KEY: str = Field(default="changeme", description="Admin API key for protected routes")

    ADMIN_WHATSAPP_NUMBER: str = Field(default="", description="Admin WhatsApp number for payment alerts (10-digit or E.164)")
    ADMIN_EMAIL: str = Field(default="", description="Admin email address for payment notification emails")
    ADMIN_AISENSY_CAMPAIGN_NAME_ADMIN: str = Field(default="admin_payment_alert", description="AiSensy campaign for admin payment notifications")
    ADMIN_DASHBOARD_URL: str = Field(default="", description="Admin dashboard URL included in notifications")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Render/Railway often provide postgres:// — SQLAlchemy async needs asyncpg."""
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return value.replace("postgres://", "postgresql+asyncpg://", 1)
            if value.startswith("postgresql://") and "+asyncpg" not in value:
                return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
