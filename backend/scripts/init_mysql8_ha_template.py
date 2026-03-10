import asyncio
import sys
import os

# 将 backend 目录添加到路径以便导入 app 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppTemplate, AppType
from sqlalchemy import select

# MySQL 8 HA Docker Compose 模板 (基于 Bitnami 镜像)
# 支持 Master-Slave 复制模式
# 变量说明：
# - role: 通过部署时的角色选择决定 ('master' 或 'slave')
# - server_id: 系统自动分配的唯一服务器ID，用作 MySQL server-id
# - master_ip: 用户在配置中手动填写的 Master IP
# - instance_id: 应用实例 ID，用于生成唯一的容器名称
MYSQL_TEMPLATE = """services:
  mysql:
    image: {{ image }}
    container_name: mysql-{{ instance_id }}-{{ server_id }}
    environment:
      # 基础认证配置
      - MYSQL_ROOT_PASSWORD={{ root_password }}
      - MYSQL_REPLICATION_USER={{ repl_user }}
      - MYSQL_REPLICATION_PASSWORD={{ repl_password }}
      
      # 端口配置
      - MYSQL_PORT_NUMBER={{ port }}
      
      # 复制配置
      # 使用系统分配的 server_id (int) 作为 MySQL Server ID，确保唯一性
      - MYSQL_SERVER_ID={{ server_id }}
      
      {% if role and 'master' in role %}
      - MYSQL_REPLICATION_MODE=master
      {% else %}
      - MYSQL_REPLICATION_MODE=slave
      - MYSQL_MASTER_HOST={{ master_ip }}
      - MYSQL_MASTER_PORT_NUMBER={{ master_port | default(port) }}
      - MYSQL_MASTER_ROOT_PASSWORD={{ root_password }}
      {% endif %}
      
      # 允许空密码 (不建议，但在模板中我们强制要求了密码)
      - ALLOW_EMPTY_PASSWORD=no
    
    ports:
      - {{ port }}:{{ port }}
    
    volumes:
      - {{ data_path }}:/bitnami/mysql/data
    
    restart: always
"""

CONFIG_SCHEMA = {
  "type": "object",
  "x-roles": ["master", "slave"],
  "properties": {
    "image": {
      "type": "string",
      "title": "Image",
      "default": "bitnami/mysql:8.0",
      "description": "Docker 镜像地址 (如拉取失败可修改为私有仓库地址)"
    },
    "port": {
      "type": "integer",
      "title": "Service Port",
      "default": 3306,
      "description": "MySQL 服务端口 (本机监听端口)"
    },
    "master_port": {
      "type": "integer",
      "title": "Master Port",
      "default": 3306,
      "description": "Master 节点端口 (Slave 模式下连接 Master 使用)"
    },
    "root_password": {
      "type": "string",
      "title": "Root Password",
      "default": "mysql_root_123",
      "description": "Root 用户密码 (集群内需保持一致)"
    },
    "repl_user": {
      "type": "string",
      "title": "Replication User",
      "default": "repl_user",
      "description": "复制专用用户名"
    },
    "repl_password": {
      "type": "string",
      "title": "Replication Password",
      "default": "repl_pass_123",
      "description": "复制专用用户密码"
    },
    "master_ip": {
      "type": "string",
      "title": "Master IP",
      "description": "Master 节点 IP 地址 (部署 Slave 节点时必填)"
    },
    "data_path": {
      "type": "string",
      "title": "Data Path",
      "default": "/data/mysql8",
      "description": "宿主机数据存储路径"
    }
  },
  "required": ["root_password", "repl_user", "repl_password", "data_path"]
}

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(AppTemplate).where(AppTemplate.name == "mysql-8-ha")
        result = await db.execute(stmt)
        existing_template = result.scalar_one_or_none()

        if existing_template:
            print("Template 'mysql-8-ha' exists. Updating...")
            existing_template.deploy_template = MYSQL_TEMPLATE
            existing_template.version = "8.0"
            existing_template.description = "MySQL 8.0 High Availability (Master-Slave). 基于 Bitnami 镜像，支持一键部署主从复制集群。部署时请注意选择正确的角色(master/slave)并填写 Master IP。"
            existing_template.config_schema = CONFIG_SCHEMA
            existing_template.default_config = {
                "image": "bitnami/mysql:8.0",
                "port": 3306,
                "master_port": 3306,
                "root_password": "mysql_root_123",
                "repl_user": "repl_user",
                "repl_password": "repl_pass_123",
                "data_path": "/data/mysql8"
            }
            await db.commit()
            print("Template 'mysql-8-ha' updated.")
            return

        template = AppTemplate(
            name="mysql-8-ha",
            display_name="MySQL 8 HA",
            version="8.0",
            description="MySQL 8.0 High Availability (Master-Slave). 基于 Bitnami 镜像，支持一键部署主从复制集群。部署时请注意选择正确的角色(master/slave)并填写 Master IP。",
            icon="https://www.mysql.com/common/logos/logo-mysql-170x115.png",
            app_type=AppType.docker_compose,
            config_schema=CONFIG_SCHEMA,
            default_config={
                "image": "bitnami/mysql:8.0",
                "port": 3306,
                "master_port": 3306,
                "root_password": "mysql_root_123",
                "repl_user": "repl_user",
                "repl_password": "repl_pass_123",
                "data_path": "/data/mysql8"
            },
            deploy_template=MYSQL_TEMPLATE,
            is_system=True
        )
        db.add(template)
        await db.commit()
        print("Template 'mysql-8-ha' created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
