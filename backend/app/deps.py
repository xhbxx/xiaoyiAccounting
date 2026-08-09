from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import  select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.db.database import get_db
from app.models import User


async def   get_current_user(
    creds:HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db:AsyncSession = Depends(get_db)
):
    try:
        payload= decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401,detail="token无效或已过期")
    
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id==user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code = 401,detail = "用户不存在")
    return user