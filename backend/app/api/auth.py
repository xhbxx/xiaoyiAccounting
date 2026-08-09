from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.database import get_db
from app.models import User, Ledger, UserSetting
from app.schemas import WechatLoginRequest, LoginResponse, UserInfo

router = APIRouter(prefix="/auth",tags=["认证"])

@router.post("/wechat-login")
async def wechat_login(req:WechatLoginRequest,db:AsyncSession = Depends(get_db)):
        openid = req.code
        result = await db.execute(select(User).where(User.openid==openid))
        user=result.scalar_one_or_none()

        if user:
            is_new_user = False
        else:
            is_new_user=True
            user=User(openid=openid)
            db.add(user)
            await db.flush()

            ledger= Ledger(user_id=user.id)
            db.add(ledger)
            await db.flush()

            setting = UserSetting(user_id=user.id,last_ledger_id=ledger.id)
            db.add(setting)
            await db.flush()
            
            await db.commit()
        token = create_access_token(user.id) 
        return LoginResponse(
            token=token,
            token_type="Bearer",
            user=UserInfo(id=user.id,nick_name=user.nick_name,avatar_url=user.avatar_url),
            is_new_user=is_new_user
        )

        

        
