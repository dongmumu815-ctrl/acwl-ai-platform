import asyncio
import sys
import os

# 将 backend 目录添加到路径以便导入 app 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppTemplate, AppType
from sqlalchemy import select

# Elasticsearch 8.x Docker Compose 模板
# 支持单机及集群模式 (Initial Master / Join Node)
# 默认开启 X-Pack Security (密码认证)，禁用 SSL (HTTP/Transport) 以简化内部网络部署
ES8_TEMPLATE = """version: '3'
services:
  elasticsearch:
    image: elasticsearch:8.13.4
    container_name: elasticsearch-8-{{ server_id }}
    environment:
      - node.name=es-8-{{ server_id }}
      - cluster.name={{ cluster_name }}
      - network.host=0.0.0.0
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS={{ java_opts }}"
      - ELASTIC_PASSWORD={{ es_password }}
      
      # 角色与发现配置
      {% if role == 'initial_master' %}
      # 初始主节点: 设置自身为初始 Master 列表，用于引导集群
      - cluster.initial_master_nodes=es-8-{{ server_id }}
      {% else %}
      # 加入节点: 指定 Master IP 进行发现，严禁设置 initial_master_nodes
      - discovery.seed_hosts={{ master_ip }}
      {% endif %}

      # 安全配置 (禁用 SSL 以简化 HTTP/Transport 连接)
      - xpack.security.enabled=true
      - xpack.security.http.ssl.enabled=false
      - xpack.security.transport.ssl.enabled=false
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - {{ data_path }}:/usr/share/elasticsearch/data
    ports:
      - {{ http_port }}:9200
      - {{ transport_port }}:9300
    restart: always
"""

CONFIG_SCHEMA = {
  "type": "object",
  "properties": {
    "cluster_name": {
      "type": "string",
      "title": "Cluster Name",
      "default": "acwl-es-cluster",
      "description": "集群名称，所有节点必须一致"
    },
    "role": {
      "type": "string",
      "title": "Node Role",
      "default": "initial_master",
      "enum": ["initial_master", "join_node"],
      "description": "节点角色: 'initial_master' (首个节点/引导节点) 或 'join_node' (加入现有集群)"
    },
    "master_ip": {
      "type": "string",
      "title": "Master IP",
      "description": "Master 节点的 IP 地址 (仅 'join_node' 需要填写)"
    },
    "http_port": {
      "type": "integer",
      "title": "HTTP Port",
      "default": 9200,
      "description": "Elasticsearch HTTP 服务端口"
    },
    "transport_port": {
      "type": "integer",
      "title": "Transport Port",
      "default": 9300,
      "description": "Elasticsearch 节点间通信端口 (TCP)"
    },
    "es_password": {
      "type": "string",
      "title": "Elastic Password",
      "default": "elastic123456",
      "description": "elastic 用户密码 (集群内所有节点建议保持一致)"
    },
    "java_opts": {
      "type": "string",
      "title": "Java OPTS",
      "default": "-Xms2g -Xmx2g",
      "description": "JVM 堆内存配置 (ES 8 建议至少 2G)"
    },
    "data_path": {
      "type": "string",
      "title": "Data Path",
      "default": "/data/elasticsearch-8",
      "description": "宿主机数据存储路径"
    }
  },
  "required": ["cluster_name", "role", "http_port", "transport_port", "es_password", "data_path"]
}

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(AppTemplate).where(AppTemplate.name == "elasticsearch-8")
        result = await db.execute(stmt)
        existing_template = result.scalar_one_or_none()

        if existing_template:
            print("Template 'elasticsearch-8' exists. Updating...")
            existing_template.deploy_template = ES8_TEMPLATE
            existing_template.version = "8.13.4"
            existing_template.description = "Elasticsearch 8.13.4 (Cluster Ready). 支持单机或集群部署。默认开启 X-Pack 认证，禁用 SSL。集群模式下请确保 Cluster Name 一致且网络互通。"
            existing_template.config_schema = CONFIG_SCHEMA
            existing_template.default_config = {
                "cluster_name": "acwl-es-cluster",
                "role": "initial_master",
                "http_port": 9200,
                "transport_port": 9300,
                "es_password": "elastic123456",
                "java_opts": "-Xms2g -Xmx2g",
                "data_path": "/data/elasticsearch-8"
            }
            await db.commit()
            print("Template 'elasticsearch-8' updated.")
            return

        template = AppTemplate(
            name="elasticsearch-8",
            display_name="Elasticsearch 8",
            version="8.13.4",
            description="Elasticsearch 8.13.4 (Cluster Ready). 支持单机或集群部署。默认开启 X-Pack 认证，禁用 SSL。集群模式下请确保 Cluster Name 一致且网络互通。",
            icon="https://static-www.elastic.co/v3/assets/bltefdd0b53724fa2ce/blt36f2c55b9ce15d1d/5ea8c62ce24a911ec4872407/brand-elasticsearch-220x130.svg",
            app_type=AppType.docker_compose,
            config_schema=CONFIG_SCHEMA,
            default_config={
                "cluster_name": "acwl-es-cluster",
                "role": "initial_master",
                "http_port": 9200,
                "transport_port": 9300,
                "es_password": "elastic123456",
                "java_opts": "-Xms2g -Xmx2g",
                "data_path": "/data/elasticsearch-8"
            },
            deploy_template=ES8_TEMPLATE,
            is_system=True
        )
        db.add(template)
        await db.commit()
        print("Template 'elasticsearch-8' created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
