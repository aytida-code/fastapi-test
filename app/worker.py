import logging

from app.core.logging import configure_logging
from app.kafka.consumer import OrderEventConsumer


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting order-service Kafka worker")
    consumer = OrderEventConsumer()
    consumer.run_forever()


if __name__ == "__main__":
    main()
