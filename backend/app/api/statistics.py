from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends
from numpy import average
from sqlalchemy import select
from app.db.database import get_db
from app.deps import get_current_user
from app.models import Bill, UserSetting


router=APIRouter(prefix="/statistics",tags=["图表"])

"""查询period选定周期的账单
    返回值   periods
            "index":周数,
            "label":显示文字,
            "start_date"datetime:,
            "end_date": datetime        
"""
def query(period,first_date,current_date):
    if(period=="week"):
        start = (
                first_date - timedelta(days=first_date.weekday())
                ).replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0
                        )
        
        current_start= (
            current_date - timedelta(days=current_date.weekday())
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        periods=[]
        index=0
        startC=start
        while startC<=current_start:
            endC=startC+timedelta(days=7)
            index+=1
            if startC==current_start:
                label="本周"
            else:
                label=f"第{index}周"
            periods.append({
                "index":index,
                "label":label,
                "start_date":startC,
                "end_date": endC
            })
            startC=endC

    elif period=="month":
        start = datetime(
                first_date.year,
                first_date.month,
                1
            )

        current_start = datetime(
            current_date.year,
            current_date.month,
            1
        )
        periods=[]
        index=0
        startC=start
        while startC<=current_start:
            if startC.month==12:
                endC=datetime(startC.year+1,1,1)
            else:
                endC=datetime(startC.year,startC.month+1,1)
            if startC==current_start:
                label="本月"
            elif startC.year==current_start.year:
                label=f"{startC.month}月"
            else:
                label=f"{startC.year}年-{startC.month}月"
            periods.append({
                "index":index,
                "label":label,
                "start_date":startC,
                "end_date": endC
            })
            startC=endC

    elif period=="year":
        start = datetime(
                first_date.year,
                1,
                1
            )

        current_start = datetime(
            current_date.year,
            1,
            1
        )
        periods=[]
        index=0
        startC=start
        while startC<=current_start:
            endC=datetime(startC.year+1,1,1)

            if startC==current_start:
                label="今年"
            else:
                label=f"{startC.year}年"
            periods.append({
                "index":index,
                "label":label,
                "start_date":startC,
                "end_date": endC
            })
            startC=endC       
    return periods

"""计算账单 总共 平均 
折线图显示值
{
        "total": f"{total:.2f}",
        "average": f"{average:.2f}",
        "days": days,
        "trend": trend,
        "ranking": ranking
    }

trend[
    {
    "date": "2026-08-03",
    "label": "08-03",
    "amount": "82.20"
    }]

排行榜
"ranking": [
    {
        "category": "餐饮",
        "amount": "154.84",
        "percentage": "55.2"
    }]"""
def calculate(bills,period,start_date,end_date,current_date):
    trend=[]
    total = Decimal("0.00")
    trend_totals = defaultdict(lambda: Decimal("0.00"))
    category_totals = defaultdict(lambda: Decimal("0.00"))

    for bill in bills:
        total +=bill.amount
        if period == "year":
            trend_key = bill.bill_date.strftime("%Y-%m")
        else:
            trend_key = bill.bill_date.strftime("%Y-%m-%d")
        trend_totals[trend_key] += bill.amount 
        category_totals[bill.category]+=bill.amount

    current_end=current_date + timedelta(days=1)
    actual_end=min(end_date,current_end)
    days = (actual_end - start_date).days
    if days <= 0:
        days = 1
    average = total / Decimal(str(days))

    if period in ("week", "month"):
        current = start_date

        while current < actual_end:
            key = current.strftime("%Y-%m-%d")

            trend.append({
                "date": key,
                "label": current.strftime("%m-%d"),
                "amount": f"{trend_totals[key]:.2f}"
            })

            current += timedelta(days=1)

    elif period == "year":
        current = start_date

        while current < actual_end:
            key = current.strftime("%Y-%m")

            trend.append({
                "date": key,
                "label": f"{current.month}月",
                "amount": f"{trend_totals[key]:.2f}"
            })

            if current.month == 12:
                current = current.replace(
                    year=current.year + 1,
                    month=1
                )
            else:
                current = current.replace(
                    month=current.month + 1
                )
    ranking = []

    for category, category_amount in category_totals.items():
        percentage = category_amount / total * Decimal("100")

        ranking.append({
            "category": category,
            "amount": f"{category_amount:.2f}",
            "percentage": f"{percentage:.1f}"
        })

    ranking.sort(
        key=lambda item: Decimal(item["amount"]),
        reverse=True
    )

    return {
        "total": f"{total:.2f}",
        "average": f"{average:.2f}",
        "days": days,
        "trend": trend,
        "ranking": ranking
    }



@router.get("")
async def statistics(
    type:str,
    period:str,
    date:str,
    ledger_id:int|None=None,
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    result=await db.execute(select(UserSetting).where(UserSetting.user_id==user.id))
    setting=result.scalar()
    if setting is None:
        return
    ledger_id=setting.last_ledger_id

    current_date=datetime.strptime(date,"%Y-%m-%d")

    result=await db.execute(select(Bill).where(
        Bill.ledger_id==ledger_id,
        Bill.user_id==user.id
    ).order_by(Bill.bill_date.asc()).limit(1))
    first_bill=result.scalar()
    if first_bill is None:
        return
    
    periods=query(period,first_bill.bill_date,current_date)
    for item in periods:
        result=await db.execute(select(Bill).where( Bill.user_id == user.id,
                                                    Bill.ledger_id == ledger_id,
                                                    Bill.type == type,
                                                    Bill.bill_date>=item["start_date"],
                                                    Bill.bill_date<item["end_date"]))
        bills=result.scalars().all()
        if bills==None:
            break
        data = calculate(
        bills,
        period,
        item["start_date"],
        item["end_date"],
        current_date
    )
        item.update(data)
    return {
    "type": type,
    "period": period,
    "current_index": periods[-1]["index"],
    "items": periods
}   
