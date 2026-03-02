
import paramiko
import time
import sys

def reset_harbor_db():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        print("1. Stopping Harbor containers (Core, JobService, DB)...")
        cmd = "echo 'cepiec1qaz@WSXaczt8912059Nxtektppyoud' | sudo -S docker stop harbor-core harbor-jobservice harbor-db"
        client.exec_command(cmd)
        time.sleep(5)
        
        print("2. Cleaning Database Data (/data/harbor/database/*)...")
        # Be extremely careful with this command
        cmd = "echo 'cepiec1qaz@WSXaczt8912059Nxtektppyoud' | sudo -S rm -rf /data/harbor/database/*"
        client.exec_command(cmd)
        
        print("3. Starting Harbor DB (will re-initialize)...")
        cmd = "echo 'cepiec1qaz@WSXaczt8912059Nxtektppyoud' | sudo -S docker start harbor-db"
        client.exec_command(cmd)
        
        print("Waiting 15s for DB initialization...")
        time.sleep(15)
        
        print("4. Starting Harbor Core (will run migrations and create admin)...")
        cmd = "echo 'cepiec1qaz@WSXaczt8912059Nxtektppyoud' | sudo -S docker start harbor-core"
        client.exec_command(cmd)
        
        print("Waiting 20s for Core initialization...")
        time.sleep(20)
        
        print("5. Starting JobService...")
        cmd = "echo 'cepiec1qaz@WSXaczt8912059Nxtektppyoud' | sudo -S docker start harbor-jobservice"
        client.exec_command(cmd)
        
        print("6. Checking Logs for Admin Password...")
        cmd = "docker logs harbor-core 2>&1 | grep 'User id: 1'"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\n=== Current Password Config ===")
        cmd = "cat /data/harbor/common/config/core/env | grep ADMIN_PASSWORD"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    reset_harbor_db()
