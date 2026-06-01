from pydantic import BaseSettings, Field, SecretStr


class Settings(BaseSettings):
    APP_NAME: str = "Hyderabad Hangama Club"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: SecretStr

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: SecretStr
    RAZORPAY_WEBHOOK_SECRET: SecretStr

    RESEND_API_KEY: str
    EMAIL_FROM: str
    EMAIL_FROM_NAME: str = "Hyderabad Hangama Club"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    AISENSY_API_KEY: str = ""
    AISENSY_CAMPAIGN_NAME: str = "ticket_confirmation"

    # Public base URL of this API (e.g. https://api.example.com).
    # Required for QR code media attachment in WhatsApp messages.
    API_BASE_URL: str = ""

    ADMIN_API_KEY: str = Field("changeme", description="Admin API key for protected routes")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
