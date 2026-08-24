from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_name: str = "brownfield-order-service"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "mysql+pymysql://orders_user:orders_password@localhost:3306/orders_db"

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_order_created: str = "order.created"
    kafka_topic_order_status_updated: str = "order.status_updated"
    kafka_consumer_group: str = "order-service-consumer"


@lru_cache
def get_settings() -> Settings:
    return Settings()
