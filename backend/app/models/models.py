from sqlalchemy import DECIMAL, Column, DateTime, ForeignKey, Integer, String, func

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(64), nullable=False, unique=True)
    unionid = Column(String(64))
    nick_name = Column(String(64))
    avatar_url = Column(String(512))
    phone = Column(String(20), unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Ledger(Base):
    __tablename__ = "ledgers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(64), server_default="默认账本")
    icon = Column(String(64), server_default="book")
    color = Column(String(16), server_default="#1677ff")
    sort = Column(Integer, nullable=False, server_default="0")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    categories = Column(String(64), nullable=False)
    type = Column(String(16))
    icon = Column(String(64))
    sort = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ledger_id = Column(Integer, ForeignKey("ledgers.id"), nullable=False)
    type = Column(String(16), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    bill_date = Column(DateTime, nullable=False)
    remark = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    category = Column(String(64))


class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    default_bill_type = Column(String(16), server_default="expense")
    theme_color = Column(String(16), server_default="#1677ff")
    last_ledger_id = Column(Integer, ForeignKey("ledgers.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
