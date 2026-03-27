import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, engine
from app.models.application import AppTemplate
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        stmt = select(AppTemplate).where(AppTemplate.name == 'minio')
        res = await db.execute(stmt)
        t = res.scalar_one_or_none()
        
        if t:
            new_template = """version: '3.8'

services:
  minio:
    image: minio/minio:latest
    container_name: minio-{{ server_id }}
    network_mode: "host"
    command: server /data --console-address ":{{ console_port | default('9001') }}" --address ":{{ api_port | default('9000') }}"
    environment:
      MINIO_ROOT_USER: {{ access_key }}
      MINIO_ROOT_PASSWORD: {{ secret_key }}
    volumes:
      - "{{ data_path }}:/data"
    deploy:
      resources:
        limits:
          memory: {{ mem_limit | default('1G') }}
          cpus: '{{ cpu_limit | default("1.0") }}'
    restart: always"""
            
            t.deploy_template = new_template
            await db.commit()
            print('MinIO template updated to host network mode successfully')
        else:
            print('MinIO template not found')
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
