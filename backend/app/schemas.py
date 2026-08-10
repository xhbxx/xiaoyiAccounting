from pydantic import BaseModel
from typing import Optional

class WechatLoginRequest(BaseModel):
    code:str

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

class CategoriesItem(BaseModel):
    id:int
    name:str
    icon:str

class CategoriesResponse(BaseModel):
    type:str
    items:list[CategoriesItem]