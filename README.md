# 电商客服系统（Ecommerce Customer Service）

一个面向课堂演示与学习的电商客服示例项目，由三个独立但协作的服务组成：电商业务服务、智能客服后端、以及 Vue 前端。客服后端通过 LLM 与业务服务接口，帮助用户查询订单 / 物流 / 商品，并提交退款、发货提醒等操作。

> 项目来自 atguigu 课堂示例，数据覆盖待发货、待揽收、运输中、已完成、已取消、已有退款申请、已有发货提醒等多种典型状态，便于演示。

## 目录结构

```
ecommerce-customer-service/
├── ecommerce-service-backend/   # 电商业务服务（FastAPI + SQLAlchemy + MySQL）
├── customer-service/           # 智能客服后端（FastAPI + LangChain + MySQL）
├── customer-service-frontend/  # 客服前端（Vue 3 + Vite）
└── docker/                      # MySQL 容器与初始化 SQL
    ├── docker-compose.yml
    └── mysql/initdb/
        ├── 001_init_customer_service.sql   # customer_service 库
        └── 002_init_commerce.sql           # commerce 库
```

## 服务总览

| 服务 | 技术栈 | 默认端口 | 说明 |
|------|--------|----------|------|
| 电商业务服务 | Python + FastAPI + SQLAlchemy + MySQL | `18081` | 提供订单、物流、商品查询及退款 / 发货提醒创建 |
| 智能客服后端 | Python + FastAPI + LangChain + MySQL | `18082` | 接收前端会话，调用 LLM 与业务服务编排对话 |
| 客服前端 | Vue 3 + Vite | `5173` | 聊天界面与业务对象（订单 / 商品）侧边栏 |
| MySQL | mysql:8.4 | `3307` | 同时承载 `commerce` 与 `customer_service` 两个库 |

## 整体架构

```
┌────────────────┐     /api/chat      ┌──────────────────┐    HTTP/LLM     ┌────────────────────────┐
│  Vue 前端 :5173 │ ─────────────────▶ │ 客服后端 :18082  │ ───────────────▶ │ 电商业务服务 :18081    │
│  (聊天 + 侧栏)  │ ◀───────────────── │ (LangChain)      │                  │ (订单/物流/商品/退款)   │
└────────────────┘     /api/chat/history└──────────────────┘                  └────────────────────────┘
                                                   │                                          │
                                                   └────────── MySQL :3307 ───────────────────┘
                                                       (commerce + customer_service)
```

前端通过 Vite 开发代理把 `/api`、`/health` 转发到客服后端，把 `/commerce` 转发到电商业务服务（见 `customer-service-frontend/vite.config.js`）。

## 快速开始

### 1. 准备环境

