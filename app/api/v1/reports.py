from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.report import MonthlyOrderStatusTotal
from app.services import report_service

load_dotenv('.env_0afcde1f6be381c2', override=True)

router = APIRouter()


@router.get("/monthly", response_model=list[MonthlyOrderStatusTotal])
def get_monthly_order_report(
    db: Session = Depends(get_db),
) -> list[MonthlyOrderStatusTotal]:
    return report_service.monthly_order_status_totals(db)
