import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.db.database import get_db
from app.models import User, Ledger, UserSetting
from app.schemas import WechatLoginRequest, LoginResponse, UserInfo

router = APIRouter(prefix="/auth", tags=["认证"])
logger = logging.getLogger(__name__)


async def exchange_wechat_code(code):
    if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
        raise HTTPException(status_code=503, detail="微信登录配置未完成")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={"appid": settings.WECHAT_APPID, "secret": settings.WECHAT_SECRET,
                        "js_code": code, "grant_type": "authorization_code"},
            )
            response.raise_for_status()
            session = response.json()
    except httpx.TimeoutException as error:
        logger.warning("WeChat login request timed out: %s", type(error).__name__)
        raise HTTPException(status_code=504, detail="连接微信登录接口超时，请稍后重试")
    except httpx.HTTPStatusError as error:
        logger.warning("WeChat login HTTP status: %s", error.response.status_code)
        raise HTTPException(status_code=502, detail="微信登录服务暂时不可用，请重试")
    except (httpx.HTTPError, ValueError) as error:
        # 异常文本可能包含 AppSecret 和登录 code，只记录异常类型。
        root_error = error
        while root_error.__cause__ is not None:
            root_error = root_error.__cause__
        logger.warning(
            "WeChat login request failed: %s (cause=%s, errno=%s, reason=%s)",
            type(error).__name__, type(root_error).__name__,
            getattr(root_error, 'errno', None), getattr(root_error, 'reason', None),
        )
        raise HTTPException(status_code=502, detail="微信登录服务暂时不可用，请重试")
    if not isinstance(session, dict):
        raise HTTPException(status_code=502, detail="微信登录服务返回异常")
    if session.get("errcode") in (40029, 40163):
        raise HTTPException(status_code=400, detail="微信登录凭证已失效，请重试")
    if session.get("errcode") or not session.get("openid"):
        raise HTTPException(status_code=502, detail="微信登录失败，请检查后端微信配置")
    return session


@router.post("/wechat-login")
async def wechat_login(req: WechatLoginRequest, db: AsyncSession = Depends(get_db)):
    session = await exchange_wechat_code(req.code)
    openid = session["openid"]
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()
    is_new_user = user is None
    if user is None:
        try:
            user = User(openid=openid, unionid=session.get("unionid"))
            db.add(user)
            await db.flush()
            ledger = Ledger(user_id=user.id)
            db.add(ledger)
            await db.flush()
            db.add(UserSetting(user_id=user.id, last_ledger_id=ledger.id))
            await db.commit()
        except IntegrityError:
            # 并发首次登录时，由 openid 唯一约束保证只创建一个账户。
            await db.rollback()
            result = await db.execute(select(User).where(User.openid == openid))
            user = result.scalar_one_or_none()
            if user is None:
                raise
            is_new_user = False
    return LoginResponse(
        token=create_access_token(user.id), token_type="Bearer",
        user=UserInfo(id=user.id, nick_name=user.nick_name, avatar_url=user.avatar_url),
        is_new_user=is_new_user,
    )
