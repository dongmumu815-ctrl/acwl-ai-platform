
import os
import paramiko
import time

# 配置信息
HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def run_ssh_command(ssh, command):
    print(f"Executing: {command}")
    # Use sudo -S -p '' to read password from stdin
    # Wrap command in sh -c to handle complex shell operations like &&, >, >>, cd
    full_cmd = f"echo '{PASS}' | sudo -S -p '' sh -c '{command}'"
    
    stdin, stdout, stderr = ssh.exec_command(full_cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if exit_status != 0:
        if "No such file or directory" not in err: 
             print(f"Error executing {command}: {err}")
    return out, err

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Starting FINAL CLEAN RESTART procedure...")

        # 1. Stop Harbor
        # Note: we wrap everything in sudo sh -c, so cd works
        run_ssh_command(ssh, "cd /data/harbor && docker compose down -v")
        
        # Force remove all harbor containers just in case
        print("Force removing containers...")
        containers = "harbor-log registry registryctl harbor-db harbor-core harbor-portal harbor-jobservice redis nginx"
        run_ssh_command(ssh, f"docker rm -f {containers}")
        
        # 2. Force Clean Secret Key
        clean_key = "MTIzNDU2Nzg5MDEyMzQ1Ng=="
        # echo -n inside the sudo shell
        cmd = f"echo -n '{clean_key}' > /data/harbor/common/config/core/certificates/secretkey"
        run_ssh_command(ssh, cmd)
        
        run_ssh_command(ssh, "chmod 600 /data/harbor/common/config/core/certificates/secretkey")
        
        # 3. Wipe Database
        print("Wiping database to force password reset...")
        run_ssh_command(ssh, "rm -rf /data/harbor/database")
        run_ssh_command(ssh, "rm -rf /data/harbor/redis")
        
        print("Recreating directories with correct permissions...")
        run_ssh_command(ssh, "mkdir -p /data/harbor/database")
        run_ssh_command(ssh, "mkdir -p /data/harbor/redis")
        
        # Fix permissions: 
        # Postgres (999), Redis (999)
        # We use chmod 777 to be absolutely safe against UID mismatches, 
        # referencing common Harbor issues where permission denied occurs after volume wipe.
        run_ssh_command(ssh, "chmod 777 /data/harbor/database")
        run_ssh_command(ssh, "chmod 777 /data/harbor/redis")
        
        # 4. Ensure Env config has the password
        env_file = "/data/harbor/common/config/core/env"
        cmd = f"grep -q 'HARBOR_ADMIN_PASSWORD' {env_file} || echo 'HARBOR_ADMIN_PASSWORD=Harbor12345' >> {env_file}"
        run_ssh_command(ssh, cmd)
        
        # 5. Start Harbor
        print("Starting Harbor...")
        run_ssh_command(ssh, "cd /data/harbor && docker compose up -d")
        
        print("Harbor restarting. Waiting 60s for DB initialization...")
        time.sleep(60)
        
        # 6. Verify
        print("Verifying login...")
        # curl doesn't need sudo, but our wrapper applies it. It's fine.
        check_cmd = "curl -u 'admin:Harbor12345' -i http://127.0.0.1/api/v2.0/users/current"
        out, err = run_ssh_command(ssh, check_cmd)
        print("Verification Output:")
        print(out)
        
    except Exception as e:
        print(f"SSH Connection Failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
