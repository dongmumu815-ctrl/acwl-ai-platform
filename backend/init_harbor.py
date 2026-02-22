import asyncio
import logging
import sys
import os

# 添加 backend 目录到 sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.application import AppTemplate, AppType
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_harbor_template():
    async with AsyncSessionLocal() as session:
        # 检查是否已存在
        result = await session.execute(select(AppTemplate).where(AppTemplate.name == "Harbor"))
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info("Harbor 模板已存在，正在删除旧模板以进行更新...")
            await session.delete(existing)
            await session.flush()

        # 创建新模板
        harbor_template = AppTemplate(
            name="Harbor",
            display_name="Harbor 镜像仓库",
            version="2.8.0",
            description="Harbor 是一个开源的云原生镜像仓库，用于存储、签名和扫描内容。",
            icon="https://goharbor.io/img/logos/harbor-icon-color.png",
            app_type=AppType.docker_compose,
            is_system=True,
            config_schema={
                "type": "object",
                "properties": {
                    "http_port": {
                        "type": "integer",
                        "default": 80,
                        "title": "HTTP端口",
                        "description": "Harbor 访问端口"
                    },
                    "admin_password": {
                        "type": "string",
                        "default": "Harbor12345",
                        "title": "管理员密码",
                        "description": "初始密码，建议部署后修改"
                    },
                     "cpu_limit": {
                        "type": "string", 
                        "default": "2", 
                        "title": "CPU限制 (核心数)",
                        "enum": ["1", "2", "4", "8"],
                        "description": "容器可使用的最大CPU核心数"
                    },
                    "mem_limit": {
                        "type": "string", 
                        "default": "4G", 
                        "title": "内存限制",
                        "enum": ["2G", "4G", "8G", "16G"],
                        "description": "容器可使用的最大内存"
                    },
                    "data_volume": {
                        "type": "string",
                        "default": "/data/harbor",
                        "title": "数据存储路径",
                        "description": "宿主机挂载路径"
                    }
                },
                "required": ["http_port", "admin_password", "data_volume"]
            },
            default_config={
                "http_port": 80,
                "admin_password": "Harbor12345",
                "cpu_limit": "2",
                "mem_limit": "4G",
                "data_volume": "/data/harbor"
            },
            deploy_template="""version: '3'
services:
  harbor:
    image: goharbor/harbor-portal:v2.8.0
    container_name: harbor
    restart: always
    ports:
      - "{{ http_port }}:80"
    environment:
      - HARBOR_ADMIN_PASSWORD={{ admin_password }}
    volumes:
      - {{ data_volume }}:/data
    deploy:
      resources:
        limits:
          cpus: '{{ cpu_limit }}'
          memory: {{ mem_limit }}
"""
        )
        
        session.add(harbor_template)
        await session.commit()
        logger.info("Harbor 模板初始化/更新成功")

if __name__ == "__main__":
    asyncio.run(init_harbor_template())
