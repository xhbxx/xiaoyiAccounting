from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.db.database import get_db
from app.deps import get_current_user
from app.models import Bill, UserSetting


router=APIRouter(prefix="/statistics",tags=["图表"])

def query_week(period,first_date,current_date):
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
            else:
                label=f"{startC.month}月"
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
    
    query_week(period,first_bill.bill_date,current_date)


if __name__ == "__main__":
    first_date = datetime(2026, 8, 13)
    current_date = datetime(2026, 8, 27)

    result = query_week(
        "year",
        first_date,
        current_date
    )

    for item in result:
        print(item)