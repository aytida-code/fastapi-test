from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.kafka.events import OrderCreatedEvent, OrderItemPayload, OrderStatusUpdatedEvent
from app.kafka.producer import EventPublisher
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderStatusUpdate


class ProductNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    pass


_ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


def create_order(db: Session, event_publisher: EventPublisher, order_in: OrderCreate) -> Order:
    order = Order(user_id=order_in.user_id, status=OrderStatus.PENDING, total_amount=Decimal("0"))
    total = Decimal("0")

    for item_in in order_in.items:
        product = db.get(Product, item_in.product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {item_in.product_id} does not exist")
        if product.stock_quantity < item_in.quantity:
            raise InsufficientStockError(
                f"Product {product.sku} only has {product.stock_quantity} units in stock"
            )

        unit_price = Decimal(str(product.price))
        total += unit_price * item_in.quantity
        order.items.append(
            OrderItem(product_id=product.id, quantity=item_in.quantity, unit_price=unit_price)
        )

    order.total_amount = total
    db.add(order)
    db.commit()
    db.refresh(order)

    # Stock is decremented asynchronously once the inventory worker consumes
    # this event (see app/services/inventory_service.py). See the "Known
    # limitations" section in the README for the tradeoff this implies.
    event = OrderCreatedEvent(
        order_id=order.id,
        user_id=order.user_id,
        items=[
            OrderItemPayload(product_id=i.product_id, quantity=i.quantity, unit_price=i.unit_price)
            for i in order.items
        ],
        total_amount=order.total_amount,
    )
    settings = get_settings()
    event_publisher.publish(settings.kafka_topic_order_created, event, key=str(order.id))

    return order


def get_order(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id)


def list_orders(db: Session, user_id: int | None = None, skip: int = 0, limit: int = 100) -> list[Order]:
    query = db.query(Order)
    if user_id is not None:
        query = query.filter(Order.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def update_order_status(
    db: Session,
    event_publisher: EventPublisher,
    order: Order,
    status_in: OrderStatusUpdate,
) -> Order:
    allowed = _ALLOWED_TRANSITIONS.get(order.status, set())
    if status_in.status not in allowed:
        raise InvalidStatusTransitionError(
            f"Cannot transition order from {order.status.value} to {status_in.status.value}"
        )

    previous_status = order.status
    order.status = status_in.status
    db.add(order)
    db.commit()
    db.refresh(order)

    event = OrderStatusUpdatedEvent(
        order_id=order.id,
        previous_status=previous_status.value,
        new_status=order.status.value,
    )
    settings = get_settings()
    event_publisher.publish(settings.kafka_topic_order_status_updated, event, key=str(order.id))

    return order
