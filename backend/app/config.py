"""
Professional AI - Configuration Management
Environment-based configuration with validation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    # Application
    APP_NAME: str = "Professional AI"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    FRONTEND_URL: str = "https://professionalai.com"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/professional_ai"
    DB_SSL_MODE: str = "prefer"

    # Redis Cache
    REDIS_ENABLED: bool = True
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_DEFAULT_TTL: int = 300  # 5 minutes
    CACHE_AI_TTL: int = 3600  # 1 hour for AI responses

    # Security
    SECRET_KEY: str = "change-me-in-production-use-strong-secret"
    JWT_SECRET: str = "change-me-in-production-use-strong-secret"
    JWT_ALGORITHM: str = "HS256"
    ENCRYPTION_KEY: str = "change-me-in-production-use-strong-secret"
    INTERNAL_WORKER_SECRET: str = "change-this-internal-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CSRF_SECRET_KEY: str = "change-me-in-production"
    SESSION_TIMEOUT_MINUTES: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    ENABLE_2FA_ENFORCEMENT: bool = False
    ENABLE_ACCOUNT_LOCKOUT: bool = True
    HTTPS_ONLY: bool = False
    WAF_ENABLED: bool = True
    ENABLE_CSP: bool = True
    ENABLE_PASSKEYS: bool = True

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100

    # AI Providers
    AI_PROVIDER: str = "auto"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_KEYS: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROQ_KEYS: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_KEYS: Optional[str] = None
    AI_PROVIDER_TIMEOUT: float = 20.0  # 20s timeout per provider call
    AI_PROVIDER_RETRIES: int = 3       # 3 retries before falling back
    AI_PROVIDER_RETRY_BACKOFF: float = 1.0
    AI_FAILOVER_TIMEOUT_SECONDS: float = 2.0
    AI_CONNECTIVITY_CHECK_URL: str = "https://www.google.com/generate_204"
    AI_CONNECTIVITY_CHECK_TIMEOUT: float = 5.0
    GEMINI_CHAT_MODEL: str = "gemini-2.0-flash"
    GEMINI_CODE_MODEL: str = "gemini-2.0-flash"
    GROQ_CHAT_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_CODE_MODEL: str = "llama-3.3-70b-versatile"
    OPENROUTER_CHAT_MODEL: str = "deepseek/deepseek-chat"
    OPENROUTER_CODE_MODEL: str = "qwen/qwen2.5-coder-32b-instruct"
    AI_CACHE_ENABLED: bool = True
    AI_CACHE_TTL_SECONDS: int = 3600  # 1 hour
    AI_STREAMING_ENABLED: bool = True
    AI_MAX_TOKENS_CHAT: int = 1024
    AI_MAX_TOKENS_CODE: int = 2048

    # Vault settings
    VAULT_TIMEOUT_SECONDS: float = 20.0
    VAULT_QUEUE_MAX_SECONDS: int = 5
    VAULT_HEALTH_CHECK_INTERVAL_SECONDS: int = 60
    VAULT_KEY_REFRESH_REMINDER_DAYS: int = 7
    VAULT_LOG_ENABLED: bool = True

    # Local fallback
    LOCAL_FALLBACK_ENABLED: bool = True
    LOCAL_MODELS_DIR: str = "./data/local_models"
    LOCAL_CHAT_MODEL: str = "local-chat"
    LOCAL_CODE_MODEL: str = "local-code"
    OLLAMA_ENABLED: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Media Engine
    MEDIA_ENGINE_ENABLED: bool = True
    MEDIA_GPU_WORKERS: int = 4  # Parallel GPU workers
    MEDIA_QUEUE_CONCURRENCY: int = 10
    MEDIA_QUEUE_MAX_WORKERS: int = 4
    MEDIA_OUTPUT_DIR: str = "./data/media_output"
    MEDIA_DEFAULT_RESOLUTION: str = "1080p"
    MEDIA_MAX_SCENES: int = 20
    MEDIA_SCRIPT_LANGUAGES: str = "en,ur,hi,ar,es,fr,de"
    MEDIA_SUBTITLE_VERIFY_ENABLED: bool = True
    MEDIA_UPSCALER_ENABLED: bool = False
    MEDIA_VOICE_CLONE_MAX_SECONDS: int = 60
    MEDIA_VOICE_STYLES: str = "professional,casual,news,storytelling"
    MEDIA_FREE_ANIMATION_LIMIT: int = 3
    MEDIA_FREE_DURATIONS: str = "10,30,60"
    MEDIA_FREE_PICTURE_LIMIT: int = 10
    MEDIA_FREE_VIDEO_LIMIT: int = 5
    MEDIA_PAID_ANIMATION_LIMIT: int = -1
    MEDIA_PAID_DURATIONS: str = "10,30,60,120,300"
    MEDIA_PAID_PICTURE_LIMIT: int = -1
    MEDIA_PAID_VIDEO_LIMIT: int = -1

    # Auto Editor
    AUTO_EDITOR_ENABLED: bool = False
    AUTO_EDITOR_REQUIRES_PRO: bool = True
    AUTO_EDITOR_MAX_CLIPS: int = 10
    AUTO_EDITOR_MAX_DURATION_SECONDS: int = 600
    AUTO_EDITOR_MAX_UPLOAD_SIZE_MB: int = 500
    AUTO_EDITOR_SCENE_SCORE_THRESHOLD: float = 0.7
    AUTO_EDITOR_KEN_BURNS_INTENSITY: float = 0.5
    AUTO_EDITOR_TRANSITION_DURATION_MS: int = 500
    AUTO_EDITOR_STABILIZE_ENABLED: bool = True
    AUTO_EDITOR_COLOR_GRADE_PRESET: str = "cinematic"
    AUTO_EDITOR_WHISPER_MODEL: str = "tiny"
    AUTO_EDITOR_WHISPER_DEVICE: str = "cpu"
    AUTO_EDITOR_WHISPER_COMPUTE_TYPE: str = "int8"
    AUTO_EDITOR_BG_MUSIC_DIR: str = "./data/auto_editor/music"
    AUTO_EDITOR_INTRO_OUTRO_PATH: str = "./data/auto_editor/intro_outro"
    AUTO_EDITOR_OUTPUT_DIR: str = "./data/auto_editor/output"
    AUTO_EDITOR_TEMP_DIR: str = "./data/auto_editor/temp"
    ANIMATEDIFF_MODEL: str = "animatediff"

    # Monitoring
    METRICS_AUTH_ENABLED: bool = True
    METRICS_USERNAME: str = "admin"
    METRICS_PASSWORD: str = "change-me-in-production"
    SENTRY_DSN: Optional[str] = None

    # Unlimited Mode
    UNLIMITED_MODE_ENABLED: bool = True
    UNLIMITED_PLANS: str = "pro,pro_yearly,max,business,enterprise,trial"
    FREE_CODE_LIMIT_PER_DAY: int = 3
    FREE_CHAT_LIMIT_PER_DAY: int = 50
    ACCURACY_DOUBLE_CHECK_ENABLED: bool = True
    PRIORITY_PROVIDER_ORDER: str = "groq,gemini,openrouter,ollama,local"

    # Frontend
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_CDN_URL: str = "https://cdn.professional-ai.com"

    # Compression
    ENABLE_GZIP: bool = True
    ENABLE_BROTLI: bool = True

    # Email & Alerts
    ALERT_EMAIL_TO: str = ""
    ALERT_ON_BRUTE_FORCE: bool = True
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # AI Provider URLs
    FAL_AI_API_KEY: Optional[str] = None
    FAL_AI_API_URL: str = "https://queue.fal.run"
    REPLICATE_API_KEY: Optional[str] = None
    REPLICATE_API_URL: str = "https://api.replicate.com/v1"
    KLING_API_KEY: Optional[str] = None
    KLING_API_URL: str = "https://api.klingai.com"
    RUNWAY_API_KEY: Optional[str] = None
    RUNWAY_API_URL: str = "https://api.dev.runwayml.com/v1"
    SEARXNG_URL: str = "http://localhost:8888"
    WHISPER_API_URL: str = "http://localhost:8001"
    TTS_API_URL: str = "http://localhost:8002"
    COMFYUI_URL: str = "http://localhost:8188"
    GOOGLE_CLOUD_STORAGE_BUCKET: str = ""

    # Payments
    STRIPE_GATEWAY_ACTIVE: bool = False
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PAYOUT_CURRENCY: str = "USD"
    PAYPAL_GATEWAY_ACTIVE: bool = False
    WISE_GATEWAY_ACTIVE: bool = False
    PAYONEER_GATEWAY_ACTIVE: bool = False
    SKRILL_GATEWAY_ACTIVE: bool = False
    BINANCE_PAY_GATEWAY_ACTIVE: bool = False
    JAZZCASH_GATEWAY_ACTIVE: bool = False
    EASYPAISA_GATEWAY_ACTIVE: bool = False
    SADAPAY_GATEWAY_ACTIVE: bool = False
    NAYAPAY_GATEWAY_ACTIVE: bool = False

    # Banking
    ALLIED_BANK_ACCOUNT_NAME: str = ""
    ALLIED_BANK_ACCOUNT_NUMBER: str = ""
    ALLIED_BANK_IBAN: str = ""
    ALLIED_BANK_SWIFT: str = ""
    ALLIED_BANK_BRANCH: str = ""
    PAYONEER_AUTO_SETTLEMENT_TO_ALLIED: bool = False
    SKRILL_AUTO_SETTLEMENT_TO_ALLIED: bool = False
    WISE_AUTO_SETTLEMENT_TO_ALLIED: bool = False

    # Exchange Rates
    EXCHANGE_RATE_API_URL: str = "https://api.exchangerate.host/latest"
    EXCHANGE_RATE_API_KEY: str = ""

    # Geo / Compliance
    ISRAEL_GEO_BLOCK: str = "IL"
    ALLOWED_COUNTRIES: str = "ALL"
    ALLOWED_UPLOAD_EXTENSIONS: str = ".pdf,.docx,.txt,.png,.jpg,.jpeg,.gif"

    # OAuth
    APPLE_CLIENT_ID: str = ""
    APPLE_CLIENT_SECRET: str = ""
    FACEBOOK_CLIENT_ID: str = ""
    FACEBOOK_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""

    # Owner
    OWNER_EMAIL: str = ""
    OWNER_EMAILS: str = ""
    OWNER_SETUP_KEY: str = "change-this-owner-setup-key"
    OWNER_ENFORCE_PASSKEY: bool = False
    OWNER_ENFORCE_TOTP: bool = False

    # SMS & Voice
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    REAL_ESRGAN_API_URL: str = ""
    REAL_ESRGAN_SCALE: int = 4

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def is_owner_email(self, email: Optional[str]) -> bool:
        """True when the email matches OWNER_EMAIL configured in environment."""
        if not email:
            return False
        target = email.strip().lower()

        owner_emails = set()
        if self.OWNER_EMAIL:
            owner_emails.add(self.OWNER_EMAIL.strip().lower())

        if self.OWNER_EMAILS:
            owner_emails.update(
                value.strip().lower()
                for value in self.OWNER_EMAILS.split(",")
                if value and value.strip()
            )

        if not owner_emails:
            return False

        return target in owner_emails


# Global settings instance
settings = Settings()
