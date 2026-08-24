from decimal import Decimal

from dotenv import load_dotenv
from pydantic import BaseModel

from app.models.order import OrderStatus

load_dotenv('.env_0afcde1f6be381c2', override=True)


class MonthlyOrderStatusTotal(BaseModel):
    status: OrderStatus
    order_count: int
    total_amount: Decimal
