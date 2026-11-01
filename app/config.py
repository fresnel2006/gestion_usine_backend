from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration lue dans backend/.env (voir .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173"
    seuil_stock_faible: int = 5

    @property
    def database_url_sqlalchemy(self) -> str:
        """Certains hébergeurs fournissent postgres://, que SQLAlchemy 2 refuse."""
        if self.database_url.startswith("postgres://"):
            return "postgresql://" + self.database_url[len("postgres://"):]
        return self.database_url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
