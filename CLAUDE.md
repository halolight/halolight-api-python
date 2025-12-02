# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

HaloLight API Python 是基于 FastAPI 0.115+ + SQLAlchemy 2.0 + PostgreSQL 16 构建的企业级后端 API，与 NestJS/Java 版本共用同一数据库和接口规范，为 HaloLight 多框架管理后台生态系统提供 90+ RESTful 端点，覆盖 12 个核心业务模块。

## 技术栈速览

- **框架**: FastAPI 0.115+ + Python 3.11+
- **ORM**: SQLAlchemy 2.0 + PostgreSQL 16
- **迁移**: Alembic 1.14+
- **认证**: JWT 双令牌机制 (AccessToken + RefreshToken)
- **权限**: RBAC 角色权限控制（支持通配符）
- **验证**: Pydantic v2
- **文档**: Swagger/OpenAPI 自动生成
- **密码**: passlib + bcrypt
- **服务器**: Uvicorn + uvloop

## 常用命令

```bash
# 开发
source .venv/bin/activate                    # 激活虚拟环境
uvicorn app.main:app --reload --port 8000    # 启动开发服务器（热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4  # 生产模式

# 依赖管理
pip install -e .                             # 安装项目依赖
pip install -e ".[dev]"                      # 安装开发依赖

# 代码质量
black app tests                              # 代码格式化
ruff check app tests                         # Lint 检查
ruff check app tests --fix                   # Lint 自动修复
mypy app                                     # 类型检查

# 测试
pytest                                       # 运行测试
pytest --cov=app tests/                      # 测试覆盖率
pytest -v -s tests/test_auth.py              # 运行指定测试

# 数据库 (Alembic)
alembic revision --autogenerate -m "描述"    # 创建迁移
alembic upgrade head                         # 应用迁移
alembic downgrade -1                         # 回滚一个版本
alembic history                              # 查看迁移历史

# Docker
docker-compose up -d                         # 启动 PostgreSQL + API
docker-compose logs -f api                   # 查看日志
docker-compose down                          # 停止服务
```

## 架构

### 模块结构

项目采用分层架构：

```
app/
├── main.py                     # FastAPI 应用入口
├── api/                        # API 路由层
│   ├── auth.py                 # 认证端点（登录、注册、刷新令牌、登出）
│   ├── users.py                # 用户管理（CRUD、分页、搜索）
│   ├── roles.py                # 角色管理（CRUD + 权限分配）
│   ├── permissions.py          # 权限管理
│   ├── teams.py                # 团队管理
│   ├── documents.py            # 文档管理（标签、分享）
│   ├── files.py                # 文件管理
│   ├── folders.py              # 文件夹管理（树形结构）
│   ├── calendar.py             # 日历事件管理
│   ├── notifications.py        # 通知管理
│   ├── messages.py             # 消息会话管理
│   ├── dashboard.py            # 仪表盘统计
│   └── deps.py                 # 依赖注入（认证、权限检查）
├── models/                     # SQLAlchemy 模型层
│   ├── base.py                 # 基类和 cuid 生成器
│   ├── enums.py                # 枚举类型（UserStatus, SharePermission）
│   ├── user.py                 # 用户模型
│   ├── role.py                 # 角色和权限模型
│   ├── team.py                 # 团队模型
│   ├── document.py             # 文档和标签模型
│   ├── file.py                 # 文件和文件夹模型
│   ├── calendar.py             # 日历事件模型
│   ├── conversation.py         # 会话和消息模型
│   ├── notification.py         # 通知模型
│   ├── activity.py             # 活动日志模型
│   └── refresh_token.py        # 刷新令牌模型
├── schemas/                    # Pydantic 模式层
│   ├── user.py                 # 用户相关 DTO
│   ├── role.py                 # 角色相关 DTO
│   ├── team.py                 # 团队相关 DTO
│   └── document.py             # 文档相关 DTO
├── services/                   # 业务逻辑层
│   ├── user_service.py         # 用户服务
│   ├── role_service.py         # 角色服务
│   ├── team_service.py         # 团队服务
│   └── document_service.py     # 文档服务
└── core/                       # 核心配置
    ├── config.py               # 环境变量配置
    ├── security.py             # JWT 和密码处理
    └── database.py             # 数据库连接
```

### 核心设计模式

**认证流程:**
- JWT 认证通过 `get_current_user` 依赖注入
- 使用 `Depends(get_current_active_user)` 保护路由
- 双令牌策略：AccessToken（7天）+ RefreshToken（30天）
- RefreshToken 存储于数据库 `refresh_tokens` 表

**权限控制:**
- RBAC 角色权限，支持通配符匹配（如 `users:read`、`documents:*`、`*`）
- 使用 `check_permission` 依赖进行权限检查
- 权限存储在 `permissions` 表，通过 `role_permissions` 关联

**数据库访问:**
- 所有模型继承自 `Base` 基类
- 主键使用 cuid() 字符串（与 NestJS/Java 版本一致）
- 使用 `joinedload` 进行关系预加载，避免 N+1 查询

**API 结构:**
- 全局前缀：`/api`
- Swagger 文档：`/api/docs`
- ReDoc 文档：`/api/redoc`
- 健康检查：`/health`

### 数据流模式

1. **请求处理**: Router → Service → SQLAlchemy → Database
2. **认证拦截**: Depends(get_current_user) → JWT 验证 → 用户加载
3. **异常处理**: HTTPException 统一错误响应
4. **数据验证**: Pydantic 模式自动验证请求/响应

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | - |
| `JWT_SECRET_KEY` | JWT 签名密钥（≥32字符） | - |
| `JWT_REFRESH_SECRET_KEY` | RefreshToken 密钥 | - |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | AccessToken 过期时间（分钟） | `10080`（7天） |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | RefreshToken 过期时间（天） | `30` |
| `CORS_ORIGINS` | CORS 允许源（JSON 数组） | `["http://localhost:3000"]` |
| `DEBUG` | 调试模式 | `false` |
| `API_PREFIX` | API 前缀 | `/api` |

支持 `.env` 文件配置。

## 代码规范

- **缩进**: 4 空格
- **格式化**: Black（行宽 100）
- **Lint**: Ruff（ESLint 风格规则）
- **类型检查**: mypy 严格模式
- **命名**: 类使用 PascalCase，函数/变量使用 snake_case
- **提交规范**: 遵循 Conventional Commits（`feat:`、`fix:`、`docs:` 等）

## API 模块

项目覆盖 12 个核心业务模块，与 NestJS/Java 版本保持接口一致：

| 模块 | 端点 | 描述 |
|------|------|------|
| **Auth** | `/api/auth/*` | 登录、注册、刷新令牌、登出、忘记/重置密码 |
| **Users** | `/api/users/*` | 用户 CRUD、状态更新、批量删除 |
| **Roles** | `/api/roles/*` | 角色 CRUD、权限分配 |
| **Permissions** | `/api/permissions/*` | 权限管理 |
| **Documents** | `/api/documents/*` | 文档 CRUD、分享、标签、移动 |
| **Files** | `/api/files/*` | 文件上传、下载、收藏、批量操作 |
| **Folders** | `/api/folders/*` | 文件夹 CRUD、树形结构 |
| **Calendar** | `/api/calendar/*` | 日历事件、参会人、改期 |
| **Teams** | `/api/teams/*` | 团队 CRUD、成员管理 |
| **Messages** | `/api/messages/*` | 会话、消息发送、已读标记 |
| **Notifications** | `/api/notifications/*` | 通知管理 |
| **Dashboard** | `/api/dashboard/*` | 仪表盘统计、图表数据 |

## 新增功能开发指南

### 添加新模型

1. 在 `models/` 创建 SQLAlchemy 模型文件
2. 在 `models/__init__.py` 中导出模型
3. 运行 `alembic revision --autogenerate -m "描述"` 创建迁移
4. 运行 `alembic upgrade head` 应用迁移

### 添加新 API 端点

1. 在 `schemas/` 创建请求/响应 Pydantic 模式
2. 在 `services/` 创建或修改 Service 类
3. 在 `api/` 创建路由文件
4. 在 `main.py` 中注册路由
5. 如需权限控制，使用 `Depends(check_permission("resource:action"))`

### 添加新服务

```python
class NewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, id: str) -> Model | None:
        return self.db.query(Model).filter(Model.id == id).first()
```

## 数据库兼容性

本项目与 NestJS/Java 版本共用同一 PostgreSQL 数据库：

- 表名使用 Prisma 的 `@@map` 映射名称（如 `users`、`roles`）
- 主键使用 cuid 格式字符串
- ENUM 类型使用 `create_type=False`（Prisma 已创建）
- 复合主键用于多对多关联表

## 与前端集成

配置前端 API 地址：
```env
# Next.js
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Vue/Vite
VITE_API_URL=http://localhost:8000/api
```