- Docker（推荐通过 Docker Desktop 使用 Docker Compose）
- Python 3.11 ~ 3.13（本地开发时；推荐用 [`uv`](https://docs.astral.sh/uv/) 管理依赖）
- Node.js 18+（前端开发）

### 2. 启动 MySQL 与初始化数据

```powershell
cd docker
docker compose up -d --build
```

容器会：
- 启动 MySQL 8.4，端口映射 `3307:3306`
- 用 `MYSQL_ROOT_PASSWORD=root`、业务账号 `atguigu / Atguigu.123` 初始化
- 自动执行 `initdb/*.sql`，创建 `commerce`、`customer_service` 两个库并写入演示数据

> 若旧卷里残留了乱码数据，先清理卷再重建：`docker compose down -v && docker compose up -d --build`

### 3. 启动电商业务服务

```powershell
cd ecommerce-service-backend
uv sync
uv run python main.py
# 或：uv run uvicorn app.app:app --reload --port 18081
```

启动后：
- API：`http://127.0.0.1:18081`
- OpenAPI 文档：`http://127.0.0.1:18081/docs`

环境变量见 `ecommerce-service-backend/.env.example`，复制为 `.env` 后按需修改。核心接口：

- `GET /health`
- `GET /users/{user_id}/orders`
- `GET /users/{user_id}/products`
- `GET /orders/{order_id}`
- `GET /orders/{order_id}/status`
- `GET /orders/{order_id}/logistics`
- `GET /products/{product_id}`
- `POST /orders/{order_id}/shipping-reminders`
- `POST /orders/{order_id}/refund-applications`

### 4. 启动智能客服后端

```powershell
cd customer-service
uv sync
# 复制配置模板并填入你的 LLM_API_KEY
cp .env.example .env
uv run uvicorn atguigu.app.app:app --reload --port 18082
```

`.env` 关键变量：

| 变量 | 说明 |
|------|------|
| `LLM_MODEL` | LLM 模型名（默认 `qwen-plus`） |
| `LLM_BASE_URL` | 兼容 OpenAI 协议的接入地址（示例为阿里云 DashScope） |
| `LLM_API_KEY` | **你的 LLM API Key，请勿提交到仓库** |
| `COMMERCE_API_BASE_URL` | 电商业务服务地址（默认 `http://127.0.0.1:18081`） |
| `DATABASE_URL` | 客服库异步连接串 |
| `APP_HOST` / `APP_PORT` | 监听地址与端口 |

### 5. 启动前端

```powershell
cd customer-service-frontend
npm install
npm run dev
```

打开 `http://127.0.0.1:5173`，默认 `sender_id` 为 `u1001`，可直接发消息或点击右侧订单 / 商品把业务对象送入会话。

## 客服后端设计要点

`customer-service/atguigu/` 下按分层组织：

- `app/` — FastAPI 入口与路由（`/api/chat`、`/api/chat/history`）及 Pydantic schema
- `conf/` — 基于 `pydantic-settings` 的配置加载（读取 `.env`）
- `clients/` — 对外客户端：`llm_client`（LangChain）、`http_client`（业务服务）、`database_client`（异步 SQLAlchemy）
- `domain/` — 领域模型：对话状态（`DialogueState`）、共享状态、任务实例与会话 / 轮次
- `engine/` — 对话引擎，负责消费用户消息并产出 Bot 回复
- `service/` — 对话服务，串联「加载状态 → 引擎处理 → 保存状态」
- `repository/` — 对话状态的持久化（`dialogue_states` 表）
- `models/` — ORM 模型
- `task/` — 任务编排：
  - `flow/` — 基于 YAML 的流程定义与执行器（`flow_config/user_flows.yml`）
  - `command/`、`lifecycle/`、`response/` — 命令处理、任务生命周期事件、响应模型

内置流程（`user_flows.yml`）：欢迎引导、订单状态查询、物流查询、退款申请、相似商品推荐、人工客服。流程通过 `start → collect → action → response → end` 等步骤组合，支持条件分支。

## 数据库初始化说明

两个库均由 `docker/mysql/initdb/` 下的 SQL 自动创建并赋权给 `atguigu`：

- `customer_service`：`dialogue_states(sender_id, state_json)`，用于持久化对话状态
- `commerce`：`users`、`products`、`orders`、`order_items`、`logistics_records`、`logistics_traces`、`refund_requests`、`shipping_urge_requests`，并写入覆盖多种状态的演示数据

## 安全与仓库规范

- `.env`、密钥、凭据已加入 `.gitignore`，请勿提交；配置请基于各 `*.env.example` 模板创建本地 `.env`
- `node_modules/`、`.venv/`、`__pycache__/`、`.idea/`、`.jbeval/` 等依赖与产物目录均已忽略，不要入库
- 提交前请确认未包含真实 `LLM_API_KEY` 或数据库生产口令；本地演示口令仅用于 Docker 容器

## 本地开发提示

- 后端两个服务都用 `uv` 管理依赖，`uv.lock` 已入库以保证可复现安装
- 前端 `package-lock.json` 已入库；开发期 Vite 代理已配置好 `/api`、`/commerce`、`/health`
- 业务服务默认 `DATABASE_URL` 指向 Docker 的 MySQL（`127.0.0.1:3307`）；若自建数据库请修改 `.env`

## License

本项目为 atguigu 课堂示例，仅供学习使用。
