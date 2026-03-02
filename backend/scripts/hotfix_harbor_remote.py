
import paramiko
import time
import sys

def hotfix_remote_server():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # 1. Define configurations
        secret = "Harbor12345" # Using fixed secret for now or generate one
        
        # Core Env
        core_env = f"""LOG_LEVEL=info
CONFIG_PATH=/etc/core/app.conf
SYNC_REGISTRY=false
CHART_CACHE_DRIVER=redis
MAX_JOB_WORKERS=10
TOKEN_SERVICE_URL=http://core:8080/service/token
TOKEN_KEY_PATH=/etc/core/key
ADMIN_PASSWORD=Harbor12345
DATABASE_TYPE=postgresql
POSTGRESQL_HOST=postgresql
POSTGRESQL_PORT=5432
POSTGRESQL_USERNAME=postgres
POSTGRESQL_PASSWORD=root123
POSTGRESQL_DATABASE=registry
REDIS_URL=redis://redis:6379/0
EXT_ENDPOINT=http://reg.mydomain.com
CORE_URL=http://core:8080
JOBSERVICE_URL=http://jobservice:8080
JOBSERVICE_SECRET={secret}
REGISTRY_URL=http://registry:5000
REGISTRY_CONTROLLER_URL=http://registryctl:8080
PORTAL_URL=http://portal:80
_REDIS_URL_CORE=redis://redis:6379/0
_REDIS_URL_REG=redis://redis:6379/1
_REDIS_URL_JOB=redis://redis:6379/2
"""

        # JobService Env
        job_env = f"""CORE_URL=http://core:8080
JOBSERVICE_SECRET={secret}
"""

        # RegistryCtl Config
        registryctl_config = """registry:
  config: "/etc/registry/config.yml"
log_level: info
"""

    # JobService Config
        jobservice_config = """protocol: "http"
port: 8080
worker_pool:
  workers: 10
  backend: "redis"
  redis_pool:
    redis_url: "redis://redis:6379/2"
    namespace: "harbor_job_service_namespace"
job_loggers:
  - name: "STD_OUTPUT"
    level: "INFO"
"""

        # Registry Config (Ensure it exists)
        registry_config = """version: 0.1
log:
  level: info
  fields:
    service: registry
storage:
  cache:
    layerinfo: redis
  filesystem:
    rootdirectory: /storage
  maintenance:
    uploadpurging:
      enabled: false
  delete:
    enabled: true
http:
  addr: :5000
  secret: Harbor12345
  debug:
    addr: localhost:5001
auth:
  token:
    realm: http://reg.mydomain.com/service/token
    service: harbor-registry
    issuer: harbor-token-issuer
    rootcertbundle: /etc/registry/root.crt
redis:
  addr: redis:6379
  db: 1
  dial_timeout: 10ms
  read_timeout: 10ms
  write_timeout: 10ms
  pool:
    maxidle: 16
    maxactive: 64
    idletimeout: 300s
"""

        # 2. Write files
        files = {
            "/data/harbor/common/config/core/env": core_env,
            "/data/harbor/common/config/jobservice/env": job_env,
            "/data/harbor/common/config/registryctl/config.yml": registryctl_config,
            "/data/harbor/common/config/registry/config.yml": registry_config,
            "/data/harbor/common/config/jobservice/config.yml": jobservice_config
        }
        
        for path, content in files.items():
            print(f"Updating {path}...")
            # 1. Write to /tmp/temp_file
            import base64
            b64_content = base64.b64encode(content.encode()).decode()
            
            # Create temp file
            temp_file = f"/tmp/{path.split('/')[-1]}.tmp"
            cmd_create_temp = f"echo {b64_content} | base64 -d > {temp_file}"
            client.exec_command(cmd_create_temp)
            
            # 2. Move to target with sudo
            # echo 'password' | sudo -S mv /tmp/temp_file /target/path
            cmd_mv = f"echo '{password}' | sudo -S mv {temp_file} {path}"
            stdin, stdout, stderr = client.exec_command(cmd_mv)
            err = stderr.read().decode()
            if err and "password" not in err.lower(): # sudo -S might prompt for password on stderr
                 print(f"Error moving {path}: {err}")
            
            # 3. Fix permissions (readable by all)
            cmd_chmod = f"echo '{password}' | sudo -S chmod 644 {path}"
            client.exec_command(cmd_chmod)

        # 3. Restart containers
        print("Restarting containers...")
        cmd_restart = f"echo '{password}' | sudo -S docker restart harbor-core harbor-jobservice registryctl"
        client.exec_command(cmd_restart)
        
        # 4. Wait and check status
        print("Waiting 10s for startup...")
        time.sleep(10)
        
        stdin, stdout, stderr = client.exec_command("docker ps | grep -E 'harbor-core|harbor-jobservice|registryctl'")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    hotfix_remote_server()
