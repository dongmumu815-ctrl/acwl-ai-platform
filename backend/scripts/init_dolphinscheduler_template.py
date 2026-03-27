import asyncio
import sys
import os

# Add backend directory to path to import app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, engine
from app.models.application import AppTemplate, AppType
from sqlalchemy import select

DOLPHINSCHEDULER_TEMPLATE = """version: '3.8'

x-common-env: &common-env
  DATABASE: postgresql
  SPRING_DATASOURCE_URL: "{{ DB_URL }}"
  SPRING_DATASOURCE_USERNAME: "{{ DB_USERNAME }}"
  SPRING_DATASOURCE_PASSWORD: "{{ DB_PASSWORD }}"
  REGISTRY_TYPE: zookeeper
  REGISTRY_ZOOKEEPER_CONNECT_STRING: "{{ ZK_QUORUM }}"
  # DolphinScheduler 3.4+ IP Override configuration
  DOCKER_INSTANCE_IP: "{{ current_ip }}"
  HOST: "{{ current_ip }}"
  SPRING_APPLICATION_JSON: '{"worker":{"worker-address":"{{ current_ip }}:1234"}, "master":{"master-address":"{{ current_ip }}:5678"}, "api":{"api-address":"{{ current_ip }}:12345"}}'
  SPRING_CLOUD_INETUTILS_PREFERRED_NETWORKS: '^{{ current_ip.split(".")[0] }}\.{{ current_ip.split(".")[1] }}\..*'
  SPRING_CLOUD_INETUTILS_USE_ONLY_SITE_LOCAL_INTERFACES: "true"
  SPRING_CLOUD_INETUTILS_IGNORED_INTERFACES: "docker0,veth.*,flannel.*,br-.*"

services:
{% if 'master' in role or role == 'default' or role == '' %}
  master:
    image: "10.20.1.204:5000/uat/dolphinscheduler-master:{{ MASTER_VERSION }}"
    command: >
      bash -c "export DOLPHIN_SCHEDULER_NETWORK_INTERFACE_PREFERRED=$$(ip -o -4 addr show | grep '{{ current_ip }}' | awk '{print $$2}' | head -n 1) && bash master-server/bin/start.sh"
    network_mode: "host"
    environment:
      <<: *common-env
      SPRING_JACKSON_TIME_ZONE: "GMT+8"
{% endif %}

{% if 'worker' in role or role == 'default' or role == '' %}
  worker:
    image: "10.20.1.204:5000/uat/dolphinscheduler-worker:{{ WORKER_VERSION }}"
    command: >
      bash -c "export DOLPHIN_SCHEDULER_NETWORK_INTERFACE_PREFERRED=$$(ip -o -4 addr show | grep '{{ current_ip }}' | awk '{print $$2}' | head -n 1) && bash worker-server/bin/start.sh"
    network_mode: "host"
    environment:
      <<: *common-env
      SPRING_JACKSON_TIME_ZONE: "GMT+8"
{% endif %}

{% if 'api' in role or role == 'default' or role == '' %}
  api:
    image: "10.20.1.204:5000/uat/dolphinscheduler-api:{{ API_VERSION }}"
    command: >
      bash -c "export DOLPHIN_SCHEDULER_NETWORK_INTERFACE_PREFERRED=$$(ip -o -4 addr show | grep '{{ current_ip }}' | awk '{print $$2}' | head -n 1) && bash api-server/bin/start.sh"
    network_mode: "host"
    environment:
      <<: *common-env
      SPRING_JACKSON_TIME_ZONE: "GMT+8"
{% endif %}

{% if 'alert' in role or role == 'default' or role == '' %}
  alert:
    image: "10.20.1.204:5000/uat/dolphinscheduler-alert:{{ ALERT_VERSION }}"
    command: >
      bash -c "export DOLPHIN_SCHEDULER_NETWORK_INTERFACE_PREFERRED=$$(ip -o -4 addr show | grep '{{ current_ip }}' | awk '{print $$2}' | head -n 1) && bash alert-server/bin/start.sh"
    network_mode: "host"
    environment:
      <<: *common-env
      SPRING_JACKSON_TIME_ZONE: "GMT+8"
{% endif %}
"""

