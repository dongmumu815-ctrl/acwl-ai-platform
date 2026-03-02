import asyncio
import sys
import os
import paramiko
import time
from sqlalchemy import select

# 将 backend 目录添加到路径以便导入 app 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppTemplate

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
DEPLOY_PATH = "/opt/acwl-apps/instances/96"

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Get Template
        stmt = select(AppTemplate).where(AppTemplate.name.ilike("%Harbor%"))
        result = await session.execute(stmt)
        templates = result.scalars().all()
        template = None
        for t in templates:
            if "installer" not in t.name.lower():
                template = t
                break
        
        if not template:
            print("Harbor template not found!")
            return

        print(f"Using template: {template.name}")
        compose = template.deploy_template
        
        # 2. Prepare Config (harbor.yml) - Fixed for v2.10.0
        harbor_yml = """
hostname: 10.20.1.204
http:
  port: 5000
harbor_admin_password: Harbor12345
database:
  password: root
  max_idle_conns: 50
  max_open_conns: 100
data_volume: /data/harbor
trivy:
  ignore_unfixed: false
  skip_update: false
jobservice:
  max_job_workers: 10
  job_loggers:
    - type: "file"
      level: "INFO"
  logger_sweeper_duration: 1d
notification:
  webhook_job_max_retry: 10
  webhook_job_http_client_timeout: 10s
chart:
  absolute_url: disabled
log:
  level: info
  local:
    rotate_count: 50
    rotate_size: 200M
    location: /var/log/harbor
_version: 2.10.0
proxy:
  http_proxy:
  https_proxy:
  no_proxy:
  components:
    - core
    - jobservice
    - trivy
"""
        # Fix Compose Variables
        compose = compose.replace('{{ data_volume }}', '/data/harbor')
        compose = compose.replace('{{ http_port }}', '5000')
        compose = compose.replace('{{ https_port }}', '443')
        
        # 3. Execution
        print("Connecting to server...")
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(HOST, username=USER, password=PASS)
            
            print("Cleaning up...")
            ssh.exec_command(f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml down -v")
            ssh.exec_command(f"echo '{PASS}' | sudo -S docker rm -f harbor-core harbor-jobservice harbor-db harbor-portal registry registryctl redis nginx harbor-log")
            ssh.exec_command(f"echo '{PASS}' | sudo -S rm -rf /data/harbor")
            
            # Create directories
            ssh.exec_command(f"echo '{PASS}' | sudo -S mkdir -p /data/harbor")
            ssh.exec_command(f"echo '{PASS}' | sudo -S mkdir -p {DEPLOY_PATH}")
            
            # Upload harbor.yml
            print("Uploading harbor.yml...")
            sftp = ssh.open_sftp()
            with open("temp_harbor_v4.yml", "w", newline='\n') as f:
                f.write(harbor_yml)
            sftp.put("temp_harbor_v4.yml", "/tmp/harbor.yml")
            sftp.close()
            
            ssh.exec_command(f"echo '{PASS}' | sudo -S mv /tmp/harbor.yml /data/harbor/harbor.yml")
            
            # Run Prepare
            print("Running Prepare Container...")
            cmd_prepare = f"echo '{PASS}' | sudo -S docker run --rm -v /data/harbor:/data goharbor/prepare:v2.10.0 prepare --conf /data/harbor.yml"
            stdin, stdout, stderr = ssh.exec_command(cmd_prepare)
            print(stdout.read().decode())
            err = stderr.read().decode()
            if err:
                print(f"Prepare output/error: {err}")
                
            # Check if config generated
            print("Checking generated config...")
            stdin, stdout, stderr = ssh.exec_command(f"echo '{PASS}' | sudo -S ls -R /data/harbor/common/config")
            out = stdout.read().decode()
            print(out)
            
            if "no such file" in out:
                 print("Config generation failed! Aborting.")
                 return

            # Upload Compose
            print("Uploading docker-compose.yml...")
            sftp = ssh.open_sftp()
            with open("temp_official_compose_v4.yml", "w", newline='\n') as f:
                f.write(compose)
            sftp.put("temp_official_compose_v4.yml", "/tmp/docker-compose.yml")
            sftp.close()
            ssh.exec_command(f"echo '{PASS}' | sudo -S mv /tmp/docker-compose.yml /data/harbor/docker-compose.yml")
            
            # Start
            print("Starting Harbor...")
            cmd_up = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d"
            stdin, stdout, stderr = ssh.exec_command(cmd_up)
            print(stdout.read().decode())
            print(stderr.read().decode())
            
            # Resize Column (Just in case)
            print("Resizing Password Column (Safety)...")
            time.sleep(10)
            query = "ALTER TABLE harbor_user ALTER COLUMN password TYPE varchar(128);"
            cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
            ssh.exec_command(cmd)
            
            # Verify Login
            print("Verifying Login (Wait 20s)...")
            time.sleep(20)
            token_url = "http://10.20.1.204:5000/service/token?service=harbor-registry&client_id=docker&offline_token=true"
            cmd = f"curl -v -u admin:Harbor12345 '{token_url}' 2>&1"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode()
            print(out)
            
            if "HTTP/1.1 200 OK" in out:
                print("SUCCESS: Login Verified!")
            else:
                print("FAILURE: Login Failed.")
            
            print("Official Reinstall v4 Complete.")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()
            if os.path.exists("temp_harbor_v4.yml"): os.remove("temp_harbor_v4.yml")
            if os.path.exists("temp_official_compose_v4.yml"): os.remove("temp_official_compose_v4.yml")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
