import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("1. Stopping all containers...")
        cmd = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml down"
        ssh.exec_command(cmd)
        
        print("2. Removing Database Directory completely...")
        cmd = f"echo '{PASS}' | sudo -S rm -rf /data/harbor/database"
        ssh.exec_command(cmd)
        # Recreate empty dir to be safe (Docker handles it but just in case)
        cmd = f"echo '{PASS}' | sudo -S mkdir -p /data/harbor/database"
        ssh.exec_command(cmd)
        cmd = f"echo '{PASS}' | sudo -S chmod 777 /data/harbor/database" # PG needs perm
        ssh.exec_command(cmd)
        
        print("3. Starting Harbor...")
        cmd = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        print("Waiting for startup (60s for DB init)...")
        time.sleep(60)
        
        print("4. Checking Core Logs...")
        cmd = f"echo '{PASS}' | sudo -S docker logs --tail 20 harbor-core"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        logs = stdout.read().decode()
        print(logs)
        
        if "The database has been migrated successfully" in logs:
            print("DB Migration Success.")
        
        print("5. Testing Login with Default Password...")
        cmd = f"echo '{PASS}' | sudo -S docker login -u admin -p Harbor12345 127.0.0.1:5000"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        print("STDOUT:", out)
        print("STDERR:", err)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
