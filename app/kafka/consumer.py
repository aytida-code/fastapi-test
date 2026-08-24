import json
import logging

from kafka import KafkaConsumer

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.inventory_service import (
    decrement_stock_for_order,
    restock_for_cancelled_order,
)

logger = logging.getLogger(__name__)


class OrderEventConsumer:
    """Consumes order lifecycle events and keeps inventory in sync.

    Runs as a standalone worker process (see app/worker.py) rather than
    inside the FastAPI process, so the API and the async workers can scale
    independently.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings
        self._consumer = KafkaConsumer(
            settings.kafka_topic_order_created,
            settings.kafka_topic_order_status_updated,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )

    def run_forever(self) -> None:
        logger.info("Order event consumer started, listening for events...")
        for message in self._consumer:
            try:
                self._handle_message(message.topic, message.value)
            except Exception:
                logger.exception("Failed to process message from topic %s", message.topic)

    def _handle_message(self, topic: str, payload: dict) -> None:
        db = SessionLocal()
        try:
            if topic == self._settings.kafka_topic_order_created:
                decrement_stock_for_order(db, payload)
            elif topic == self._settings.kafka_topic_order_status_updated:
                if payload.get("new_status") == "cancelled":
                    restock_for_cancelled_order(db, payload)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
