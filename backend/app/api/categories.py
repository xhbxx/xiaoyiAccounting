from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import or_, select
from app.db.database import get_db
from app.deps import get_current_user
from app.models import Category, User
from app.schemas import CategoriesItem, CategoryWrite
from typing import Literal

router=APIRouter(tags=["获取分类"])

@router.get("/categories")
async def categories(
    type:Literal['expense', 'income'],
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
        item=CategoriesItem(id=s.id,name=s.name,icon=s.icon,sort=s.sort,is_system=s.user_id is None)
        items.append(item)

    return {"type": type, "items": items}


async def check_category_name(db, user, item, category_id=None):
    # 串行处理同一用户的类别修改，避免并发提交产生重名。
    await db.execute(select(User.id).where(User.id == user.id).with_for_update())
    query = select(Category.id).where(
        Category.type == item.type, Category.name == item.name,
        or_(Category.user_id.is_(None), Category.user_id == user.id),
    )
    if category_id is not None:
        query = query.where(Category.id != category_id)
    if (await db.execute(query.with_for_update())).first():
        raise HTTPException(status_code=409, detail='同类型下已存在这个类别')


async def editable_category(db, user, category_id):
    result = await db.execute(select(Category).where(
        Category.id == category_id,
        or_(Category.user_id.is_(None), Category.user_id == user.id),
    ))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=404, detail='类别不存在')
    if category.user_id is None:
        raise HTTPException(status_code=403, detail='系统预设类别为只读')
    return category


@router.post('/categories', status_code=201)
async def create_category(item: CategoryWrite, db=Depends(get_db), user=Depends(get_current_user)):
    await check_category_name(db, user, item)
    category = Category(user_id=user.id, name=item.name, type=item.type, icon=item.icon, sort=100)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return {'id': category.id, 'name': category.name}


@router.put('/categories/{category_id}')
async def rename_category(category_id: int, item: CategoryWrite, db=Depends(get_db), user=Depends(get_current_user)):
    category = await editable_category(db, user, category_id)
    if item.type != category.type:
        raise HTTPException(status_code=400, detail='类别的收支类型不能修改')
    await check_category_name(db, user, item, category_id)
    category.name = item.name
    await db.commit()
    return {'id': category.id, 'name': category.name}


@router.delete('/categories/{category_id}')
async def delete_category(category_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    category = await editable_category(db, user, category_id)
    await db.delete(category)
    await db.commit()
    return {'message': '类别已删除'}


