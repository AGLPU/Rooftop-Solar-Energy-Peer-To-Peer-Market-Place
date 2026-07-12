from pydantic_settings import BaseSettings
from pydantic import ConfigDict, computed_field
from functools import lru_cache
import os


class Settings(BaseSettings):
    # App
    app_name: str = "RoofTop Solar Energy Marketplace"
    app_version: str = "1.0.0"
    debug: bool = True
    allowed_origins: str = "http://localhost:3000"

    # Database credentials (AWS RDS style)
    database_username: str | None = None
    database_password: str | None = None
    database_host: str | None = None
    database_port: int = 5432
    database_name: str | None = None
    database_schema: str = "public"
    database_read_host: str | None = None

    # Railway style — DATABASE_URL takes priority if set
    database_url: str | None = None

    # SSL mode — "require" for AWS RDS, "disable" for Railway/local
    database_sslmode: str = "require"

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Blockchain (optional)
    blockchain_enabled: bool = False
    blockchain_rpc_url: str | None = None
    blockchain_network: str | None = None
    blockchain_contract_address: str | None = None
    blockchain_private_key: str | None = None

    @computed_field
    @property
    def db_url(self) -> str:
        """
        Build database URL for write operations.
        Priority:
          1. DATABASE_URL  (Railway injects this automatically)
          2. DATABASE_HOST + DATABASE_USERNAME + ... (AWS RDS style)
        """
        if self.database_url:
            # Railway provides postgresql://user:pass@host:port/db
            # Ensure it uses postgresql:// not postgres://
            return self.database_url.replace("postgres://", "postgresql://", 1)

        if not self.database_host:
            raise ValueError(
                "No database configuration found. "
                "Set DATABASE_URL (Railway) or DATABASE_HOST + DATABASE_USERNAME + ... (AWS RDS)"
            )

        ssl = f"sslmode={self.database_sslmode}" if self.database_sslmode != "disable" else ""
        schema = f"options=-csearch_path%3D{self.database_schema}" if self.database_schema != "public" else ""
        params = "&".join(filter(None, [ssl, schema]))
        qs = f"?{params}" if params else ""

        return (
            f"postgresql://{self.database_username}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}{qs}"
        )

    @computed_field
    @property
    def db_read_url(self) -> str | None:
        """Build database URL for read operations (replica). Falls back to primary if not set."""
        if self.database_url:
            return None  # Railway doesn't have separate read replica on free tier

        if not self.database_read_host:
            return None

        ssl = f"sslmode={self.database_sslmode}" if self.database_sslmode != "disable" else ""
        schema = f"options=-csearch_path%3D{self.database_schema}" if self.database_schema != "public" else ""
        params = "&".join(filter(None, [ssl, schema]))
        qs = f"?{params}" if params else ""

        return (
            f"postgresql://{self.database_username}:{self.database_password}"
            f"@{self.database_read_host}:{self.database_port}/{self.database_name}{qs}"
        )

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    model_config = ConfigDict(env_file=".env", case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    return Settings()

