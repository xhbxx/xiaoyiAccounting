# 小翼记账

基于微信原生小程序和 FastAPI 的个人记账项目，使用 MySQL 保存账单、账本和用户设置，前端采用统一的黄色主题。

## 功能

| 页面 | 功能 |
| --- | --- |
| 明细 | 按月查看收支汇总，按日期查看、编辑和删除账单 |
| 图表 | 按周、月、年查看收入或支出趋势及分类排行 |
| 记账 | 记录收入和支出，选择类别、日期，填写备注，使用加减运算输入金额 |
| 发现 | 查看月度收支和结余，设置当前账本的月预算，通过百分比环查看剩余预算 |
| 我的 | 显示头像、昵称、连续记账天数、总记账天数和总记账笔数 |
| 我的账本 | 新增、改名和切换账本 |
| 设置 | 修改头像和昵称，设置默认记账类型，管理自定义类别 |

- 使用真实微信登录，首次登录自动创建默认账本和用户设置。
- 记账天数按账单日期去重统计，连续天数允许从昨天延续，各账本的记录共同计入个人统计。
- 月预算按账本、年份和月份保存，以对应月份的支出抵扣。
- 自定义类别支持新增、改名和删除，历史账单保留记账时的类别名称，系统预设类别只读。

## 技术栈与目录

- 前端使用微信原生小程序，趋势图使用 ECharts。
- 后端使用 Python、FastAPI、SQLAlchemy 异步接口和 aiomysql，登录凭证使用 JWT。
- 数据库使用 MySQL，后端镜像基于 Python 3.12。

```text
.
├── miniprogram/              小程序页面、组件、图片和请求封装
├── backend/
│   ├── app/                  后端接口、数据模型和配置
│   ├── migrations/           空库初始化与数据库增量 SQL
│   ├── tests/                后端接口回归测试
│   ├── requirements.txt      Python 依赖
│   ├── Dockerfile            云托管镜像构建配置
│   └── .dockerignore         镜像构建忽略规则
├── tests/                    前端金额运算和预算环测试
├── cloudfunctions/           初始模板保留的云函数示例
├── project.config.json       微信开发者工具项目配置
└── README.md
```

当前记账业务通过 HTTP 请求访问 FastAPI。`cloudfunctions/` 和 `uploadCloudFunction.sh` 是模板遗留的示例及上传脚本。

## 本地运行

### 准备数据库与配置

准备 Python 3.12、MySQL 和微信开发者工具。在 `backend/.env` 中填写以下配置，将示例值替换为自己的实际值。

```dotenv
APP_ENV=dev
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=xiaoyi
JWT_SECRET_KEY=replace_with_a_random_secret
WECHAT_APPID=your_miniprogram_appid
WECHAT_SECRET=your_miniprogram_appsecret
```

`WECHAT_APPID` 需要与微信开发者工具中使用的小程序 AppID 一致。`.env` 已加入 Git 忽略规则，密钥保存在本地配置或部署环境变量中。

在数据库管理工具中选中与 `DB_NAME` 对应的空数据库，按 UTF-8 编码导入 `backend/migrations/000_initial_schema.sql`。该文件创建 6 张业务表并初始化 11 个系统预设类别，首次微信登录时会自动创建用户、默认账本和用户设置。导入后可以执行 `SHOW TABLES;` 检查表结构，通过 `SELECT name, type FROM categories WHERE user_id IS NULL;` 检查预设类别。

已有完整业务表、仅缺少月预算表的数据库，可以执行 `backend/migrations/001_monthly_budgets.sql`。该 SQL 的外键使用 `INT UNSIGNED`，执行前需要确认已有 `ledgers.id` 的类型一致。

### 启动后端

在 PowerShell 中进入 `backend` 目录后执行。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

启动后可以打开接口文档 `http://127.0.0.1:8000/docs`。登录、账单等业务接口需要数据库连接和表结构配置完成。

### 启动小程序

