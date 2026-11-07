from io import BytesIO

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError


async def read_image_upload(file: UploadFile, label: str):
    try:
        content = await file.read(2 * 1024 * 1024 + 1)
    finally:
        await file.close()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f'{label}大小不能超过 2MB')
    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in ('JPEG', 'PNG') or image.width * image.height > 16000000:
                raise ValueError('invalid image format or size')
            suffix = '.jpg' if image.format == 'JPEG' else '.png'
            image.verify()
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail='请选择 JPG 或 PNG 图片')
    return content, suffix
