from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AgentConnect AI"
    database_url: str = "postgresql+psycopg://agentconnect:agentconnect@localhost:5432/agentconnect"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    gemini_model: str = "gemini-1.5-flash"
    jwt_secret: str = "change-this-to-a-long-random-secret"
    jwt_expire_minutes: int = 1440
    match_threshold: float = 0.55
    max_matches: int = 5
    webhook_timeout_seconds: int = 8
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
