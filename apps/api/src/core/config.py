from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Hyderabad Hangama Club"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: SecretStr = Field(default="dev-secret-key-change-in-production")

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://hangama:hangama_secret@127.0.0.1:5432/hangama",
        description="PostgreSQL URL (Supabase connection string in production)",
    )
    DATABASE_SSL: bool = Field(
        default=True,
        description="Use SSL for PostgreSQL (disable only for local Docker Postgres)",
    )
    DB_POOL_SIZE: int = Field(default=5, ge=1, le=20)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DB_USE_NULL_POOL: bool = Field(
        default=False,
        description="Use NullPool for Supabase transaction pooler (port 6543)",
    )

    REDIS_URL: str = ""

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: SecretStr = Field(default="")
    RAZORPAY_WEBHOOK_SECRET: SecretStr = Field(default="")

    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = ""
    EMAIL_FROM_NAME: str = "Hyderabad Hangama Club"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    AISENSY_API_KEY: str = ""
    AISENSY_CAMPAIGN_NAME: str = "ticket_confirmation"

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: SecretStr = Field(default="")
    SUPABASE_STORAGE_BUCKET: str = "payment-screenshots"

    API_BASE_URL: str = ""

    CORS_ORIGINS: str = Field(
        default="http://127.0.0.1:3000,http://localhost:3000",
        description="Comma-separated allowed browser origins",
    )

    PAYMENT_MODE: str = Field(default="UPI_MANUAL")
    UPI_ID: str = Field(default="")
    UPI_MERCHANT_NAME: str = Field(default="Hyderabad Hangama Club")

    ADMIN_API_KEY: str = Field(default="changeme")
    ADMIN_WHATSAPP_NUMBER: str = ""
    ADMIN_EMAIL: str = ""
    ADMIN_AISENSY_CAMPAIGN_NAME_ADMIN: str = "admin_payment_alert"
    ADMIN_DASHBOARD_URL: str = ""

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://") and "+asyncpg" not in value:
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @model_validator(mode="after")
    def apply_pooler_defaults(self) -> "Settings":
        """Auto-enable NullPool for Supabase transaction pooler (port 6543)."""
        if self.DB_USE_NULL_POOL:
            return self
        try:
            parsed = urlparse(self.DATABASE_URL)
            host = (parsed.hostname or "").lower()
            if parsed.port == 6543 or "pooler.supabase.com" in host:
                return self.model_copy(update={"DB_USE_NULL_POOL": True})
        except Exception:
            pass
        return self

    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    def supabase_configured(self) -> bool:
        return bool(
            self.SUPABASE_URL.strip()
            and self.SUPABASE_SERVICE_ROLE_KEY.get_secret_value().strip()
        )

    def supabase_url_normalized(self) -> str:
        return self.SUPABASE_URL.rstrip("/")

    def database_requires_ssl(self) -> bool:
        if not self.DATABASE_SSL:
            return False
        host = (urlparse(self.DATABASE_URL).hostname or "").lower()
        if host in ("127.0.0.1", "localhost", "db"):
            return False
        return True

    def cors_origins_list(self) -> list[str]:
        raw = self.CORS_ORIGINS.strip()
        if not raw or raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    def validate_production(self) -> list[str]:
        """Return list of configuration errors for production startup."""
        errors: list[str] = []
        if not self.is_production():
            return errors

        if self.ADMIN_API_KEY in ("changeme", ""):
            errors.append("ADMIN_API_KEY must be set to a strong secret in production")

        if not self.API_BASE_URL.strip():
            errors.append("API_BASE_URL is required in production (public HTTPS API URL)")

        origins = self.cors_origins_list()
        if origins == ["*"]:
            errors.append("CORS_ORIGINS must list your Vercel frontend URL(s) in production")

        if not self.supabase_configured():
            errors.append(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required in production"
            )

        if not self.DATABASE_URL.strip():
            errors.append("DATABASE_URL is required in production")

        return errors

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