CONFIG_SCHEMA = {
  "type": "object",
  "x-roles": ["master", "worker", "api", "alert"],
  "properties": {
    "MASTER_VERSION": {
      "type": "string",
      "title": "Master Version",
      "default": "3.4.1-prod"
    },
    "WORKER_VERSION": {
      "type": "string",
      "title": "Worker Version",
      "default": "3.4.1-prod"
    },
    "API_VERSION": {
      "type": "string",
      "title": "API Version",
      "default": "3.4.1-prod"
    },
    "ALERT_VERSION": {
      "type": "string",
      "title": "Alert Version",
      "default": "3.4.1-prod"
    },
    "DB_URL": {
      "type": "string",
      "title": "Database URL",
      "description": "e.g., jdbc:postgresql://10.20.1.213:5432/dolphinscheduler",
      "default": "jdbc:postgresql://10.20.1.213:5432/dolphinscheduler"
    },
    "DB_USERNAME": {
      "type": "string",
      "title": "Database Username",
      "default": "postgres"
    },
    "DB_PASSWORD": {
      "type": "string",
      "title": "Database Password",
      "default": "nxs1Fs3DI9RhYiov"
    },
    "ZK_QUORUM": {
      "type": "string",
      "title": "Zookeeper Quorum",
      "description": "e.g., 10.20.1.210:2181,10.20.1.211:2181,10.20.1.212:2181",
      "default": "10.20.1.210:2181,10.20.1.211:2181,10.20.1.212:2181"
    }
  },
  "required": ["MASTER_VERSION", "WORKER_VERSION", "API_VERSION", "ALERT_VERSION", "DB_URL", "DB_USERNAME", "DB_PASSWORD", "ZK_QUORUM"]
}

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(AppTemplate).where(AppTemplate.name == "dolphinscheduler")
        result = await db.execute(stmt)
        existing_template = result.scalar_one_or_none()

        if existing_template:
            print("Template 'dolphinscheduler' exists. Updating...")
            existing_template.deploy_template = DOLPHINSCHEDULER_TEMPLATE
            existing_template.version = "3.4.1-prod"
            existing_template.description = "A distributed and easy-to-expand visual DAG workflow scheduling system."
            existing_template.config_schema = CONFIG_SCHEMA
            existing_template.default_config = {
                "MASTER_VERSION": "3.4.1-prod",
                "WORKER_VERSION": "3.4.1-prod",
                "API_VERSION": "3.4.1-prod",
                "ALERT_VERSION": "3.4.1-prod",
                "DB_URL": "jdbc:postgresql://10.20.1.213:5432/dolphinscheduler",
                "DB_USERNAME": "postgres",
                "DB_PASSWORD": "nxs1Fs3DI9RhYiov",
                "ZK_QUORUM": "10.20.1.210:2181,10.20.1.211:2181,10.20.1.212:2181"
            }
            existing_template.icon = "https://dolphinscheduler.apache.org/img/hlogo_colorful.svg"
            await db.commit()
            print("Template 'dolphinscheduler' updated.")
        else:
            template = AppTemplate(
                name="dolphinscheduler",
                display_name="Apache DolphinScheduler",
                version="3.4.1-prod",
                description="A distributed and easy-to-expand visual DAG workflow scheduling system.",
                app_type=AppType.docker_compose,
                config_schema=CONFIG_SCHEMA,
                default_config={
                    "MASTER_VERSION": "3.4.1-prod",
                    "WORKER_VERSION": "3.4.1-prod",
                    "API_VERSION": "3.4.1-prod",
                    "ALERT_VERSION": "3.4.1-prod",
                    "DB_URL": "jdbc:postgresql://10.20.1.213:5432/dolphinscheduler",
                    "DB_USERNAME": "postgres",
                    "DB_PASSWORD": "nxs1Fs3DI9RhYiov",
                    "ZK_QUORUM": "10.20.1.210:2181,10.20.1.211:2181,10.20.1.212:2181"
                },
                deploy_template=DOLPHINSCHEDULER_TEMPLATE,
                is_system=True,
                icon="https://dolphinscheduler.apache.org/img/hlogo_colorful.svg"
            )
            db.add(template)
            await db.commit()
            print("Template 'dolphinscheduler' created successfully.")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
