import asyncio
import sys
import os

# Add backend directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from app.core.database import AsyncSessionLocal
from app.models.application import AppTemplate, AppType
from sqlalchemy import select

async def seed_redis_template():
    async with AsyncSessionLocal() as session:
        # Check if template exists
        stmt = select(AppTemplate).where(AppTemplate.name == "redis")
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        template_data = {
            "name": "redis",
            "display_name": "Redis",
            "version": "7.2",
            "description": "The open source, in-memory data store used by millions of developers as a database, cache, streaming engine, and message broker.",
            "icon": "https://upload.wikimedia.org/wikipedia/en/6/6b/Redis_Logo.svg",
            "app_type": AppType.docker_compose,
            "is_system": True,
            "deploy_template": """version: '3'

services:
  redis:
    # 尝试使用 AWS 公共镜像 (华为云镜像可能不稳定)
    image: public.ecr.aws/bitnami/redis:7.2
    # 修复 Permission denied 问题
    user: root
    ports:
      - "{{ port | default(6379) }}:6379"
    environment:
      - REDIS_PASSWORD={{ password }}
      # Optional: Disable AOF if you don't need persistence
      - REDIS_AOF_ENABLED={{ aof_enabled | default('yes') }}
    volumes:
      - "{{ data_path | default('/data/redis') }}:/bitnami/redis/data"
    
    deploy:
      resources:
        limits:
          memory: {{ mem_limit | default('1G') }}
          cpus: '{{ cpu_limit | default("1.0") }}'
    
    restart: always
""",
            "config_schema": {
                "type": "object",
                "required": ["password"],
                "properties": {
                    "password": {
                        "type": "string",
                        "title": "访问密码",
                        "description": "Redis 认证密码 (系统会自动生成，也可手动修改)"
                    },
                    "port": {
                        "type": "integer",
                        "title": "端口",
                        "default": 6379
                    },
                    "data_path": {
                        "type": "string",
                        "title": "数据路径",
                        "default": "/data/redis"
                    },
                    "mem_limit": {
                        "type": "string",
                        "title": "内存限制",
                        "default": "1G",
                        "description": "容器最大内存使用量 (推荐: 512M, 1G, 4G)"
                    },
                    "cpu_limit": {
                        "type": "string",
                        "title": "CPU限制",
                        "default": "1.0",
                        "description": "容器最大CPU核心数 (推荐: 0.5, 1.0, 2.0)"
                    },
                    "aof_enabled": {
                        "type": "string",
                        "title": "开启AOF持久化",
                        "default": "yes",
                        "enum": ["yes", "no"],
                        "description": "是否开启 AOF 持久化 (建议开启以保证数据安全)"
                    }
                }
            },
            "default_config": {
                "port": 6379,
                "data_path": "/data/redis",
                "mem_limit": "1G",
                "cpu_limit": "1.0",
                "aof_enabled": "yes"
            }
        }

        if existing:
            print("Updating existing Redis template...")
            for key, value in template_data.items():
                setattr(existing, key, value)
        else:
            print("Creating new Redis template...")
            new_template = AppTemplate(**template_data)
            session.add(new_template)
        
        await session.commit()
        print("Done!")

if __name__ == "__main__":
    # Windows Selector Event Loop Policy for async
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(seed_redis_template())
