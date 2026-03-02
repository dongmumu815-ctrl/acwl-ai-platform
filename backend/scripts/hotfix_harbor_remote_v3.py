
import paramiko
import time
import sys
import base64

def hotfix_remote_server_v3():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # Core Config - Add secret to app.conf
        core_app_conf = """appname = Harbor
runmode = prod
enablegzip = true
jobservice_secret = Harbor12345

[dev]
httpport = 8080
[prod]
httpport = 8080
"""

        # RegistryCtl Config - Try registry_config key
        registryctl_config = """registry_config: "/etc/registry/config.yml"
log_level: info
"""

        # Write files
        files = {
            "/data/harbor/common/config/core/app.conf": core_app_conf,
            "/data/harbor/common/config/registryctl/config.yml": registryctl_config
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
        print("Restarting containers...")
        # Restart Core (to pick up app.conf), JobService (just in case), RegistryCtl
        cmd_restart = f"echo '{password}' | sudo -S docker restart harbor-core harbor-jobservice registryctl"
        client.exec_command(cmd_restart)
        
        # Wait and check
        print("Waiting 15s...")
        time.sleep(15)
        
        stdin, stdout, stderr = client.exec_command("docker ps | grep -E 'harbor-core|harbor-jobservice|registryctl'")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    hotfix_remote_server_v3()
