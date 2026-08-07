import jwt
from datetime import datetime,timedelta,timezone
from app.core.config import settings

def create_access_token(user_id):
    expire = datetime.now(timezone.utc)+timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload={"sub":str(user_id),"exp":expire}
    return jwt.encode(payload,settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM)

def decode_token(token):
    return jwt.decode(token,settings.JWT_SECRET_KEY,algorithms=[settings.JWT_ALGORITHM])


