from fastapi import Depends
from fastapi.routing import APIRouter
from sqlalchemy import or_, select
from app.db.database import get_db
from app.deps import get_current_user
from app.models import Category
from app.schemas import CategoriesItem

router=APIRouter(tags=["获取分类"])

@router.get("/categories")
async def categories(
    type:str,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    result = await db.execute(select(Category)
        .where(Category.type==type)
        .where(or_(Category.user_id==None,Category.user_id==current_user.id))
        .order_by(Category.sort.asc()))
    setting=result.scalars().all()

    items=[]
    for s in setting:
        item=CategoriesItem(id=s.id,name=s.name,icon=s.icon)
        items.append(item)

    return {"type": type, "items": items}


