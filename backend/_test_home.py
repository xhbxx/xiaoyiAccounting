import asyncio
import httpx
from app.main import app


async def test():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        t = (await c.post("/auth/wechat-login", json={"code": "test123"})).json()["token"]
        r = await c.get("/home?year=2026&month=5", headers={"Authorization": "Bearer " + t})
        print("状态码:", r.status_code)
        print(r.json())


asyncio.run(test())
