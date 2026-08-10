from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.db.database import get_db
from app.deps import get_current_user
from app.models import Ledger, UserSetting


router=APIRouter(prefix="/ledgers",tags=["查找账本"])

@router.get("")
async def getLedger(
    db=Depends(get_db),
    user=Depends(get_current_user)):

    result1=await db.execute(select(UserSetting).where(UserSetting.user_id==user.id))
    setting1=result1.scalar_one_or_none()
    ledger_id=setting1.last_ledger_id

    items=[]
    result=await db.execute(select(Ledger).where(Ledger.user_id==user.id))
    setting=result.scalars().all()
    for l in setting:
        items.append({"id": l.id, "name": l.name, "icon": l.icon, "color": l.color, "sort": l.sort})

    return {"current_ledger_id":ledger_id,"items":items}