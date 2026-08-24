import json
import logging
from functools import lru_cache

from kafka import KafkaProducer
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Thin wrapper around kafka-python's KafkaProducer.

    The connection to the broker is established lazily on first use so that
    importing this module (e.g. during unit tests) never requires a live
    Kafka cluster. Publish failures are logged and swallowed by default so
    that a Kafka outage never takes down the write path of the API - this
    mirrors the "best effort" event publishing pattern used elsewhere in
    this codebase.
    """

    def __init__(self, bootstrap_servers: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._producer: KafkaProducer | None = None

    def _get_producer(self) -> KafkaProducer:
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                retries=3,
                linger_ms=10,
            )
        return self._producer

    def publish(self, topic: str, payload: BaseModel, key: str | None = None) -> bool:
        try:
            producer = self._get_producer()
            future = producer.send(topic, key=key, value=payload.model_dump(mode="json"))
            future.get(timeout=5)
            return True
        except Exception:
            logger.exception("Failed to publish event to topic %s", topic)
            return False

    def close(self) -> None:
        if self._producer is not None:
            self._producer.flush()
            self._producer.close()
            self._producer = None


@lru_cache
def get_event_publisher() -> EventPublisher:
    settings = get_settings()
    return EventPublisher(bootstrap_servers=settings.kafka_bootstrap_servers)
