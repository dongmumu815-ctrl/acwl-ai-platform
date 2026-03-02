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
        
        script = template.default_config.get('pre_deploy_script')
        compose = template.deploy_template
        
        # 2. Apply Configuration & Fixes (Reinstall v9 Logic)
        HTTP_PORT = "5000"
        HTTPS_PORT = "443"
        EXTERNAL_URL = "http://10.20.1.204:5000"
        HOSTNAME = "10.20.1.204"
        ADMIN_PASSWORD = "Harbor12345"
        DATA_VOLUME = "/data/harbor"

        # Variable Replacement
        script = script.replace('{{ external_url }}', EXTERNAL_URL)
        script = script.replace('{{ http_port }}', HTTP_PORT)
        script = script.replace('{{ https_port }}', HTTPS_PORT)
        script = script.replace('{{ hostname }}', HOSTNAME)
        script = script.replace('{{ harbor_admin_password }}', ADMIN_PASSWORD)
        script = script.replace('{{ data_volume }}', DATA_VOLUME)
        
        if '$EXT_ENDPOINT/service/token' in script:
            script = script.replace('realm: $EXT_ENDPOINT/service/token', 'realm: $EXT_URL/service/token')
            
        gen_key_cmd = "openssl genrsa -out $INSTALL_PATH/common/config/core/private_key.pem 4096"
        convert_cmd = """
        openssl genrsa -out $INSTALL_PATH/common/config/core/private_key.pem 4096
        mv $INSTALL_PATH/common/config/core/private_key.pem $INSTALL_PATH/common/config/core/private_key.pem.raw
        openssl rsa -in $INSTALL_PATH/common/config/core/private_key.pem.raw -out $INSTALL_PATH/common/config/core/private_key.pem -traditional
        rm $INSTALL_PATH/common/config/core/private_key.pem.raw
        """
        if gen_key_cmd in script and "mv $INSTALL_PATH" not in script:
             script = script.replace(gen_key_cmd, convert_cmd)

        nginx_c_block = """
        location /c/ {
            proxy_pass http://core:8080/c/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        location /api/ {"""
        
        script = script.replace('location /api/ {', nginx_c_block)
        script = script.replace('location /service/ {', 'location /service/ {\n            proxy_set_header X-Forwarded-Proto \$scheme;')

        compose = compose.replace('{{ data_volume }}', DATA_VOLUME)
        compose = compose.replace('{{ http_port }}', HTTP_PORT)
        compose = compose.replace('{{ https_port }}', HTTPS_PORT)
        
        # 3. Execution
        print("Connecting to server...")
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(HOST, username=USER, password=PASS)
            
            print("Wiping /data/harbor (Fresh Install v9)...")
            ssh.exec_command(f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml down -v")
            ssh.exec_command(f"echo '{PASS}' | sudo -S docker rm -f harbor-core harbor-jobservice harbor-db harbor-portal registry registryctl redis nginx harbor-log")
            ssh.exec_command(f"echo '{PASS}' | sudo -S rm -rf /data/harbor")
            
            # Re-create directory
            ssh.exec_command(f"echo '{PASS}' | sudo -S mkdir -p {DEPLOY_PATH}")
            
            # Upload
            print("Uploading scripts...")
            sftp = ssh.open_sftp()
            with open("temp_reinstall_script_v9_retry.sh", "w", newline='\n') as f:
                f.write(script)
            with open("temp_reinstall_compose_v9_retry.yml", "w", newline='\n') as f:
                f.write(compose)
            sftp.put("temp_reinstall_script_v9_retry.sh", "/tmp/pre_deploy.sh")
            sftp.put("temp_reinstall_compose_v9_retry.yml", "/tmp/docker-compose.yml")
            sftp.close()
            
            # Move & Permission
            cmd_prep = f"""
            echo '{PASS}' | sudo -S mv /tmp/pre_deploy.sh {DEPLOY_PATH}/pre_deploy.sh && \
            echo '{PASS}' | sudo -S mv /tmp/docker-compose.yml {DEPLOY_PATH}/docker-compose.yml && \
            echo '{PASS}' | sudo -S chmod +x {DEPLOY_PATH}/pre_deploy.sh
            """
            ssh.exec_command(cmd_prep)
            
            # Generate Config
            print("Generating Config...")
            cmd_gen = f"echo '{PASS}' | sudo -S bash {DEPLOY_PATH}/pre_deploy.sh"
            stdin, stdout, stderr = ssh.exec_command(cmd_gen)
            print(stdout.read().decode())
            
            # Copy Compose
            ssh.exec_command(f"echo '{PASS}' | sudo -S cp {DEPLOY_PATH}/docker-compose.yml /data/harbor/docker-compose.yml")

            # Start
            print("Starting Harbor...")
            cmd_up = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d"
            stdin, stdout, stderr = ssh.exec_command(cmd_up)
            print(stdout.read().decode())
            print(stderr.read().decode())
            
            # Wait
            print("Waiting 15s...")
            time.sleep(15)
            
            # Resize Column
            print("Resizing Password Column...")
            query = "ALTER TABLE harbor_user ALTER COLUMN password TYPE varchar(128);"
            cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
            ssh.exec_command(cmd)

            # Create Test User
            print("Creating Test User...")
            # Generate hash for 'test1234'
            cmd = "htpasswd -B -n -b test test1234"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode().strip()
            if ":" in out:
                hash_val = out.split(":")[1]
                if hash_val.startswith("$2y$"):
                    hash_val = "$2a$" + hash_val[4:]
                escaped_hash = hash_val.replace("$", "\\$")
                
                query = f"INSERT INTO harbor_user (username, password, password_version, email, realname, comment, deleted, sysadmin_flag, creation_time, update_time) VALUES ('test', '{escaped_hash}', 'v2', 'test@example.com', 'Test User', 'Test', false, false, NOW(), NOW());"
                cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
                stdin, stdout, stderr = ssh.exec_command(cmd)
                print(stdout.read().decode())
                print(stderr.read().decode())
            else:
                print("Failed to generate test hash")
            
            print("Reinstall v9 Retry Complete.")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()
            if os.path.exists("temp_reinstall_script_v9_retry.sh"): os.remove("temp_reinstall_script_v9_retry.sh")
            if os.path.exists("temp_reinstall_compose_v9_retry.yml"): os.remove("temp_reinstall_compose_v9_retry.yml")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
