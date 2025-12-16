# HaloLight API | Python (FastAPI)

[![License](https://img.shields.io/badge/license-ISC-green.svg)](https://github.com/halolight/halolight-api-python/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-%233776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-%23009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-%23D71F00.svg)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-%23336791.svg)](https://www.postgresql.org/)

基于 FastAPI 0.115+ 的企业级后端 API 实现，与 NestJS/Java 版本共用同一数据库（PostgreSQL）和接口规范，支持 JWT 认证、RBAC 权限、Swagger 文档，为 HaloLight 多框架管理后台提供强大、可扩展的服务端支持。

- 在线预览：<http://halolight-api-python.h7ml.cn>
- API 文档：<http://halolight-api-python.h7ml.cn/api/docs>
- GitHub：<https://github.com/halolight/halolight-api-python>

## 功能亮点

- **FastAPI 0.115+ + Python 3.11+**：现代化异步框架、类型提示、自动文档生成
- **SQLAlchemy 2.0 + PostgreSQL 16**：类型安全的 ORM、关系管理、连接池
- **JWT 认证 + RBAC 权限**：AccessToken/RefreshToken 双令牌机制，支持通配符权限控制
- **Swagger/OpenAPI 文档**：自动生成交互式 API 文档，支持在线测试与调试
- **12 个业务模块**：90+ RESTful API 端点，覆盖用户、角色、权限、文档、文件、日历、通知等
- **企业级架构**：分层设计、依赖注入、全局异常处理、请求验证、日志记录
- **数据库兼容**：与 NestJS/Java 版本共用同一 PostgreSQL 数据库
- **Docker 部署**：多阶段构建优化、Docker Compose 一键部署、健康检查机制

## 目录结构

```
app/
├── main.py                     # FastAPI 应用入口
├── api/                        # API 路由层
│   ├── auth.py                 # 认证端点
│   ├── users.py                # 用户管理
│   ├── roles.py                # 角色管理
│   ├── permissions.py          # 权限管理
│   ├── teams.py                # 团队管理
│   ├── documents.py            # 文档管理
│   ├── files.py                # 文件管理
│   ├── folders.py              # 文件夹管理
│   ├── calendar.py             # 日历事件
│   ├── notifications.py        # 通知管理
│   ├── messages.py             # 消息会话
│   ├── dashboard.py            # 仪表盘统计
│   └── deps.py                 # 依赖注入
├── models/                     # SQLAlchemy 模型（17 个实体）
│   ├── base.py                 # 基类和 cuid 生成器
│   ├── enums.py                # 枚举类型
│   ├── user.py                 # 用户模型
│   ├── role.py                 # 角色和权限模型
│   └── ...                     # 其他业务模型
├── schemas/                    # Pydantic 模式
├── services/                   # 业务逻辑层
└── core/                       # 核心配置
    ├── config.py               # 环境变量配置
    ├── security.py             # JWT 和密码处理
    └── database.py             # 数据库连接
alembic/                        # 数据库迁移
tests/                          # 测试文件
```

## 快速开始

环境要求：Python >= 3.11、PostgreSQL >= 13（或 Neon）。

```bash
git clone https://github.com/halolight/halolight-api-python.git
cd halolight-api-python

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库连接和 JWT 密钥

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

生产构建与启动

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEBUG` | 调试模式 | `false` |
| `API_PREFIX` | API 前缀 | `/api` |
| `DATABASE_URL` | PostgreSQL 数据库连接 | - |
| `JWT_SECRET_KEY` | JWT 密钥（≥32字符） | - |
| `JWT_REFRESH_SECRET_KEY` | RefreshToken 密钥 | - |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | AccessToken 过期时间（分钟） | `10080`（7天） |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | RefreshToken 过期时间（天） | `30` |
| `CORS_ORIGINS` | CORS 允许源 | `["http://localhost:3000"]` |

在项目根目录创建 `.env` 文件来配置环境变量：

```bash
# .env 示例
DEBUG=false
DATABASE_URL=postgresql://user:password@localhost:5432/halolight_db
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-min-32-chars
JWT_REFRESH_SECRET_KEY=your-refresh-secret-key-change-in-production
CORS_ORIGINS=["http://localhost:3000","https://halolight.h7ml.cn"]
```

## 常用脚本

```bash
# 开发
uvicorn app.main:app --reload --port 8000    # 启动开发服务器（热重载）

# 代码质量
black app tests                              # 代码格式化
ruff check app tests                         # Lint 检查
ruff check app tests --fix                   # Lint 自动修复
mypy app                                     # 类型检查

# 测试
pytest                                       # 运行测试
pytest --cov=app tests/                      # 测试覆盖率

# 数据库迁移
alembic revision --autogenerate -m "描述"    # 创建迁移
alembic upgrade head                         # 应用迁移
alembic downgrade -1                         # 回滚一个版本
```

## API 模块

项目包含 **12 个核心业务模块**，提供 **90+ RESTful API 端点**：

| 模块 | 端点数 | 描述 |
|------|--------|------|
| **Auth** | 7 | 用户认证（登录、注册、刷新 Token、登出、忘记/重置密码） |
| **Users** | 7 | 用户管理（CRUD、分页、搜索、状态更新、批量删除） |
| **Roles** | 6 | 角色管理（CRUD + 权限分配） |
| **Permissions** | 4 | 权限管理（支持通配符权限） |
| **Teams** | 7 | 团队管理（成员增删） |
| **Documents** | 11 | 文档管理（支持标签、分享、移动） |
| **Files** | 14 | 文件管理（上传、下载、收藏、批量操作） |
| **Folders** | 5 | 文件夹管理（树形结构） |
| **Calendar** | 9 | 日历事件管理（参会人、改期） |
| **Notifications** | 5 | 通知管理 |
| **Messages** | 5 | 消息会话 |
| **Dashboard** | 9 | 仪表盘统计 |

### 在线文档

- **Swagger API 文档**：<http://halolight-api-python.h7ml.cn/api/docs> - 交互式 API 测试与调试
- **ReDoc 文档**：<http://halolight-api-python.h7ml.cn/api/redoc> - 美观的 API 参考文档
- **完整使用指南（中文）**：<https://halolight.docs.h7ml.cn/guide/api-python> - 详细的 API 参考和使用示例

## 代码规范

- **分层架构**：Router → Service → Model，职责清晰
- **依赖注入**：使用 FastAPI 的 `Depends` 进行依赖注入
- **类型安全**：严格的 Python 类型提示，mypy 类型检查
- **格式化**：Black 代码格式化（行宽 100）
- **Lint**：Ruff 代码检查
- **测试规范**：pytest 单元测试
- **提交规范**：遵循 Conventional Commits 规范（`feat:`, `fix:`, `docs:` 等）

## 部署

### Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/halolight/halolight-api-python.git
cd halolight-api-python

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库密码、JWT密钥等

# 启动所有服务（API + PostgreSQL）
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

### Docker 镜像构建

```bash
docker build -t halolight-api-python .
docker run -p 8000:8000 --env-file .env halolight-api-python
```

### 自托管部署

1. **环境准备**：确保 Python >= 3.11 已安装
2. **配置环境变量**：创建 `.env` 文件并设置必要变量
3. **安装依赖**：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
4. **运行迁移**：
   ```bash
   alembic upgrade head
   ```
5. **启动服务**：
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
6. **进程守护**（可选）：使用 systemd、Supervisor 或 Docker 运行

## 数据库兼容性

本项目与 NestJS/Java 版本共用同一 PostgreSQL 数据库：

- 表名与 Prisma schema 一致（如 `users`、`roles`、`teams`）
- 主键使用 cuid 格式字符串
- ENUM 类型复用 Prisma 创建的类型
- 支持同时运行多个后端版本

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进项目！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 相关链接

- [在线预览](http://halolight-api-python.h7ml.cn)
- [API 文档](http://halolight-api-python.h7ml.cn/api/docs)
- [HaloLight 文档](https://github.com/halolight/docs)
- [HaloLight Next.js](https://github.com/halolight/halolight)
- [HaloLight Vue](https://github.com/halolight/halolight-vue)
- [HaloLight API NestJS](https://github.com/halolight/halolight-api-nestjs)
- [HaloLight API Java](https://github.com/halolight/halolight-api-java)
- [问题反馈](https://github.com/halolight/halolight-api-python/issues)

## 许可证

[ISC](LICENSE)
