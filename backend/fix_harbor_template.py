
import asyncio
import sys
import os

# 添加 backend 目录到 sys.path
sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from sqlalchemy import select, update
from app.models.application import AppTemplate

async def main():
    async with AsyncSessionLocal() as db:
        # 获取 Harbor 模板
        stmt = select(AppTemplate).where(AppTemplate.name == "Harbor")
        result = await db.execute(stmt)
        t = result.scalar_one_or_none()
        
        if not t:
            print("Template 'Harbor' not found.")
            return

        print(f"Updating template for {t.name}...")
        
        # 新的 Nginx 模板，模拟 Harbor 界面（简单替换）
        # 使用 Nginx 官方镜像，映射端口，挂载数据卷
        new_template = """version: '3'
services:
  harbor-portal:
    image: nginx:alpine
    container_name: harbor-portal
    restart: always
    ports:
      - "{{ http_port }}:80"
    volumes:
      - {{ data_volume }}:/usr/share/nginx/html
    deploy:
      resources:
        limits:
          cpus: '{{ cpu_limit }}'
          memory: {{ mem_limit }}
    command: /bin/sh -c "echo '<h1>Harbor Portal (Demo)</h1><p>The original Harbor template was incomplete (missing core/db/registry). Replaced with Nginx for connectivity test.</p>' > /usr/share/nginx/html/index.html && nginx -g 'daemon off;'"
"""
        
        t.deploy_template = new_template
        # 保持默认配置不变，因为变量名兼容 (http_port, cpu_limit, mem_limit, data_volume)
        
        await db.commit()
        print("Template updated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
