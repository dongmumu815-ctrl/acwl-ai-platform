
import paramiko
import time
import sys
import base64

def hotfix_remote_server_v4():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # RegistryCtl Config - Try all possible keys
        registryctl_config = """registry_config: "/etc/registry/config.yml"
registry:
  config: "/etc/registry/config.yml"
log_level: info
"""

        # RegistryCtl Env - Add CONFIG path just in case
        registryctl_env = """CORE_URL=http://core:8080
CONFIG=/etc/registryctl/config.yml
"""

        # Write files
        files = {
            "/data/harbor/common/config/registryctl/config.yml": registryctl_config,
            "/data/harbor/common/config/registryctl/env": registryctl_env
        }
        
        for path, content in files.items():
            print(f"Updating {path}...")
            b64_content = base64.b64encode(content.encode()).decode()
            temp_file = f"/tmp/{path.split('/')[-1]}.tmp"
            
            cmd_create_temp = f"echo {b64_content} | base64 -d > {temp_file}"
            client.exec_command(cmd_create_temp)
            
            cmd_mv = f"echo '{password}' | sudo -S mv {temp_file} {path}"
            client.exec_command(cmd_mv)
            
            cmd_chmod = f"echo '{password}' | sudo -S chmod 644 {path}"
            client.exec_command(cmd_chmod)
            
            cmd_chown = f"echo '{password}' | sudo -S chown 10000:10000 {path}"
            client.exec_command(cmd_chown)

        # Restart containers
        print("Restarting registryctl...")
        cmd_restart = f"echo '{password}' | sudo -S docker restart registryctl"
        client.exec_command(cmd_restart)
        
        # Wait and check
        print("Waiting 10s...")
        time.sleep(10)
        
        stdin, stdout, stderr = client.exec_command("docker ps | grep registryctl")
        print(stdout.read().decode())
        
        # Check logs if restarted
        print("Checking logs...")
        stdin, stdout, stderr = client.exec_command("docker logs --tail 20 registryctl")
        print(stdout.read().decode())
        print(stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    hotfix_remote_server_v4()
