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

async def seed_postgres_template():
    async with AsyncSessionLocal() as session:
        # Check if template exists
        stmt = select(AppTemplate).where(AppTemplate.name == "postgresql")
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        template_data = {
            "name": "postgresql",
            "display_name": "PostgreSQL",
            "version": "16",
            "description": "The World's Most Advanced Open Source Relational Database (Single Instance)",
            "icon": "https://upload.wikimedia.org/wikipedia/commons/2/29/Postgresql_elephant.svg",
            "app_type": AppType.docker_compose,
            "is_system": True,
            "deploy_template": """version: '3'

services:
  postgresql:
    # 使用华为云镜像加速 (解决 docker.io 403 问题)
    image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/bitnami/postgresql:16
    # 修复 Permission denied 问题
    user: root
    ports:
      - "{{ port | default(5432) }}:5432"
    environment:
      - POSTGRESQL_USERNAME={{ username | default('postgres') }}
      - POSTGRESQL_PASSWORD={{ password }}
      - POSTGRESQL_DATABASE={{ database | default('postgres') }}
      # Optional: Tune PostgreSQL memory usage
      # - POSTGRESQL_SHARED_BUFFERS={{ shared_buffers | default('128MB') }}
    volumes:
      - "{{ data_path | default('/data/postgresql') }}:/bitnami/postgresql"
    
    # Increase shared memory size for better performance
    shm_size: '{{ shm_size | default("1g") }}'
    
    deploy:
      resources:
        limits:
          memory: {{ mem_limit | default('8G') }}
          cpus: '{{ cpu_limit | default("4.0") }}'
    
    restart: always
""",
            "config_schema": {
                "type": "object",
                "required": ["password"],
                "properties": {
                    "password": {
                        "type": "string",
                        "title": "管理员密码",
                        "description": "postgres 用户的密码 (系统会自动生成，也可手动修改)"
                    },
                    "mem_limit": {
                        "type": "string",
                        "title": "内存限制",
                        "default": "8G",
                        "description": "容器最大内存使用量 (推荐: 4G, 8G, 16G)"
                    },
                    "cpu_limit": {
                        "type": "string",
                        "title": "CPU限制",
                        "default": "4.0",
                        "description": "容器最大CPU核心数 (推荐: 2.0, 4.0, 8.0)"
                    },
                    "username": {
                        "type": "string",
                        "title": "用户名",
                        "default": "postgres"
                    },
                    "database": {
                        "type": "string",
                        "title": "数据库名",
                        "default": "postgres"
                    },
                    "port": {
                        "type": "integer",
                        "title": "端口",
                        "default": 5432
                    },
                    "data_path": {
                        "type": "string",
                        "title": "数据路径",
                        "default": "/data/postgresql"
                    },
                    "shm_size": {
                        "type": "string",
                        "title": "共享内存(shm_size)",
                        "default": "1g",
                        "description": "Docker共享内存大小，建议设置为内存的 1/4 左右"
                    }
                }
            },
            "default_config": {
                "username": "postgres",
                "database": "postgres",
                "port": 5432,
                "data_path": "/data/postgresql",
                "mem_limit": "8G",
                "cpu_limit": "4.0",
                "shm_size": "1g"
            }
        }

        if existing:
            print("Updating existing PostgreSQL template...")
            for key, value in template_data.items():
                setattr(existing, key, value)
        else:
            print("Creating new PostgreSQL template...")
            new_template = AppTemplate(**template_data)
            session.add(new_template)
        
        await session.commit()
        print("Done!")

if __name__ == "__main__":
    # Windows Selector Event Loop Policy for async
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(seed_postgres_template())
