
import paramiko
import sys
import time

def force_update_db_password():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # 1. Update Core Env to Harbor12345
        print("Updating Core Env to Harbor12345...")
        new_pass = "Harbor12345"
        cmd = f"echo '{password}' | sudo -S sed -i 's/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD={new_pass}/' /data/harbor/common/config/core/env"
        client.exec_command(cmd)
        
        # 2. Update DB directly
        # The default salt is often generated randomly.
        # But Harbor v2.0+ uses sha256 with salt.
        # We can try to delete the user row, but that's risky.
        # Instead, let's try to reset the database completely AGAIN, but this time ensuring the ENV is set to Harbor12345 BEFORE first boot.
        
        print("Stopping Harbor...")
        cmd = f"echo '{password}' | sudo -S docker stop harbor-core harbor-jobservice harbor-db"
        client.exec_command(cmd)
        time.sleep(5)
        
        print("Wiping Database...")
        cmd = f"echo '{password}' | sudo -S rm -rf /data/harbor/database/*"
        client.exec_command(cmd)
        
        print("Starting DB...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-db"
        client.exec_command(cmd)
        
        print("Waiting for DB (15s)...")
        time.sleep(15)
        
        print("Starting Core (will init with Harbor12345)...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-core"
        client.exec_command(cmd)
        
        print("Waiting for Core (20s)...")
        time.sleep(20)
        
        print("Starting JobService...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-jobservice"
        client.exec_command(cmd)
        
        print("Checking Logs...")
        cmd = "docker logs harbor-core 2>&1 | grep 'User id: 1'"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("Checking Env File...")
        cmd = "cat /data/harbor/common/config/core/env | grep ADMIN_PASSWORD"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    force_update_db_password()
