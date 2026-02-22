
import asyncio
import sys
import os

# 添加 backend 目录到 sys.path
sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from sqlalchemy import select, update
from app.models.application import AppTemplate, AppType

async def main():
    async with AsyncSessionLocal() as db:
        # 1. 将现有的 "Harbor" 模板改名为 "Nginx"
        stmt = select(AppTemplate).where(AppTemplate.name == "Harbor")
        result = await db.execute(stmt)
        t_nginx = result.scalar_one_or_none()
        
        if t_nginx:
            print("Found existing 'Harbor' template. Renaming to 'Nginx'...")
            t_nginx.name = "Nginx"
            t_nginx.display_name = "Nginx Web Server"
            t_nginx.description = "High performance web server and reverse proxy server."
            t_nginx.icon = "https://nginx.org/nginx.png" # 简单的在线图标，实际项目中可能存本地
            t_nginx.version = "1.25-alpine"
            # 确保模板内容是纯净的 Nginx
            t_nginx.deploy_template = """version: '3'
services:
  nginx:
    image: nginx:alpine
    container_name: nginx-server
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
    command: /bin/sh -c "echo '<h1>Nginx Web Server</h1><p>Deployed via ACWL AI Platform.</p>' > /usr/share/nginx/html/index.html && nginx -g 'daemon off;'"
"""
            t_nginx.default_config = {
                "http_port": 80,
                "cpu_limit": "0.5",
                "mem_limit": "512M",
                "data_volume": "/data/nginx"
            }
            db.add(t_nginx)
            print("Renamed to 'Nginx' successfully.")
        else:
            print("Existing 'Harbor' template not found. Skipping rename.")

        # 2. 创建真正的 "Harbor" 模板
        # 检查是否已存在
        stmt = select(AppTemplate).where(AppTemplate.name == "Harbor")
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            print("'Harbor' template already exists (maybe created just now?). Skipping creation.")
        else:
            print("Creating new 'Harbor' template...")
            # 这是一个基于 Bitnami Harbor 的简化 Docker Compose 模板
            # 注意：Harbor 部署较复杂，这里提供一个基础版本
            harbor_template_content = """version: '3'
services:
  harbor-core:
    image: bitnami/harbor-core:2
    environment:
      - HARBOR_ADMIN_PASSWORD={{ admin_password }}
      - HARBOR_DATABASE_HOST=harbor-db
      - HARBOR_DATABASE_PASSWORD=bitnami
      - HARBOR_REDIS_HOST=harbor-redis
      - HARBOR_REGISTRY_URL=http://harbor-registry:5000
    depends_on:
      - harbor-db
      - harbor-redis
      - harbor-registry

  harbor-portal:
    image: bitnami/harbor-portal:2
    ports:
      - "{{ http_port }}:8080"
    environment:
      - HARBOR_API_URL=http://harbor-core:8080
    depends_on:
      - harbor-core

  harbor-registry:
    image: bitnami/harbor-registry:2
    environment:
      - REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY=/var/lib/registry
    volumes:
      - {{ data_volume }}/registry:/var/lib/registry

  harbor-db:
    image: bitnami/postgresql:11
    environment:
      - POSTGRESQL_PASSWORD=bitnami
      - POSTGRESQL_DATABASE=registry
    volumes:
      - {{ data_volume }}/database:/bitnami/postgresql

  harbor-redis:
    image: bitnami/redis:6
    environment:
      - ALLOW_EMPTY_PASSWORD=yes
    volumes:
      - {{ data_volume }}/redis:/bitnami/redis/data
"""
            new_harbor = AppTemplate(
                name="Harbor",
                display_name="Harbor Registry",
                version="2.8.0",
                description="Cloud native registry project that stores, signs, and scans content.",
                icon="https://goharbor.io/img/logos/harbor-icon-color.png",
                app_type=AppType.docker_compose,
                deploy_template=harbor_template_content,
                default_config={
                    "http_port": 8080, # Harbor Portal 默认内部 8080
                    "admin_password": "Harbor12345",
                    "data_volume": "/data/harbor",
                    "cpu_limit": "2",
                    "mem_limit": "4G"
                },
                config_schema={
                    "type": "object",
                    "properties": {
                        "http_port": {"type": "integer", "title": "Web Port", "default": 8080},
                        "admin_password": {"type": "string", "title": "Admin Password", "default": "Harbor12345"},
                        "data_volume": {"type": "string", "title": "Data Volume Path", "default": "/data/harbor"}
                    }
                }
            )
            db.add(new_harbor)
            print("New 'Harbor' template created.")

        await db.commit()
        print("All operations completed.")

if __name__ == "__main__":
    asyncio.run(main())
