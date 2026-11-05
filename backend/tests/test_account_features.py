"""账户、账本、类别、月预算的隔离接口回归测试。"""
from datetime import datetime, timedelta, timezone
from io import BytesIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

# 在导入应用前指定测试配置，测试只连接内存 SQLite。
for key, value in {
    'DB_HOST': 'localhost', 'DB_USER': 'test', 'DB_PASSWORD': 'test', 'DB_NAME': 'test',
    'JWT_SECRET_KEY': 'isolated-account-feature-test-secret', 'WECHAT_APPID': 'test',
    'WECHAT_SECRET': 'test', 'APP_ENV': 'test',
}.items():
    os.environ[key] = value

from httpx import ASGITransport, AsyncClient, ConnectError, ReadTimeout, Request, Response
from PIL import Image
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.core.security import create_access_token
from app.models import User, Ledger, UserSetting, Category, MonthlyBudget
from app.api import auth, profile


class AccountFeatureTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine('sqlite+aiosqlite:///:memory:')
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async def test_db():
            async with self.sessions() as db:
                yield db
        app.dependency_overrides[get_db] = test_db
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url='http://test',
                                  headers={'Authorization': 'Bearer ' + create_access_token(1)})
        self.other_headers = {'Authorization': 'Bearer ' + create_access_token(2)}
        async with self.sessions() as db:
            db.add_all([User(id=1, openid='one'), User(id=2, openid='two')])
            await db.flush()
            db.add_all([Ledger(id=1, user_id=1), Ledger(id=2, user_id=2)])
            await db.flush()
            db.add_all([UserSetting(user_id=1, last_ledger_id=1), UserSetting(user_id=2, last_ledger_id=2),
                        Category(id=1, name='餐饮', type='expense', sort=1)])
            await db.commit()

    async def asyncTearDown(self):
        await self.client.aclose()
        app.dependency_overrides.clear()
        await self.engine.dispose()

    async def call(self, method, url, expected=200, **kwargs):
        response = await self.client.request(method, url, **kwargs)
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    async def add_bill(self, date, **values):
        return await self.call('POST', '/bills', 201, json={
            'type': 'expense', 'amount': '10.00', 'category': '餐饮', 'bill_date': date, **values})

    async def test_account_default_and_avatar(self):
        await self.call('PUT', '/profile', json={'nick_name': '小翼'})
        await self.call('PUT', '/profile/settings', json={'default_bill_type': 'income'})
        data = await self.call('GET', '/profile')
        self.assertEqual(data['user']['nick_name'], '小翼')
        self.assertEqual(data['settings']['default_bill_type'], 'income')
        other = await self.call('GET', '/profile', headers=self.other_headers)
        self.assertIsNone(other['user']['nick_name'])
        await self.call('PUT', '/profile', 422, json={'nick_name': ' '})
        await self.call('PUT', '/profile/settings', 422, json={'default_bill_type': 'invalid'})
        with tempfile.TemporaryDirectory() as directory, patch.object(profile, 'AVATAR_DIR', Path(directory)):
            stream = BytesIO()
            Image.new('RGB', (8, 8), 'yellow').save(stream, format='PNG')
            avatar = await self.call('POST', '/profile/avatar', files={'file': ('avatar.png', stream.getvalue(), 'image/png')})
            self.assertTrue((Path(directory) / avatar['avatar_url'].split('/')[-1]).exists())
            await self.call('POST', '/profile/avatar', 400, files={'file': ('bad.png', b'not an image', 'image/png')})
            await self.call('POST', '/profile/avatar', 400, files={'file': ('huge.png', b'x' * (2 * 1024 * 1024 + 1), 'image/png')})

    async def test_statistics_use_unique_bill_dates_across_ledgers(self):
        today = datetime.now(timezone(timedelta(hours=8))).date()
        yesterday = str(today - timedelta(days=1))
        await self.add_bill(yesterday)
        await self.add_bill(yesterday, type='income')
        await self.add_bill(str(today - timedelta(days=2)))
        data = (await self.call('GET', '/profile'))['statistics']
        self.assertEqual(data, {'consecutive_days': 2, 'total_days': 2, 'total_bills': 3})
        other = await self.call('GET', '/profile', headers=self.other_headers)
        self.assertEqual(other['statistics']['total_bills'], 0)
        bill = await self.add_bill(str(today))
        data = (await self.call('GET', '/profile'))['statistics']
        self.assertEqual(data['consecutive_days'], 3)
        await self.call('DELETE', f"/bills/{bill['id']}")
        data = (await self.call('GET', '/profile'))['statistics']
        self.assertEqual(data['consecutive_days'], 2)

    async def test_ledger_switch_and_owner_checks(self):
        ledger = await self.call('POST', '/ledgers', 201, json={'name': '旅行账本'})
        await self.call('PUT', f"/ledgers/{ledger['id']}", json={'name': '旅行'})
        await self.call('PUT', f"/ledgers/{ledger['id']}/select")
        data = await self.call('GET', '/ledgers')
        self.assertEqual(data['current_ledger_id'], ledger['id'])
        await self.add_bill('2026-11-04')
        home = await self.call('GET', '/home?year=2026&month=11')
        self.assertEqual(home['ledger']['id'], ledger['id'])
        self.assertEqual(home['period']['expense'], '10.00')
        home = await self.call('GET', '/home?year=2026&month=11&ledger_id=1')
        self.assertEqual(home['groups'], [])
        await self.call('PUT', '/ledgers/2/select', 404)
        await self.call('PUT', '/ledgers/2', 404, json={'name': '越权'})

    async def test_categories_keep_history_and_system_categories_readonly(self):
        category = await self.call('POST', '/categories', 201, json={'name': '宠物', 'type': 'expense'})
        await self.add_bill('2026-11-04', category='宠物')
        await self.call('PUT', f"/categories/{category['id']}", json={'name': '猫咪', 'type': 'expense'})
        await self.call('DELETE', f"/categories/{category['id']}", 404, headers=self.other_headers)
        await self.call('DELETE', f"/categories/{category['id']}")
        home = await self.call('GET', '/home?year=2026&month=11')
        self.assertEqual(home['groups'][0]['items'][0]['category'], '宠物')
        await self.call('DELETE', '/categories/1', 403)
        await self.call('PUT', '/categories/1', 403, json={'name': '其他', 'type': 'expense'})
        await self.call('POST', '/categories', 409, json={'name': '餐饮', 'type': 'expense'})

    async def test_budget_isolated_by_month_and_ledger(self):
        budget = {'ledger_id': 1, 'year': 2026, 'month': 11, 'amount': '50.00'}
        await self.add_bill('2026-11-04', amount='60.00')
        await self.call('PUT', '/home/budget', json=budget)
        data = await self.call('GET', '/home?year=2026&month=11')
        self.assertEqual(data['budget'], {'amount': '50.00', 'remaining': '-10.00', 'remaining_percent': 0.0})
        await self.call('PUT', '/home/budget', json={**budget, 'amount': '100.00'})
        data = await self.call('GET', '/home?year=2026&month=11')
        self.assertEqual(data['budget']['remaining'], '40.00')
        self.assertEqual(data['budget']['remaining_percent'], 40.0)
        self.assertIsNone((await self.call('GET', '/home?year=2026&month=12'))['budget'])
        await self.call('PUT', '/home/budget', 404, json={**budget, 'ledger_id': 2})
        await self.call('PUT', '/home/budget', 422, json={**budget, 'amount': '0'})
        async with self.sessions() as db:
            self.assertEqual(await db.scalar(select(func.count(MonthlyBudget.id))), 1)

    async def test_login_uses_wechat_identity_and_handles_invalid_code(self):
        with patch.object(auth, 'exchange_wechat_code', AsyncMock(return_value={'openid': 'real-openid'})) as exchange:
            first = await self.call('POST', '/auth/wechat-login', json={'code': 'temporary-code'})
            second = await self.call('POST', '/auth/wechat-login', json={'code': 'another-code'})
            self.assertTrue(first['is_new_user'])
            self.assertFalse(second['is_new_user'])
            self.assertEqual(first['user']['id'], second['user']['id'])
            exchange.assert_awaited_with('another-code')
        with patch.object(auth.httpx, 'AsyncClient') as client:
            client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=Response(200, json={'errcode': 40029}, request=Request('GET', 'https://test')))
            await self.call('POST', '/auth/wechat-login', 400, json={'code': 'invalid'})

    async def test_wechat_failures_log_diagnostics_without_credentials(self):
        secret = 'private-diagnostic-test-secret'
        request = Request('GET', 'https://api.weixin.qq.com/sns/jscode2session',
                          params={'secret': secret, 'js_code': 'private-login-code'})
        failures = (
            (ConnectError(str(request.url), request=request), 502, 'ConnectError'),
            (ReadTimeout(str(request.url), request=request), 504, 'ReadTimeout'),
        )
        for error, status, diagnostic in failures:
            with self.subTest(diagnostic=diagnostic), patch.object(auth.httpx, 'AsyncClient') as client:
                client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=error)
                with self.assertLogs(auth.logger, level='WARNING') as logs:
                    response = await self.call('POST', '/auth/wechat-login', status,
                                               json={'code': 'private-login-code'})
                output = '\n'.join(logs.output) + str(response)
                self.assertIn(diagnostic, output)
                self.assertNotIn(secret, output)
                self.assertNotIn('private-login-code', output)

        with patch.object(auth.httpx, 'AsyncClient') as client:
            client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=Response(503, request=request))
            with self.assertLogs(auth.logger, level='WARNING') as logs:
                await self.call('POST', '/auth/wechat-login', 502, json={'code': 'private-login-code'})
            output = '\n'.join(logs.output)
            self.assertIn('503', output)
            self.assertNotIn(secret, output)
            self.assertNotIn('private-login-code', output)


if __name__ == '__main__':
    unittest.main()
