from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Greenmile API"
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str = "postgresql+asyncpg://greenmile:greenmile@localhost:5432/greenmile"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    auto_seed_demo: bool = True

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None
    openai_api_version: str = "2024-10-21"
    azure_openai_timeout_seconds: float = 20.0
    azure_openai_max_retries: int = 1

    fuel_price_per_litre: float = 94.77
    vehicle_fuel_efficiency_km_per_l: float = 12.0
    co2_kg_per_litre: float = 2.31
    driver_cost_per_hour: float = 180.0
    average_speed_kmh: float = 28.0
    default_service_time_seconds: int = 300
    max_driver_hours: float = 12.0

    dbscan_eps_km: float = 3.0
    dbscan_min_samples: int = 2
    two_opt_max_iterations: int = 60
    algorithm_version: str = "greenmile-haversine-optimized-v2"
    routing_provider: str = "HAVERSINE"


@lru_cache
def get_settings() -> Settings:
    return Settings()
