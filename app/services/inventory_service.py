import logging

from sqlalchemy.orm import Session

from app.models.inventory import InventoryLog
from app.models.order import Order
from app.models.product import Product

logger = logging.getLogger(__name__)


def decrement_stock_for_order(db: Session, event_payload: dict) -> None:
    for item in event_payload.get("items", []):
        product = db.get(Product, item["product_id"])
        if product is None:
            logger.warning(
                "Product %s referenced by order %s no longer exists",
                item["product_id"],
                event_payload.get("order_id"),
            )
            continue

        quantity = item["quantity"]
        product.stock_quantity = max(product.stock_quantity - quantity, 0)
        db.add(
            InventoryLog(
                product_id=product.id,
                change_quantity=-quantity,
                reason=f"order:{event_payload.get('order_id')}:created",
            )
        )


def restock_for_cancelled_order(db: Session, event_payload: dict) -> None:
    order_id = event_payload.get("order_id")
    order = db.get(Order, order_id)
    if order is None:
        logger.warning("Order %s not found while restocking a cancelled order", order_id)
        return

    for item in order.items:
        product = db.get(Product, item.product_id)
        if product is None:
            continue
        product.stock_quantity += item.quantity
        db.add(
            InventoryLog(
                product_id=product.id,
                change_quantity=item.quantity,
                reason=f"order:{order_id}:cancelled",
            )
        )
