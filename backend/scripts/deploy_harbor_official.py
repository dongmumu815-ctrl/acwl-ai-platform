
import asyncio
import sys
import os
import paramiko
import time
from sqlalchemy import select

# Add backend directory to path
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
        
        # 2. Prepare Config (harbor.yml)
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
            # Stop containers
            ssh.exec_command(f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml down -v")
            ssh.exec_command(f"echo '{PASS}' | sudo -S docker rm -f harbor-core harbor-jobservice harbor-db harbor-portal registry registryctl redis nginx harbor-log")
            # Remove data directory completely
            ssh.exec_command(f"echo '{PASS}' | sudo -S rm -rf /data/harbor")
            
            # Create directories
            ssh.exec_command(f"echo '{PASS}' | sudo -S mkdir -p /data/harbor/common/config")
            ssh.exec_command(f"echo '{PASS}' | sudo -S mkdir -p {DEPLOY_PATH}")
            
            # Upload harbor.yml
            print("Uploading harbor.yml...")
            sftp = ssh.open_sftp()
            with open("temp_harbor.yml", "w", newline='\n') as f:
                f.write(harbor_yml)
            sftp.put("temp_harbor.yml", "/tmp/harbor.yml")
            sftp.close()
            
            ssh.exec_command(f"echo '{PASS}' | sudo -S mv /tmp/harbor.yml /data/harbor/harbor.yml")
            
            # Run Prepare
            print("Running Prepare Container...")
            cmd_prepare = f"echo '{PASS}' | sudo -S docker run --rm -v /data/harbor/common/config:/config -v /data/harbor:/data goharbor/prepare:v2.10.0 prepare --conf /data/harbor.yml"
            stdin, stdout, stderr = ssh.exec_command(cmd_prepare)
            out = stdout.read().decode()
            print(f"Prepare output: {out}")
            
            # --- FIX KEYS AND CERTS ---
            print("Fixing Keys and Certificates...")
            
            # 1. private_key.pem
            key_path = "/data/harbor/common/config/core/private_key.pem"
            # Force remove if dir
            ssh.exec_command(f"echo '{PASS}' | sudo -S rm -rf {key_path}")
            
            # Generate using -traditional to ensure PKCS#1 format (Harbor requirement)
            print("Generating Private Key (PKCS#1)...")
            cmd_key = f"echo '{PASS}' | sudo -S openssl genrsa -traditional -out {key_path} 4096"
            stdin, stdout, stderr = ssh.exec_command(cmd_key)
            # Fallback if -traditional not supported
            if "unknown option" in stderr.read().decode():
                print("OpenSSL -traditional not supported, trying default...")
                cmd_key = f"echo '{PASS}' | sudo -S openssl genrsa -out {key_path} 4096"
                ssh.exec_command(cmd_key)
                
            ssh.exec_command(f"echo '{PASS}' | sudo -S chmod 644 {key_path}")
            
            # 2. root.crt
            crt_path = "/data/harbor/common/config/registry/root.crt"
            # Ensure dir exists
            ssh.exec_command(f"echo '{PASS}' | sudo -S mkdir -p /data/harbor/common/config/registry")
            # Generate
            cmd_crt = f"echo '{PASS}' | sudo -S openssl req -new -x509 -key {key_path} -out {crt_path} -days 3650 -subj '/C=CN/ST=Beijing/L=Beijing/O=VMware/OU=Harbor/CN=harbor-token-signer'"
            ssh.exec_command(cmd_crt)
            
            # 3. secretkey
            # Check if prepare generated it at /data/harbor/secret/keys/secretkey
            src_secret = "/data/harbor/secret/keys/secretkey"
            dest_secret = "/data/harbor/common/config/core/certificates/secretkey"
            
            # Ensure dest dir exists
            ssh.exec_command(f"echo '{PASS}' | sudo -S mkdir -p /data/harbor/common/config/core/certificates")
            
            # Copy or Generate
            check_secret = f"echo '{PASS}' | sudo -S test -f {src_secret} && echo 'exists' || echo 'missing'"
            stdin, stdout, stderr = ssh.exec_command(check_secret)
            if "exists" in stdout.read().decode():
                print("Copying secretkey from prepare location...")
                ssh.exec_command(f"echo '{PASS}' | sudo -S cp {src_secret} {dest_secret}")
            else:
                print("Generating new secretkey...")
                # Generate random 32 char string
                gen_secret = f"echo '{PASS}' | sudo -S python3 -c \"import secrets; print(secrets.token_urlsafe(32), end='')\" > {dest_secret}"
                ssh.exec_command(gen_secret)
            
            ssh.exec_command(f"echo '{PASS}' | sudo -S chmod 644 {dest_secret}")

            # Upload Compose
            print("Uploading docker-compose.yml...")
            sftp = ssh.open_sftp()
            with open("temp_official_compose.yml", "w", newline='\n') as f:
                f.write(compose)
            sftp.put("temp_official_compose.yml", "/tmp/docker-compose.yml")
            sftp.close()
            ssh.exec_command(f"echo '{PASS}' | sudo -S mv /tmp/docker-compose.yml /data/harbor/docker-compose.yml")
            
            # Start
            print("Starting Harbor...")
            cmd_up = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d"
            stdin, stdout, stderr = ssh.exec_command(cmd_up)
            print(stdout.read().decode())
            print(stderr.read().decode())
            
            # Verify Login
            print("Verifying Login (Wait 45s)...")
            time.sleep(45)
            token_url = "http://10.20.1.204:5000/service/token?service=harbor-registry&client_id=docker&offline_token=true"
            cmd = f"curl -v -u admin:Harbor12345 '{token_url}' 2>&1"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode()
            print(out)
            
            if "HTTP/1.1 200 OK" in out:
                print("SUCCESS: Login Verified!")
            else:
                print("FAILURE: Login Failed.")
            
            print("Harbor Deployment Complete.")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()
            if os.path.exists("temp_harbor.yml"): os.remove("temp_harbor.yml")
            if os.path.exists("temp_official_compose.yml"): os.remove("temp_official_compose.yml")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
