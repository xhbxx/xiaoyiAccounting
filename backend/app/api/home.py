from datetime import datetime
from fastapi import APIRouter, Depends, Query
from app.deps import get_current_user, get_user_ledger
from sqlalchemy import select
from app.db.database import get_db
from app.models import Bill, MonthlyBudget, Ledger
from app.schemas import HomeResponse, LedgerInfo, PeriodInfo, BillGroup, BillItem, BudgetWrite

router = APIRouter(tags=["详细"])

@router.get("/home")
async def home(
    year:int = Query(ge=2000, le=2100),
    month:int = Query(ge=1, le=12),
    ledger_id:int|None=None,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    ledger = await get_user_ledger(db, current_user, ledger_id)
    ledger_id = ledger.id

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
        ).order_by(Bill.bill_date.desc(), Bill.id.desc())
    )
    bills = result.scalars().all() 

    income=0
    outcome=0
    for b in bills:
        if b.type=="income":
            income=income+b.amount
        else:
            outcome=outcome+b.amount
            

    groups_dict = {}                         
    for b in bills:                           
        date_str = b.bill_date.strftime("%Y-%m-%d")   
        groups_dict.setdefault(date_str, []).append(b)  

    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期天"]
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
                bill_date=b.bill_date.strftime('%Y-%m-%d %H:%M:%S'),
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

    budget = await db.scalar(select(MonthlyBudget).where(
        MonthlyBudget.ledger_id == ledger_id, MonthlyBudget.year == year, MonthlyBudget.month == month
    ))
    budget_data = None
    if budget is not None:
        remaining = budget.amount - outcome
        budget_data = {'amount': f'{budget.amount:.2f}', 'remaining': f'{remaining:.2f}',
                       'remaining_percent': float(max(0, min(100, remaining / budget.amount * 100)))}
    return HomeResponse(
        ledger=LedgerInfo(id=ledger.id, name=ledger.name, icon=ledger.icon, color=ledger.color),
        period=PeriodInfo(year=year, month=month, income=f"{income:.2f}", expense=f"{outcome:.2f}"),
        groups=groups,
        budget=budget_data,
    )


@router.put('/home/budget')
async def save_budget(item: BudgetWrite, db=Depends(get_db), user=Depends(get_current_user)):
    ledger = await get_user_ledger(db, user, item.ledger_id)
    # 锁定账本，再查询预算，保证同一账本月份只有一条记录。
    await db.execute(select(Ledger.id).where(Ledger.id == ledger.id).with_for_update())
    budget = await db.scalar(select(MonthlyBudget).where(
        MonthlyBudget.ledger_id == ledger.id, MonthlyBudget.year == item.year,
        MonthlyBudget.month == item.month,
    ).with_for_update())
    if budget is None:
        db.add(MonthlyBudget(ledger_id=ledger.id, year=item.year, month=item.month, amount=item.amount))
    else:
        budget.amount = item.amount
    await db.commit()
    return {'message': '月预算已保存'}
