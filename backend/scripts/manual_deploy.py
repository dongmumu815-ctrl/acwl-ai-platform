import asyncio
import sys
import os
import paramiko

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppTemplate
from sqlalchemy import select

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
DEPLOY_PATH = "/opt/acwl-apps/instances/96"

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Get Template
        stmt = select(AppTemplate).where(AppTemplate.id == 4)
        result = await session.execute(stmt)
        template = result.scalar_one_or_none()
        
        if not template:
            print("Template 4 not found!")
            return
            
        script = template.default_config.get('pre_deploy_script')
        compose = template.deploy_template
        
        # 2. Hardcode Variables
        # Script
        script = script.replace('{{ external_url }}', 'http://10.20.1.204:5000')
        script = script.replace('{{ http_port }}', '5000')
        script = script.replace('{{ https_port }}', '443')
        script = script.replace('{{ hostname }}', '10.20.1.204')
        script = script.replace('{{ harbor_admin_password }}', 'Harbor12345')
        script = script.replace('{{ data_volume }}', '/data/harbor')
        
        # Fix Private Key Generation in Script
        gen_key_cmd = "openssl genrsa -out $INSTALL_PATH/common/config/core/private_key.pem 4096"
        convert_cmd = """
        openssl genrsa -out $INSTALL_PATH/common/config/core/private_key.pem 4096
        # Convert to PKCS#1
        if openssl rsa -help 2>&1 | grep -q "traditional"; then
            openssl rsa -in $INSTALL_PATH/common/config/core/private_key.pem -out $INSTALL_PATH/common/config/core/private_key.pem.tmp -traditional
            mv $INSTALL_PATH/common/config/core/private_key.pem.tmp $INSTALL_PATH/common/config/core/private_key.pem
        else
            openssl rsa -in $INSTALL_PATH/common/config/core/private_key.pem -out $INSTALL_PATH/common/config/core/private_key.pem.tmp
            mv $INSTALL_PATH/common/config/core/private_key.pem.tmp $INSTALL_PATH/common/config/core/private_key.pem
        fi
        """
        script = script.replace(gen_key_cmd, convert_cmd)
        
        # Compose
        compose = compose.replace('{{ data_volume }}', '/data/harbor')
        compose = compose.replace('{{ http_port }}', '5000')
        compose = compose.replace('{{ https_port }}', '443')
        
        print("Generated configuration files locally.")
        
        # 3. Deploy manually
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(HOST, username=USER, password=PASS)
            
            # Create deploy dir
            cmd = f"echo '{PASS}' | sudo -S mkdir -p {DEPLOY_PATH}"
            ssh.exec_command(cmd)
            
            # Upload files
            sftp = ssh.open_sftp()
            
            # Write to local tmp then upload
            with open("temp_script.sh", "w", newline='\n') as f:
                f.write(script)
            with open("temp_compose.yml", "w", newline='\n') as f:
                f.write(compose)
                
            sftp.put("temp_script.sh", "/tmp/pre_deploy.sh")
            sftp.put("temp_compose.yml", "/tmp/docker-compose.yml")
            sftp.close()
            
            print("Files uploaded to /tmp.")
            
            # Move to deploy path and set permissions
            cmd = f"echo '{PASS}' | sudo -S mv /tmp/pre_deploy.sh {DEPLOY_PATH}/pre_deploy.sh"
            ssh.exec_command(cmd)
            cmd = f"echo '{PASS}' | sudo -S mv /tmp/docker-compose.yml {DEPLOY_PATH}/docker-compose.yml"
            ssh.exec_command(cmd)
            cmd = f"echo '{PASS}' | sudo -S chmod +x {DEPLOY_PATH}/pre_deploy.sh"
            ssh.exec_command(cmd)
            
            # Clean old data
            print("Cleaning old data...")
            cmd = f"echo '{PASS}' | sudo -S docker rm -f harbor-log harbor-db harbor-core registry registryctl harbor-jobservice harbor-portal nginx redis"
            ssh.exec_command(cmd)
            cmd = f"echo '{PASS}' | sudo -S rm -rf /data/harbor"
            ssh.exec_command(cmd)
            
            # Run Script
            print("Running pre_deploy.sh...")
            cmd = f"echo '{PASS}' | sudo -S bash {DEPLOY_PATH}/pre_deploy.sh"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode()
            err = stderr.read().decode()
            print(out)
            if err:
                print(f"STDERR: {err}")
                
            # Copy docker-compose to /data/harbor for convenience (standard Harbor location)
            cmd = f"echo '{PASS}' | sudo -S cp {DEPLOY_PATH}/docker-compose.yml /data/harbor/docker-compose.yml"
            ssh.exec_command(cmd)
            
            # Start Containers
            print("Starting containers...")
            cmd = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode()
            err = stderr.read().decode()
            print(out)
            if err:
                print(f"STDERR: {err}")
                
            print("Manual deployment completed.")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()
            # Clean local temp files
            if os.path.exists("temp_script.sh"): os.remove("temp_script.sh")
            if os.path.exists("temp_compose.yml"): os.remove("temp_compose.yml")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
