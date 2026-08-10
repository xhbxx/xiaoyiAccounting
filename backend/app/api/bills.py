from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.db.database import get_db
from app.deps import get_current_user
from app.models import Bill, User, UserSetting
from app.schemas import BillRespond,NewBill


router=APIRouter(prefix="/bills",tags=["账单"])

@router.post("")
async def bills(
    amount:Decimal,
    type:str,
    category:str,
    bill_date:str,
    remark:str|None=None,
    db=Depends(get_db),
    user=Depends(get_current_user)   
):
    if amount<0:
        raise  HTTPException(status_code=400,detail="金额必须大于0")

    item=NewBill(id=user.id
                ,type=type
                ,amount=str(amount)
                ,bill_date=bill_date
                ,category=category          
                ,remark=remark)

    date = datetime.strptime(bill_date, "%Y-%m-%d")

    result=await db.execute(select(UserSetting).where(UserSetting.user_id==user.id))
    setting=result.scalar()

    dbitem=Bill(user_id=user.id
            ,ledger_id=setting.last_ledger_id
            ,type=type
            ,amount=amount
            ,bill_date=date
            ,category=category          
            ,remark=remark)
    db.add(dbitem)
    await db.commit()
    await db.refresh(dbitem)
    
    respond=BillRespond(id=user.id
                        ,message="记账成功"
                        ,bill=item)
    return respond

@router.put("/{bill_id}")
async def changeBill(
        bill_id:int,
        amount:Decimal,
        type:str,
        category:str,
        bill_date:str,
        remark:str|None=None,
        db=Depends(get_db),
        user=Depends(get_current_user)
):
    date = datetime.strptime(bill_date, "%Y-%m-%d")
    
    result=await db.execute(select(Bill).where(Bill.id==bill_id))
    bill=result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="账单不存在")
    bill.amount=amount
    bill.type=type
    bill.bill_date=date
    bill.category=category
    bill.remark=remark
    await db.commit()
    await db.refresh(bill)
    return {"message":"账单已更新"}

@router.delete("/{bill_id}")
async def deleteBill(
    bill_id:int,
    db=Depends(get_db),
    user=Depends(get_current_user)
):
    result=await db.execute(select(Bill).where(Bill.id==bill_id))
    bill=result.scalar_one_or_none()

    if not bill:
        raise HTTPException(status_code=404, detail="账单不存在")
    if bill.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权删除")
    await db.delete(bill)
    await db.commit()
    return {"message": "删除成功"}
