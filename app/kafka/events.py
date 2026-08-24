from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemPayload(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderCreatedEvent(BaseModel):
    event_type: str = "order.created"
    order_id: int
    user_id: int
    items: list[OrderItemPayload]
    total_amount: Decimal
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrderStatusUpdatedEvent(BaseModel):
    event_type: str = "order.status_updated"
    order_id: int
    previous_status: str
    new_status: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
