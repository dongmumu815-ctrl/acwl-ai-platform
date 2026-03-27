import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, engine
from app.models.application import AppTemplate, AppType
from sqlalchemy import select

ZOOKEEPER_TEMPLATE = """version: '3'
services:
  zookeeper:
    image: bitnami/zookeeper:{{ version | default('latest') }}
    container_name: zookeeper-{{ ZOO_MY_ID | default(server_id) }}
    hostname: zk-{{ ZOO_MY_ID | default(server_id) }}
    network_mode: "host"
    restart: always
    user: root
    environment:
      - ZOO_SERVER_ID={{ ZOO_MY_ID }}
      - ZOO_SERVERS={{ ZOO_SERVERS }}
      - ALLOW_ANONYMOUS_LOGIN=yes
      - ZOO_CLIENT_PORT=2181
      - ZOO_PORT_NUMBER=2181
      - ZOO_LISTEN_ALLIPS_ENABLED=yes
      - ZOO_ENABLE_ADMIN_SERVER=yes
      - ZOO_ADMIN_SERVER_PORT_NUMBER=8080
      - ZOO_4LW_COMMANDS_WHITELIST=*
      - ZOO_TICK_TIME=2000
      - ZOO_INIT_LIMIT=5
      - ZOO_SYNC_LIMIT=2
      - ZOO_MAX_CLIENT_CNXNS=60
      - ZOO_HEAP_SIZE={{ heap_size | default('1024') }}
    volumes:
      - /data/zookeeper/data:/bitnami/zookeeper/data
      - /data/zookeeper/log:/bitnami/zookeeper/datalog
    deploy:
      resources:
        limits:
          memory: {{ memory_limit | default('2g') }}
"""

CONFIG_SCHEMA = {
  "type": "object",
  "x-roles": ["leader", "follower", "observer"],
  "properties": {
    "ZOO_SERVERS": {
      "type": "string",
      "title": "Zookeeper Servers",
      "description": "Zookeeper 集群服务器列表配置 (自动生成)"
    },
    "ZOO_MY_ID": {
      "type": "integer",
      "title": "My ID",
      "description": "当前节点的 ID (自动生成)"
    },
    "data_root_path": {
      "type": "string",
      "title": "Data Root Path",
      "default": "/data/zookeeper",
      "description": "宿主机数据存储根目录"
    },
    "heap_size": {
      "type": "string",
      "title": "Java Heap Size (MB)",
      "default": "1024",
      "description": "Zookeeper JVM 堆内存大小 (MB)"
    },
    "memory_limit": {
      "type": "string",
      "title": "Container Memory Limit",
      "default": "2g",
      "description": "容器内存硬限制"
    }
  }
}

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(AppTemplate).where(AppTemplate.name == "zookeeper")
        result = await db.execute(stmt)
        existing_template = result.scalar_one_or_none()

        if existing_template:
            print("Template 'zookeeper' exists. Updating...")
            existing_template.deploy_template = ZOOKEEPER_TEMPLATE
            existing_template.version = "3.8"
            existing_template.description = "Apache Zookeeper 高可用集群部署模板，基于 Bitnami 镜像。"
            existing_template.config_schema = CONFIG_SCHEMA
            existing_template.default_config = {
                "data_root_path": "/data/zookeeper",
                "heap_size": "1024",
                "memory_limit": "2g"
            }
            await db.commit()
            print("Template 'zookeeper' updated successfully.")
        else:
            template = AppTemplate(
                name="zookeeper",
                display_name="Zookeeper Cluster",
                version="3.8",
                description="Apache Zookeeper 高可用集群部署模板，基于 Bitnami 镜像。",
                app_type=AppType.docker_compose,
                config_schema=CONFIG_SCHEMA,
                default_config={
                    "data_root_path": "/data/zookeeper",
                    "heap_size": "1024",
                    "memory_limit": "2g"
                },
                deploy_template=ZOOKEEPER_TEMPLATE,
                is_system=True
            )
            db.add(template)
            await db.commit()
            print("Template 'zookeeper' created successfully.")
    
    # 释放数据库引擎连接，避免由于事件循环关闭导致 aiomysql 报错
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
