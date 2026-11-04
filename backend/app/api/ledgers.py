from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.db.database import get_db
from app.deps import get_current_user, get_user_ledger
from app.models import Ledger, UserSetting
from app.schemas import NameWrite

router = APIRouter(prefix="/ledgers", tags=["账本"])


@router.get('')
async def getLedger(db=Depends(get_db), user=Depends(get_current_user)):
    current = await get_user_ledger(db, user)
    result = await db.execute(select(Ledger).where(Ledger.user_id == user.id)
                              .order_by(Ledger.sort, Ledger.id))
    return {'current_ledger_id': current.id, 'items': [
        {'id': item.id, 'name': item.name, 'icon': item.icon, 'color': item.color, 'sort': item.sort}
        for item in result.scalars()
    ]}


@router.post('', status_code=201)
async def create_ledger(item: NameWrite, db=Depends(get_db), user=Depends(get_current_user)):
    ledger = Ledger(user_id=user.id, name=item.name)
    db.add(ledger)
    await db.commit()
    await db.refresh(ledger)
    return {'id': ledger.id, 'name': ledger.name}


@router.put('/{ledger_id}')
async def rename_ledger(ledger_id: int, item: NameWrite, db=Depends(get_db), user=Depends(get_current_user)):
    ledger = await get_user_ledger(db, user, ledger_id)
    ledger.name = item.name
    await db.commit()
    return {'id': ledger.id, 'name': ledger.name}


@router.put('/{ledger_id}/select')
async def select_ledger(ledger_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    ledger = await get_user_ledger(db, user, ledger_id)
    result = await db.execute(select(UserSetting).where(UserSetting.user_id == user.id))
    setting = result.scalar_one()
    setting.last_ledger_id = ledger.id
    await db.commit()
    return {'current_ledger_id': ledger.id}
