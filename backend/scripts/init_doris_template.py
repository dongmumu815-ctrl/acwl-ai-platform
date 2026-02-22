import asyncio
import sys
import os

# 将 backend 目录添加到路径以便导入 app 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppTemplate, AppType
from sqlalchemy import select

# Doris Docker Compose 模板
# 更新为 4.0.3 版本，增加数据目录配置，支持多角色混部
# 增加内存限制配置 (FE Heap, FE Container Limit, BE Container Limit)
DORIS_TEMPLATE = """version: '3'
services:
  {% set roles = (role or '').split(',') %}

  {% if 'fe-master' in roles %}
  doris-fe:
    image: apache/doris:fe-4.0.3-slim
    container_name: doris-fe
    hostname: {{ role | replace(',', '-') }}-{{ server_id }}
    network_mode: "host"
    restart: always
    environment:
      - FE_SERVERS={{ fe_servers }}
      # 使用后端生成的 fe_id_value (server_id)，避免 ID 冲突
      - FE_ID={{ fe_id_value }}
      - FE_MASTER_IP={{ fe_master_ip }}
      - PRIORITY_NETWORKS={{ priority_networks }}
      - DORIS_FE_PROPERTIES=priority_networks={{ priority_networks }}
      - JAVA_OPTS=-Xmx{{ fe_memory }} -Xms{{ fe_memory }}
      - JAVA_OPTS_FOR_JDK_17=-Xmx{{ fe_memory }} -Xms{{ fe_memory }}
    volumes:
      - {{ data_root_path }}/fe/doris-meta:/opt/apache-doris/fe/doris-meta
      - {{ data_root_path }}/fe/log:/opt/apache-doris/fe/log
      - {{ data_root_path }}/fe/conf:/opt/apache-doris/fe/conf
      - {{ data_root_path }}/backup:/opt/apache-doris/backup
    deploy:
      resources:
        limits:
          memory: {{ fe_memory_limit }}
  {% endif %}

  {% if 'fe-follower' in roles or 'fe-observer' in roles %}
  doris-fe:
    image: apache/doris:fe-4.0.3-slim
    container_name: doris-fe
    hostname: {{ role | replace(',', '-') }}-{{ server_id }}
    network_mode: "host"
    restart: always
    environment:
      - PRIORITY_NETWORKS={{ priority_networks }}
      - FE_SERVERS={{ fe_servers }}
      - FE_MASTER_IP={{ fe_master_ip }}
      # 使用后端生成的 fe_id_value (server_id)，避免 ID 冲突
      - FE_ID={{ fe_id_value }}
      - FE_ROLE=follower
      - JAVA_OPTS=-Xmx{{ fe_memory }} -Xms{{ fe_memory }}
      - JAVA_OPTS_FOR_JDK_17=-Xmx{{ fe_memory }} -Xms{{ fe_memory }}
    volumes:
      - {{ data_root_path }}/fe/doris-meta:/opt/apache-doris/fe/doris-meta
      - {{ data_root_path }}/fe/log:/opt/apache-doris/fe/log
      - {{ data_root_path }}/fe/conf:/opt/apache-doris/fe/conf
      - {{ data_root_path }}/backup:/opt/apache-doris/backup
    deploy:
      resources:
        limits:
          memory: {{ fe_memory_limit }}
  {% endif %}

  {% if 'be' in roles %}
  doris-be:
    image: apache/doris:be-4.0.3-slim
    container_name: doris-be
    hostname: be-{{ server_id }}
    network_mode: "host"
    restart: always
    privileged: true
    environment:
      - PRIORITY_NETWORKS={{ priority_networks }}
      - BE_ADDR={{ current_ip }}:9050
      - FE_SERVERS={{ fe_servers }}
      - FE_MASTER_IP={{ fe_master_ip }}
      - BE_PORT=9060
      - WEBSERVER_PORT=8040
      - HEARTBEAT_SERVICE_PORT=9050
      - BRPC_PORT=8060
    volumes:
      - {{ data_root_path }}/be/storage:/opt/apache-doris/be/storage
      - {{ data_root_path }}/be/log:/opt/apache-doris/be/log
      - {{ data_root_path }}/be/conf:/opt/apache-doris/be/conf
      - {{ data_root_path }}/backup:/opt/apache-doris/backup
    deploy:
      resources:
        limits:
          memory: {{ be_memory_limit }}
  {% endif %}
"""

CONFIG_SCHEMA = {
  "type": "object",
  "x-roles": ["fe-master", "fe-follower", "be"],
  "properties": {
    "fe_master_ip": {
      "type": "string",
      "title": "Master FE IP",
      "description": "Master FE 节点的内网 IP，用于集群发现"
    },
    "priority_networks": {
      "type": "string",
      "title": "Priority Networks (CIDR)",
      "default": "10.20.0.0/16",
      "description": "Doris 节点通信使用的网段"
    },
    "data_root_path": {
      "type": "string",
      "title": "Data Root Path",
      "default": "/data/doris",
      "description": "宿主机数据存储根目录"
    },
    "fe_memory": {
      "type": "string",
      "title": "FE Java Heap",
      "default": "32g",
      "description": "FE 节点的 Java 堆内存大小 (例如 8g, 16g). 建议设置为系统内存的 1/4 - 1/2."
    },
    "fe_memory_limit": {
      "type": "string",
      "title": "FE Container Limit",
      "default": "40g",
      "description": "FE 容器的最大内存限制. 建议比 Java Heap 大 2-4GB 用于非堆内存开销."
    },
    "be_memory_limit": {
      "type": "string",
      "title": "BE Container Limit",
      "default": "180g",
      "description": "BE 容器的内存硬限制 (Docker memory limit)。建议统一配置，以混部节点的可用内存为准（例如 256G 机器混部 FE 后剩 200G 左右，扣除系统预留设为 180G）。"
    }
  },
  "required": ["fe_master_ip"]
}

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(AppTemplate).where(AppTemplate.name == "apache-doris")
        result = await db.execute(stmt)
        existing_template = result.scalar_one_or_none()

        if existing_template:
            print("Template 'apache-doris' exists. Updating...")
            existing_template.deploy_template = DORIS_TEMPLATE
            existing_template.version = "4.0.3"
            existing_template.description = "Apache Doris 实时数据仓库 (集群版 4.0.3). 支持多角色混合部署. 已增强内存配置(FE Heap/Container, BE Container)及自动系统参数优化."
            existing_template.config_schema = CONFIG_SCHEMA
            existing_template.default_config = {
                "priority_networks": "10.20.0.0/16",
                "data_root_path": "/data/doris",
                "fe_memory": "32g",
                "fe_memory_limit": "40g",
                "be_memory_limit": "180g"
            }
            await db.commit()
            print("Template 'apache-doris' updated to version 4.0.3 with improved schema.")
            return

        template = AppTemplate(
            name="apache-doris",
            display_name="Apache Doris (Cluster)",
            version="4.0.3",
            description="Apache Doris 实时数据仓库 (集群版 4.0.3). 支持多角色混合部署. 已增强内存配置(FE Heap/Container, BE Container)及自动系统参数优化.",
            app_type=AppType.docker_compose,
            config_schema=CONFIG_SCHEMA,
            default_config={
                "priority_networks": "10.20.0.0/16",
                "data_root_path": "/data/doris",
                "fe_memory": "32g",
                "fe_memory_limit": "40g",
                "be_memory_limit": "180g"
            },
            deploy_template=DORIS_TEMPLATE,
            is_system=True
        )
        db.add(template)
        await db.commit()
        print("Template 'apache-doris' created successfully.")

if __name__ == "__main__":
    asyncio.run(main())