from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://anarisuto:anarisuto@localhost:5432/anarisuto"

    llm_mode: str = "gemini"  # gemini|stub
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    cors_origins: str = "http://localhost:5173"

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
