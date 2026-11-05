import logging
import os
from pathlib import Path
import re
import ssl
from urllib.parse import quote, quote_plus

import certifi
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
WECHAT_PLATFORM_CERTIFICATE = Path('/app/cert/certificate.crt')


async def exchange_wechat_code(code):
    if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
        raise HTTPException(status_code=503, detail="微信登录配置未完成")
    try:
        # 在公共 CA 的基础上信任云托管开放接口服务的证书。
        ssl_context = ssl.create_default_context(
            cafile=os.environ.get('SSL_CERT_FILE') or certifi.where(),
            capath=os.environ.get('SSL_CERT_DIR'),
        )
        if WECHAT_PLATFORM_CERTIFICATE.is_file():
            ssl_context.load_verify_locations(cafile=str(WECHAT_PLATFORM_CERTIFICATE))
        async with httpx.AsyncClient(timeout=10, verify=ssl_context) as client:
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
    except (httpx.HTTPError, ValueError, OSError) as error:
        # 先移除 URL，再清理原始和编码后的凭证，保留连接错误详情。
        message = re.sub(r'https?://\S+', '[redacted-url]', str(error))
        for value in (settings.WECHAT_SECRET, code):
            if value:
                representations = {value, quote(value, safe=''), quote_plus(value)}
                pattern = '|'.join(re.escape(item) for item in representations)
                message = re.sub(pattern, '[redacted]', message, flags=re.IGNORECASE)
        root_error = error
        while root_error.__cause__ is not None:
            root_error = root_error.__cause__
        logger.warning(
            "WeChat login request failed: %s (cause=%s, errno=%s, reason=%s, platform_ca=%s, detail=%s)",
            type(error).__name__, type(root_error).__name__,
            getattr(root_error, 'errno', None), getattr(root_error, 'reason', None),
            WECHAT_PLATFORM_CERTIFICATE.is_file(), message[:500],
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
