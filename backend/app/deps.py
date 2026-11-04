from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import  select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.db.database import get_db
from app.models import User, Ledger, UserSetting


async def   get_current_user(
    creds:HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    db:AsyncSession = Depends(get_db)
):
    try:
        if creds is None:
            raise ValueError('missing token')
        payload= decode_token(creds.credentials)
        user_id = int(payload['sub'])
    except Exception:
        raise HTTPException(status_code=401,detail="token无效或已过期")
    
    result = await db.execute(select(User).where(User.id==user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code = 401,detail = "用户不存在")
    return user


async def get_user_ledger(db, user, ledger_id=None):
    if ledger_id is None:
        result = await db.execute(select(UserSetting).where(UserSetting.user_id == user.id))
        setting = result.scalar_one_or_none()
        ledger_id = setting.last_ledger_id if setting else None
    result = await db.execute(select(Ledger).where(
        Ledger.id == ledger_id, Ledger.user_id == user.id
    ))
    ledger = result.scalar_one_or_none()
    if ledger is None:
        raise HTTPException(status_code=404, detail='账本不存在')
    return ledger