1. 在微信开发者工具中导入项目根目录，使用自己的小程序 AppID。
2. 确认 `miniprogram/utils/config.js` 中的 `BASE_URL` 为 `http://127.0.0.1:8000`。
3. 本地联调时，在开发者工具的本地设置中开启“不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书”。
4. 编译运行，使用微信登录后查看账本和账单。

本地回环地址用于同一台电脑上的开发者工具联调。真机访问需要配置手机可访问的后端地址。

## 微信云托管部署

仓库已包含后端 `Dockerfile`。在云托管中绑定本项目的 GitHub 仓库和部署分支，填写以下构建参数。

| 配置项 | 值 |
| --- | --- |
| 目标目录 | `backend` |
| Dockerfile 文件 | 有 |
| Dockerfile 名称 | `Dockerfile` |
| 服务端口 | `8000` |

容器使用 `uvicorn app.main:app --host 0.0.0.0 --port 8000` 启动。云托管的目标目录和端口配置可参考[官方说明](https://docs.cloudbase.net/run/deploy/deploy/introduce)。

开启云托管开放接口服务后，平台会通过 `/app/cert/certificate.crt` 提供 HTTPS 证书。后端检测到该文件时，会在公共 CA 的基础上加载平台证书，用于请求微信登录接口。相关要求见[微信云托管证书说明](https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloudrun/src/guide/weixin/open)。连接失败时，运行日志会记录异常类型、平台证书是否存在和脱敏后的错误详情。

在云托管的环境变量中配置以下内容。

| 变量 | 取值说明 |
| --- | --- |
| `APP_ENV` | `prod` |
| `DB_HOST` | 后端可访问的云端 MySQL 内网地址 |
| `DB_PORT` | MySQL 连接端口，通常为 `3306` |
| `DB_USER` | 数据库用户名 |
| `DB_PASSWORD` | 对应数据库账号的密码 |
| `DB_NAME` | 已创建的数据库名称 |
| `JWT_SECRET_KEY` | 自行生成并保存的随机密钥 |
| `WECHAT_APPID` | 当前小程序的 AppID |
| `WECHAT_SECRET` | 当前小程序的 AppSecret |

完成镜像构建后，还需要完成以下部署工作。

1. 初始化云端数据库业务表和预设类别，并验证数据库连接。
2. 将小程序请求地址改为已部署的 HTTPS 服务地址，配置对应的 request、uploadFile 和 downloadFile 合法域名，并验证头像访问。
3. 处理头像持久化。当前后端将头像写入 `backend/uploads/avatars/`，容器中对应 `/app/uploads/avatars/`，云端需要接入持久化存储或对象存储。
4. 在微信开发者工具中完成联调和真机预览，再上传小程序版本。

当前前端使用 `wx.request` 和 `wx.uploadFile` 访问后端。使用 `wx.cloud.callContainer` 接入云托管的方式需要另行适配。

## 类别图片

新增自定义类别时，可以从现有图标中选择，也可以上传 JPG 或 PNG 图片，单张最大 2MB。上传图片与类别记录在同一个事务中保存，图片内容存放在 MySQL 的 `categories.icon_data` 字段中。类别列表和明细接口按需读取图片地址，图片内容通过独立读取接口加载。

已有数据库需要先执行 `backend/migrations/002_category_images.sql`，再部署新版后端并重新编译小程序。该脚本为类别表新增可空的 `MEDIUMBLOB` 字段，支持重复执行。首次新建数据库也需要在完成基础表初始化后执行该脚本。

## 测试

在项目根目录执行前端回归测试，需要已安装 Node.js。

```powershell
node --test tests/bill-calculation.test.cjs tests/budget-ring.test.cjs
```

后端测试使用内存 SQLite、模拟微信接口及临时头像目录。在 `backend` 目录执行，需要额外安装测试依赖 `aiosqlite`。

```powershell
.\.venv\Scripts\python.exe -m pip install aiosqlite
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```
