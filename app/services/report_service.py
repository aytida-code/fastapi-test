from datetime import UTC, datetime, timedelta
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order
from app.schemas.report import MonthlyOrderStatusTotal

load_dotenv('.env_0afcde1f6be381c2', override=True)


def monthly_order_status_totals(db: Session) -> list[MonthlyOrderStatusTotal]:
    cutoff = datetime.now(UTC) - timedelta(days=30)
    rows = (
        db.query(
            Order.status,
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total_amount), 0).label("total_amount"),
        )
        .filter(Order.created_at >= cutoff)
        .group_by(Order.status)
        .order_by(Order.status)
        .all()
    )
    return [
        MonthlyOrderStatusTotal(
            status=status,
            order_count=order_count,
            total_amount=Decimal(str(total_amount)),
        )
        for status, order_count, total_amount in rows
    ]
