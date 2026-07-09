from pydantic_settings import BaseSettings
from pydantic import ConfigDict, computed_field
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "RoofTop Solar Energy Marketplace"
    app_version: str = "1.0.0"
    debug: bool = True
    allowed_origins: str = "http://localhost:3000"

    # Database credentials
    database_username: str
    database_password: str

    # Database endpoints
    database_host: str
    database_port: int = 5432
    database_name: str
    database_schema: str = "public"
    database_read_host: str | None = None

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
        """Build database URL for write operations (primary instance)"""
        return f"postgresql://{self.database_username}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}?sslmode=require&options=-csearch_path%3D{self.database_schema}"

    @computed_field
    @property
    def db_read_url(self) -> str | None:
        """Build database URL for read operations (replica instances)"""
        if not self.database_read_host:
            return None
        return f"postgresql://{self.database_username}:{self.database_password}@{self.database_read_host}:{self.database_port}/{self.database_name}?sslmode=require&options=-csearch_path%3D{self.database_schema}"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    model_config = ConfigDict(env_file=".env", case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    return Settings()

