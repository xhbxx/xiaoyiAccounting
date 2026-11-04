from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from io import BytesIO
from PIL import Image, UnidentifiedImageError

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select, func

from app.db.database import get_db
from app.deps import get_current_user
from app.models import UserSetting, Bill
from app.schemas import AccountWrite, SettingWrite

router = APIRouter(prefix="/profile", tags=["我的与设置"])
AVATAR_DIR = Path(__file__).resolve().parents[2] / 'uploads' / 'avatars'


async def user_setting(db, user):
    result = await db.execute(select(UserSetting).where(UserSetting.user_id == user.id))
    setting = result.scalar_one_or_none()
    if setting is None:
        raise HTTPException(status_code=404, detail="用户设置不存在")
    return setting


@router.get('')
async def profile(db=Depends(get_db), user=Depends(get_current_user)):
    setting = await user_setting(db, user)
    result = await db.execute(select(func.date(Bill.bill_date)).where(
        Bill.user_id == user.id
    ).distinct())
    dates = {datetime.strptime(str(row), '%Y-%m-%d').date() for row in result.scalars()}
    count = await db.scalar(select(func.count(Bill.id)).where(Bill.user_id == user.id))
    today = datetime.now(timezone(timedelta(hours=8))).date()
    day = today if today in dates else today - timedelta(days=1)
    consecutive_days = 0
    while day in dates:
        consecutive_days += 1
        day -= timedelta(days=1)
    return {
        'user': {'id': user.id, 'nick_name': user.nick_name, 'avatar_url': user.avatar_url},
        'settings': {'default_bill_type': setting.default_bill_type or 'expense'},
        'statistics': {'consecutive_days': consecutive_days, 'total_days': len(dates),
                       'total_bills': count},
    }


@router.put('')
async def update_account(item: AccountWrite, db=Depends(get_db), user=Depends(get_current_user)):
    user.nick_name = item.nick_name
    await db.commit()
    return {'id': user.id, 'nick_name': user.nick_name, 'avatar_url': user.avatar_url}


@router.put('/settings')
async def update_settings(item: SettingWrite, db=Depends(get_db), user=Depends(get_current_user)):
    setting = await user_setting(db, user)
    setting.default_bill_type = item.default_bill_type
    await db.commit()
    return {'default_bill_type': setting.default_bill_type}


@router.post('/avatar')
async def update_avatar(file: UploadFile = File(...), db=Depends(get_db), user=Depends(get_current_user)):
    try:
        content = await file.read(2 * 1024 * 1024 + 1)
    finally:
        await file.close()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail='头像大小不能超过 2MB')
    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in ('JPEG', 'PNG') or image.width * image.height > 16000000:
                raise ValueError('invalid avatar format or size')
            suffix = '.jpg' if image.format == 'JPEG' else '.png'
            image.verify()
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail='请选择 JPG 或 PNG 图片')
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f'{user.id}_{uuid4().hex}{suffix}'
    path = AVATAR_DIR / filename
    path.write_bytes(content)
    user.avatar_url = f'/uploads/avatars/{filename}'
    try:
        await db.commit()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return {'avatar_url': user.avatar_url}
