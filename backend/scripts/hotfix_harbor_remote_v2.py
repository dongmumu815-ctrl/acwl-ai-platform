
import paramiko
import time
import sys
import base64

def hotfix_remote_server_v2():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # JobService Config - Add loggers
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
loggers:
  - name: "STD_OUTPUT"
    level: "INFO"
"""

        # Registry Config - Simplify to rule out issues
        # Remove redis cache for now, use defaults or inmemory if needed
        registry_config = """version: 0.1
log:
  level: info
  fields:
    service: registry
storage:
  cache:
    blobdescriptor: inmemory
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

        # RegistryCtl Config - Ensure absolute path and valid yaml
        registryctl_config = """registry:
  config: "/etc/registry/config.yml"
log_level: info
"""

        # Write files
        files = {
            "/data/harbor/common/config/jobservice/config.yml": jobservice_config,
            "/data/harbor/common/config/registry/config.yml": registry_config,
            "/data/harbor/common/config/registryctl/config.yml": registryctl_config
        }
        
        for path, content in files.items():
            print(f"Updating {path}...")
            # Use printf to avoid newline issues
            b64_content = base64.b64encode(content.encode()).decode()
            
            # Create temp file
            temp_file = f"/tmp/{path.split('/')[-1]}.tmp"
            cmd_create_temp = f"echo {b64_content} | base64 -d > {temp_file}"
            client.exec_command(cmd_create_temp)
            
            # Move to target with sudo
            cmd_mv = f"echo '{password}' | sudo -S mv {temp_file} {path}"
            stdin, stdout, stderr = client.exec_command(cmd_mv)
            err = stderr.read().decode()
            if err and "password" not in err.lower(): 
                 print(f"Error moving {path}: {err}")
            
            # Fix permissions
            cmd_chmod = f"echo '{password}' | sudo -S chmod 644 {path}"
            client.exec_command(cmd_chmod)
            
            # Fix ownership (harbor:harbor)
            cmd_chown = f"echo '{password}' | sudo -S chown 10000:10000 {path}"
            client.exec_command(cmd_chown)

        # Restart containers
        print("Restarting containers...")
        cmd_restart = f"echo '{password}' | sudo -S docker restart harbor-jobservice registryctl"
        client.exec_command(cmd_restart)
        
        # Wait and check
        print("Waiting 10s...")
        time.sleep(10)
        
        stdin, stdout, stderr = client.exec_command("docker ps | grep -E 'harbor-jobservice|registryctl'")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    hotfix_remote_server_v2()
