from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.auth import router as auth_router
from app.api.home import router as home_router
from app.api.categories import router as categories_router
from app.api.bills import router as bills_router
from app.api.ledgers import router as ledgers_router
from app.api.statistics import router as statistics_router
from app.api.profile import router as profile_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(home_router)
app.include_router(categories_router)
app.include_router(bills_router)
app.include_router(ledgers_router)
app.include_router(statistics_router)
app.include_router(profile_router)
app.mount('/uploads/avatars', StaticFiles(
    directory=str(Path(__file__).resolve().parents[1] / 'uploads' / 'avatars'),
    check_dir=False,
), name='avatars')
