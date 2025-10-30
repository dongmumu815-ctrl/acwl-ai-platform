from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import load_env_file  # 加载环境变量配置
from app.api import datasource, explorer, auth
from app.database.sqlite_db import init_db
from app.middleware.auth_middleware import AuthMiddleware
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    yield
    # 关闭时的清理工作（如果需要）

app = FastAPI(
    title="DataAInsight API",
    description="数据探查工具后端API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vue开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加认证中间件
app.add_middleware(AuthMiddleware)

# 包含路由
app.include_router(auth.router, prefix="/dataainsight/api/auth", tags=["认证"])
app.include_router(datasource.router, prefix="/dataainsight/api/datasource", tags=["数据源管理"])
app.include_router(explorer.router, prefix="/dataainsight/api/explorer", tags=["数据探查"])

# 静态文件服务
static_dir = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    
    @app.get("/dataainsight")
    async def serve_frontend():
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    @app.get("/{full_path:path}")
    async def serve_frontend_routes(full_path: str):
        # 如果是API路径，跳过
        if full_path.startswith("api/"):
            return {"error": "API endpoint not found"}
        
        # 检查文件是否存在
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # 对于前端路由，返回index.html
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "DataAInsight API is running. Frontend not built yet."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="10.20.1.200", port=8001, reload=True)