"""FastAPI application entry point."""

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.api import (
    auth,
    calendar,
    dashboard,
    documents,
    files,
    folders,
    messages,
    notifications,
    permissions,
    roles,
    teams,
    users,
)
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(roles.router, prefix=settings.API_PREFIX)
app.include_router(permissions.router, prefix=settings.API_PREFIX)
app.include_router(teams.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(files.router, prefix=settings.API_PREFIX)
app.include_router(folders.router, prefix=settings.API_PREFIX)
app.include_router(calendar.router, prefix=settings.API_PREFIX)
app.include_router(notifications.router, prefix=settings.API_PREFIX)
app.include_router(messages.router, prefix=settings.API_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)


def get_home_page() -> str:
    """Generate beautiful home page HTML."""
    env = settings.ENVIRONMENT
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="HaloLight API - 基于 FastAPI + SQLAlchemy 的企业级后端服务">
  <meta name="keywords" content="FastAPI, API, Python, SQLAlchemy, PostgreSQL, JWT, RBAC">
  <title>HaloLight API | Python FastAPI Backend</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🐍</text></svg>">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          colors: {{
            primary: '#3b82f6',
            secondary: '#10b981',
            accent: '#f59e0b',
          }}
        }}
      }}
    }}
  </script>
  <style>
    :root {{
      --primary: #3b82f6;
      --primary-dark: #2563eb;
      --secondary: #10b981;
      --accent: #f59e0b;
      --bg-dark: #0f172a;
      --gradient: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 50%, var(--accent) 100%);
    }}
    .bg-gradient-animated::before {{
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: radial-gradient(circle at 30% 30%, rgba(59, 130, 246, 0.15) 0%, transparent 50%),
                  radial-gradient(circle at 70% 70%, rgba(16, 185, 129, 0.1) 0%, transparent 50%),
                  radial-gradient(circle at 50% 50%, rgba(245, 158, 11, 0.05) 0%, transparent 50%);
      animation: rotate 30s linear infinite;
    }}
    @keyframes rotate {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(360deg); }}
    }}
    .text-gradient {{
      background: var(--gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .bg-gradient-brand {{ background: var(--gradient); }}
    .btn-gradient {{
      background: var(--gradient);
      box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
    }}
    .btn-gradient:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
    }}
    .card-hover:hover {{
      border-color: var(--primary);
      transform: translateY(-4px);
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }}
    .module-hover:hover {{
      border-color: var(--primary);
      background: rgba(59, 130, 246, 0.1);
    }}
  </style>
</head>
<body class="bg-slate-900 text-slate-50 min-h-screen overflow-x-hidden font-sans">
  <div class="fixed inset-0 bg-slate-900 -z-10 bg-gradient-animated"></div>

  <!-- Navigation -->
  <nav class="fixed top-0 left-0 right-0 z-50 py-4 backdrop-blur-xl bg-slate-900/80 border-b border-slate-700/50">
    <div class="max-w-7xl mx-auto px-6 flex justify-between items-center">
      <div class="text-2xl font-bold text-gradient">🐍 HaloLight API</div>
      <div class="hidden md:flex items-center gap-6">
        <a href="#features" class="text-slate-400 hover:text-white text-sm font-medium transition-colors">Features</a>
        <a href="#modules" class="text-slate-400 hover:text-white text-sm font-medium transition-colors">Modules</a>
        <a href="/api/docs" class="text-slate-400 hover:text-white text-sm font-medium transition-colors">API Docs</a>
        <a href="https://github.com/halolight/halolight-api-python" target="_blank" class="text-slate-400 hover:text-white text-sm font-medium transition-colors">GitHub</a>
        <span class="px-3 py-1 text-xs font-semibold rounded-full bg-green-500/20 text-green-400 border border-green-500/30">v{settings.APP_VERSION}</span>
      </div>
    </div>
  </nav>

  <!-- Hero Section -->
  <section class="min-h-screen flex items-center pt-20">
    <div class="max-w-7xl mx-auto px-6">
      <div class="max-w-3xl">
        <div class="inline-flex items-center gap-2 px-4 py-2 bg-slate-800/80 border border-slate-700/50 rounded-full text-sm text-slate-400 mb-6">
          <span class="text-yellow-500">⚡</span> Python FastAPI Backend Service
        </div>
        <h1 class="text-4xl md:text-6xl font-extrabold leading-tight mb-6">
          高性能 Python API<br>
          <span class="text-gradient">企业级解决方案</span>
        </h1>
        <p class="text-xl text-slate-400 leading-relaxed mb-8">
          基于 FastAPI 0.115+ 的企业级后端服务，提供完整的 JWT 认证、RBAC 权限管理、
          Swagger 文档自动生成，90+ RESTful API 端点开箱即用。与 NestJS/Java 版本共用数据库。
        </p>
        <div class="flex flex-col sm:flex-row gap-4 mb-12">
          <a href="/api/docs" class="btn-gradient inline-flex items-center justify-center gap-2 px-7 py-4 text-white font-semibold rounded-xl transition-all">
            📖 Swagger 文档
          </a>
          <a href="/api/redoc" class="inline-flex items-center justify-center gap-2 px-7 py-4 bg-slate-800/80 text-white font-semibold rounded-xl border border-slate-700/50 hover:border-primary hover:bg-slate-800 transition-all">
            📚 ReDoc 文档
          </a>
          <a href="/health" class="inline-flex items-center justify-center gap-2 px-7 py-4 bg-slate-800/80 text-white font-semibold rounded-xl border border-slate-700/50 hover:border-primary hover:bg-slate-800 transition-all">
            💚 健康检查
          </a>
        </div>
        <!-- Tech Stack -->
        <div class="flex flex-wrap gap-3 pt-8 border-t border-slate-700/50">
          <div class="flex items-center gap-2 px-4 py-2 bg-slate-800/80 border border-slate-700/50 rounded-lg text-sm text-slate-400">
            <span>🐍</span> Python 3.11+
          </div>
          <div class="flex items-center gap-2 px-4 py-2 bg-slate-800/80 border border-slate-700/50 rounded-lg text-sm text-slate-400">
            <span>⚡</span> FastAPI 0.115+
          </div>
          <div class="flex items-center gap-2 px-4 py-2 bg-slate-800/80 border border-slate-700/50 rounded-lg text-sm text-slate-400">
            <span>🗄️</span> SQLAlchemy 2.0
          </div>
          <div class="flex items-center gap-2 px-4 py-2 bg-slate-800/80 border border-slate-700/50 rounded-lg text-sm text-slate-400">
            <span>🐘</span> PostgreSQL 16
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Stats Section -->
  <section class="py-16">
    <div class="max-w-7xl mx-auto px-6">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div class="text-center p-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl">
          <div class="text-5xl font-extrabold text-gradient mb-2">12</div>
          <div class="text-slate-400">业务模块</div>
        </div>
        <div class="text-center p-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl">
          <div class="text-5xl font-extrabold text-gradient mb-2">90+</div>
          <div class="text-slate-400">API 端点</div>
        </div>
        <div class="text-center p-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl">
          <div class="text-5xl font-extrabold text-gradient mb-2">17</div>
          <div class="text-slate-400">数据模型</div>
        </div>
        <div class="text-center p-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl">
          <div class="text-5xl font-extrabold text-gradient mb-2">ISC</div>
          <div class="text-slate-400">开源协议</div>
        </div>
      </div>
    </div>
  </section>

  <!-- Features Section -->
  <section id="features" class="py-24">
    <div class="max-w-7xl mx-auto px-6">
      <div class="text-center mb-16">
        <h2 class="text-4xl font-bold mb-4">核心特性</h2>
        <p class="text-slate-400 text-lg max-w-2xl mx-auto">企业级架构设计，开箱即用的完整解决方案</p>
      </div>
      <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="p-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl transition-all card-hover">
          <div class="w-12 h-12 flex items-center justify-center bg-gradient-brand rounded-xl text-2xl mb-5">🔐</div>
          <h3 class="text-xl font-semibold mb-3">JWT 双令牌认证</h3>
          <p class="text-slate-400 leading-relaxed">AccessToken + RefreshToken 机制，支持自动刷新，安全可靠的身份验证方案。</p>
        </div>
        <div class="p-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl transition-all card-hover">
          <div class="w-12 h-12 flex items-center justify-center bg-gradient-brand rounded-xl text-2xl mb-5">🛡️</div>
          <h3 class="text-xl font-semibold mb-3">RBAC 权限控制</h3>
          <p class="text-slate-400 leading-relaxed">基于角色的访问控制，支持通配符权限（users:*, *），灵活的权限管理。</p>
        </div>
        <div class="p-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl transition-all card-hover">
          <div class="w-12 h-12 flex items-center justify-center bg-gradient-brand rounded-xl text-2xl mb-5">📚</div>
          <h3 class="text-xl font-semibold mb-3">Swagger 文档</h3>
          <p class="text-slate-400 leading-relaxed">自动生成交互式 API 文档，支持在线测试，前后端协作更高效。</p>
        </div>
        <div class="p-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl transition-all card-hover">
          <div class="w-12 h-12 flex items-center justify-center bg-gradient-brand rounded-xl text-2xl mb-5">⚡</div>
          <h3 class="text-xl font-semibold mb-3">异步高性能</h3>
          <p class="text-slate-400 leading-relaxed">基于 Python asyncio，支持高并发请求处理，性能媲美 Go/Node.js。</p>
        </div>
        <div class="p-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl transition-all card-hover">
          <div class="w-12 h-12 flex items-center justify-center bg-gradient-brand rounded-xl text-2xl mb-5">✅</div>
          <h3 class="text-xl font-semibold mb-3">Pydantic 验证</h3>
          <p class="text-slate-400 leading-relaxed">使用 Pydantic v2 自动验证请求数据，确保数据完整性和类型安全。</p>
        </div>
        <div class="p-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl transition-all card-hover">
          <div class="w-12 h-12 flex items-center justify-center bg-gradient-brand rounded-xl text-2xl mb-5">🔄</div>
          <h3 class="text-xl font-semibold mb-3">数据库兼容</h3>
          <p class="text-slate-400 leading-relaxed">与 NestJS/Java 版本共用同一 PostgreSQL 数据库，无缝切换后端。</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Modules Section -->
  <section id="modules" class="py-24">
    <div class="max-w-7xl mx-auto px-6">
      <div class="text-center mb-16">
        <h2 class="text-4xl font-bold mb-4">API 模块</h2>
        <p class="text-slate-400 text-lg max-w-2xl mx-auto">12 个核心业务模块，覆盖常见企业应用场景</p>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <a href="/api/docs#/Auth" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">🔑</div>
          <div><h4 class="font-semibold text-white">Auth</h4><span class="text-sm text-slate-400">7 个端点</span></div>
        </a>
        <a href="/api/docs#/Users" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">👥</div>
          <div><h4 class="font-semibold text-white">Users</h4><span class="text-sm text-slate-400">7 个端点</span></div>
        </a>
        <a href="/api/docs#/Roles" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">🎭</div>
          <div><h4 class="font-semibold text-white">Roles</h4><span class="text-sm text-slate-400">6 个端点</span></div>
        </a>
        <a href="/api/docs#/Permissions" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">🔒</div>
          <div><h4 class="font-semibold text-white">Permissions</h4><span class="text-sm text-slate-400">4 个端点</span></div>
        </a>
        <a href="/api/docs#/Teams" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">👨‍👩‍👧‍👦</div>
          <div><h4 class="font-semibold text-white">Teams</h4><span class="text-sm text-slate-400">7 个端点</span></div>
        </a>
        <a href="/api/docs#/Documents" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">📄</div>
          <div><h4 class="font-semibold text-white">Documents</h4><span class="text-sm text-slate-400">11 个端点</span></div>
        </a>
        <a href="/api/docs#/Files" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">📁</div>
          <div><h4 class="font-semibold text-white">Files</h4><span class="text-sm text-slate-400">14 个端点</span></div>
        </a>
        <a href="/api/docs#/Folders" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">📂</div>
          <div><h4 class="font-semibold text-white">Folders</h4><span class="text-sm text-slate-400">5 个端点</span></div>
        </a>
        <a href="/api/docs#/Calendar" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">📅</div>
          <div><h4 class="font-semibold text-white">Calendar</h4><span class="text-sm text-slate-400">9 个端点</span></div>
        </a>
        <a href="/api/docs#/Notifications" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">🔔</div>
          <div><h4 class="font-semibold text-white">Notifications</h4><span class="text-sm text-slate-400">5 个端点</span></div>
        </a>
        <a href="/api/docs#/Messages" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">💬</div>
          <div><h4 class="font-semibold text-white">Messages</h4><span class="text-sm text-slate-400">5 个端点</span></div>
        </a>
        <a href="/api/docs#/Dashboard" class="p-5 bg-slate-800/50 border border-slate-700/50 rounded-xl flex items-center gap-4 transition-all module-hover no-underline">
          <div class="text-2xl">📊</div>
          <div><h4 class="font-semibold text-white">Dashboard</h4><span class="text-sm text-slate-400">9 个端点</span></div>
        </a>
      </div>
    </div>
  </section>

  <!-- CTA Section -->
  <section class="py-24">
    <div class="max-w-7xl mx-auto px-6">
      <div class="relative p-16 bg-gradient-brand rounded-3xl overflow-hidden">
        <div class="relative text-center">
          <h2 class="text-4xl font-bold mb-4">开始使用 HaloLight API</h2>
          <p class="text-lg opacity-90 mb-8">查看完整文档，快速集成到你的项目中</p>
          <div class="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="/api/docs" class="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-blue-600 font-semibold rounded-xl hover:shadow-xl transition-all">
              📖 Swagger 文档
            </a>
            <a href="https://halolight.docs.h7ml.cn/guide/api-python" class="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white/20 text-white font-semibold rounded-xl border border-white/40 hover:bg-white/30 transition-all" target="_blank">
              📚 完整使用指南
            </a>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="py-12 border-t border-slate-700/50">
    <div class="max-w-7xl mx-auto px-6 text-center">
      <div class="flex flex-wrap justify-center gap-8 mb-6">
        <a href="/api/docs" class="text-slate-400 hover:text-white text-sm transition-colors">API 文档</a>
        <a href="https://halolight.docs.h7ml.cn/guide/api-python" target="_blank" class="text-slate-400 hover:text-white text-sm transition-colors">在线使用指南</a>
        <a href="https://github.com/halolight/halolight-api-python" target="_blank" class="text-slate-400 hover:text-white text-sm transition-colors">GitHub</a>
        <a href="https://github.com/halolight/halolight-api-python/issues" target="_blank" class="text-slate-400 hover:text-white text-sm transition-colors">问题反馈</a>
      </div>
      <p class="text-slate-400 text-sm">
        Built with ❤️ by <a href="https://github.com/h7ml" target="_blank" class="text-blue-400 hover:underline">h7ml</a> |
        Powered by FastAPI & SQLAlchemy
      </p>
      <p class="text-slate-500 text-sm mt-2">
        Version {settings.APP_VERSION} | Environment: {env}
      </p>
    </div>
  </footer>
</body>
</html>
    """.strip()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root() -> str:
    """Root endpoint - Beautiful home page.

    Returns:
        HTML home page
    """
    return get_home_page()


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }
