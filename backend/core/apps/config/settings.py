from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "local"
    TELEGRAM_TOKEN: str
    GEMINI_API_KEY: str | None = None

    LLM_PROVIDER: str = "fake"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    SYSTEM_PROMPT: str = "You are a helpful, concise assistant."

    TZ: str = "Asia/Qostanay"
    DAILY_CHAT_ID: int | None = None
    DAILY_CRON: str = "0 9 * * *"

    SESSIONS_BACKEND: str = "memory"  # memory | sqlite
    SQLITE_DSN: str = "./sessions.db"

    EVENTS_CHAT_ID: int | None = None

    class Config:
        env_file = ".env"

    @field_validator("DAILY_CHAT_ID", "EVENTS_CHAT_ID", mode="before")
    @classmethod
    def _empty_to_none_int(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return int(v)

    def __init__(self, **data):
        super().__init__(**data)
        if self.GEMINI_API_KEY and self.LLM_PROVIDER == "fake":
            object.__setattr__(self, "LLM_PROVIDER", "gemini")


settings = Settings()
