

from datetime import datetime

from fastapi import APIRouter, Depends
from app.deps import get_current_user
from sqlalchemy import select

from app.db.database import get_db
from app.models import Bill, Ledger, UserSetting
from app.schemas import HomeResponse, LedgerInfo, PeriodInfo, BillGroup, BillItem

router = APIRouter(tags=["首页"])

@router.get("/home")
async def home(
    year:int,
    month:int,
    ledger_id:int|None=None,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    if ledger_id is None:
        result = await db.execute(select(UserSetting).where(UserSetting.user_id == current_user.id))
        setting = result.scalar()
        ledger_id= setting.last_ledger_id 

    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

    result = await db.execute(
        select(Bill).where(
            Bill.user_id == current_user.id,
            Bill.ledger_id == ledger_id,
            Bill.bill_date >= start,
            Bill.bill_date < end,
        ).order_by(Bill.bill_date.desc())
    )
    bills = result.scalars().all()

    start = datetime(year, month, 1)
    if month == 12:
        end =datetime(year + 1, 1, 1)
    else:
        end= datetime(year, month + 1, 1)

    result = await db.execute(
        select(Bill).where(
            Bill.user_id == current_user.id,
            Bill.ledger_id == ledger_id,
            Bill.bill_date >= start,
            Bill.bill_date < end,
        ).order_by(Bill.bill_date.desc())
    )
    bills = result.scalars().all() 

    income=0
    outcome=0
    for b in bills:
        if b.type=="income":
            income=income+b.amout
        else:
            outcome=outcome+b.amout

    groups_dict = {}                         
    for b in bills:                           
        date_str = b.bill_date.strftime("%Y-%m-%d")   
        groups_dict.setdefault(date_str, []).append(b)  

    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    groups = []
    for date_str, day_bills in groups_dict.items():
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        day_income = 0
        day_expense = 0
        for b in day_bills:
            if b.type == "income":
                day_income = day_income + b.amount
            elif b.type == "expense":
                day_expense = day_expense + b.amount

        items = []
        for b in day_bills:
            if b.type == "expense":
                amount_text = f"-{b.amount:.2f}"
            else:
                amount_text = f"+{b.amount:.2f}"
            item = BillItem(
                id=b.id,
                type=b.type,
                amount=f"{b.amount:.2f}",
                amount_text=amount_text,
                category=b.category or "",
                icon=None,
                remark=b.remark,
                bill_date=date_str,
            )
            items.append(item)

        groups.append(BillGroup(
            date=date_str,
            date_text=date_obj.strftime("%m月%d日"),
            week=weekdays[date_obj.weekday()],
            expense_total=f"{day_expense:.2f}",
            income_total=f"{day_income:.2f}",
            items=items,
        ))