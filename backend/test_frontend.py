#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的前端路径测试服务
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from loguru import logger

app = FastAPI(title="前端路径测试服务")

# 挂载静态文件服务（前端页面）
def setup_frontend_routes(app, frontend_name: str, base_path: str):
    """
    设置前端路由的通用函数
    :param app: FastAPI应用实例
    :param frontend_name: 前端名称（用于日志）
    :param base_path: 前端文件夹路径
    """
    frontend_path = os.path.join(os.path.dirname(__file__), base_path)
    if not os.path.exists(frontend_path):
        logger.warning(f"⚠️ 前端目录不存在: {frontend_path}")
        return False
    
    # 挂载静态资源目录
    static_dirs = ["assets", "static"]  # 支持多种静态资源目录名
    for static_dir in static_dirs:
        static_path = os.path.join(frontend_path, static_dir)
        if os.path.exists(static_path):
            mount_path = f"/{base_path}/{static_dir}"
            app.mount(mount_path, StaticFiles(directory=static_path), name=f"{base_path}_{static_dir}")
            logger.info(f"📁 {frontend_name}静态资源已挂载: {static_path} -> {mount_path}")
    
    # 检查index.html是否存在
    index_path = os.path.join(frontend_path, "index.html")
    if not os.path.exists(index_path):
        logger.warning(f"⚠️ index.html不存在: {index_path}")
        return False
    
    # 创建路由处理函数
    async def serve_index():
        return FileResponse(index_path)
    
    async def serve_spa(path: str):
        # 如果是静态资源请求，返回404
        if any(path.startswith(f"{static_dir}/") for static_dir in static_dirs):
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(index_path)
    
    # 注册路由
    app.get(f"/{base_path}", include_in_schema=False)(serve_index)
    app.get(f"/{base_path}/{{path:path}}", include_in_schema=False)(serve_spa)
    
    logger.info(f"📁 {frontend_name}前端页面已启用: {frontend_path} -> /{base_path}")
    return True

# 配置多个前端
frontends = [
    ("管理界面", "ui"),
    ("AI界面", "ai")
]

for frontend_name, base_path in frontends:
    setup_frontend_routes(app, frontend_name, base_path)

@app.get("/")
async def root():
    return {
        "message": "前端路径测试服务",
        "available_frontends": {
            "管理界面": "/ui",
            "AI界面": "/ai"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "test_frontend:app",
        host="0.0.0.0",
        port=8082,
        reload=True,
        log_level="info"
    )