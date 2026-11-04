from decimal import Decimal

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class BillWrite(BaseModel):
    ledger_id: int | None = Field(default=None, gt=0)
    type: Literal['expense', 'income']
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=1, max_length=64)
    bill_date: datetime
    remark: str | None = Field(default=None, max_length=256)

    @field_validator('category')
    @classmethod
    def validate_category(cls, value):
        if not value.strip():
            raise ValueError('请选择分类')
        return value.strip()

    @field_validator('bill_date', mode='before')
    @classmethod
    def parse_bill_date(cls, value):
        # 同时兼容文档中的日期和旧账单的完整时间。
        for pattern in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.strptime(value, pattern)
            except (ValueError, TypeError):
                continue
        raise ValueError('账单日期格式必须为 YYYY-MM-DD 或 YYYY-MM-DD HH:mm:ss')

class WechatLoginRequest(BaseModel):
    code:str = Field(min_length=1, max_length=256)


class AccountWrite(BaseModel):
    nick_name: str = Field(min_length=1, max_length=64)

    @field_validator('nick_name')
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError('姓名不能为空')
        return value.strip()


class SettingWrite(BaseModel):
    default_bill_type: Literal['expense', 'income']


class NameWrite(BaseModel):
    name: str = Field(min_length=1, max_length=64)

    @field_validator('name', mode='before')
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class CategoryWrite(NameWrite):
    type: Literal['expense', 'income']
    icon: str | None = Field(default=None, max_length=64)


class BudgetWrite(BaseModel):
    ledger_id: int | None = Field(default=None, gt=0)
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

class UserInfo(BaseModel):
    id:int
    nick_name:str| None
    avatar_url:str| None

class LoginResponse(BaseModel):
    token:str
    token_type:str
    user:UserInfo
    is_new_user:bool

class LedgerInfo(BaseModel):
    id:int
    name:str
    icon:str
    color:str
class PeriodInfo(BaseModel):
    year: int
    month: int
    income: str        
    expense: str      
class BillItem(BaseModel):
    id: int
    type: str
    amount: str       
    amount_text: str   
    category: str
    icon: str| None
    remark: str|None
    bill_date: str     
class  BillGroup(BaseModel):
    date: str          
    date_text: str     
    week: str          
    expense_total: str 
    income_total: str  
    items: list[BillItem]   
class  HomeResponse(BaseModel):
    ledger: LedgerInfo
    period: PeriodInfo
    groups: list[BillGroup]
    budget: dict | None = None

class CategoriesItem(BaseModel):
    id:int
    name:str
    icon:str | None
    sort:int | None = None
    is_system:bool = False
class CategoriesResponse(BaseModel):
    type:str
    items:list[CategoriesItem]

class NewBill(BaseModel):
    id: int
    type: str
    amount: str
    bill_date: str
    category: str
    remark: str | None
class BillRespond(BaseModel):
    id:int
    message:str
    bill:NewBill

class Ledger(BaseModel):
    id:int
    name:str
    icon:str
    color:str
    sort:int
