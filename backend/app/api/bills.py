from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import select

from app.db.database import get_db
from app.deps import get_current_user, get_user_ledger
from app.models import Bill
from app.schemas import BillWrite

router = APIRouter(prefix="/bills", tags=["账单"])


async def read_bill_input(request: Request):
    # 新版页面发送 JSON，保留旧版调用方的查询参数格式。
    try:
        data = dict(request.query_params)
        if request.headers.get("content-type", "").startswith("application/json"):
            data = await request.json()
        return BillWrite.model_validate(data)
    except (ValidationError, ValueError) as error:
        detail = "账单参数不合法"
        if isinstance(error, ValidationError):
            first = error.errors()[0]
            field = first["loc"][0] if first["loc"] else ""
            detail = {
                "amount": "金额必须大于 0，最多两位小数且不超过 9999999999.99",
                "type": "账单类型必须为 expense 或 income",
                "category": "请选择分类，长度不超过 64 字",
                "bill_date": "账单日期格式必须为 YYYY-MM-DD 或 YYYY-MM-DD HH:mm:ss",
                "remark": "备注不能超过 256 字",
                "ledger_id": "账本 ID 必须为正整数",
            }.get(field, detail)
        raise HTTPException(status_code=400, detail=detail)


def bill_response(bill):
    return {
        "id": bill.id,
        "ledger_id": bill.ledger_id,
        "type": bill.type,
        "amount": f"{bill.amount:.2f}",
        "bill_date": bill.bill_date.strftime("%Y-%m-%d %H:%M:%S"),
        "category": bill.category,
        "remark": bill.remark,
    }


@router.post("", status_code=201)
async def bills(
    item: BillWrite = Depends(read_bill_input),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    ledger = await get_user_ledger(db, user, item.ledger_id)
    values = item.model_dump(exclude={"ledger_id"})
    bill = Bill(user_id=user.id, ledger_id=ledger.id, **values)
    db.add(bill)
    await db.commit()
    await db.refresh(bill)
    return {"id": bill.id, "message": "记账成功", "bill": bill_response(bill)}


@router.put("/{bill_id}")
async def changeBill(
    bill_id: int,
    item: BillWrite = Depends(read_bill_input),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(select(Bill).where(
        Bill.id == bill_id, Bill.user_id == user.id
    ))
    bill = result.scalar_one_or_none()
    if bill is None:
        raise HTTPException(status_code=404, detail="账单不存在")
    # 旧调用方省略账本时，编辑仍保留原账本。
    ledger_id = item.ledger_id if item.ledger_id is not None else bill.ledger_id
    ledger = await get_user_ledger(db, user, ledger_id)
    for field, value in item.model_dump(exclude={"ledger_id"}).items():
        setattr(bill, field, value)
    bill.ledger_id = ledger.id
    await db.commit()
    await db.refresh(bill)
    return {"message": "账单已更新", "bill": bill_response(bill)}


@router.delete("/{bill_id}")
async def deleteBill(bill_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Bill).where(
        Bill.id == bill_id, Bill.user_id == user.id
    ))
    bill = result.scalar_one_or_none()
    if bill is None:
        raise HTTPException(status_code=404, detail="账单不存在")
    await db.delete(bill)
    await db.commit()
    return {"message": "账单已删除"}
