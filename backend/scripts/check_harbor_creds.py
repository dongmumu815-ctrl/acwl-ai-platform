
import paramiko
import sys

def check_admin_creds():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # 1. Check Core Env file for ADMIN_PASSWORD
        print("\n=== Checking Core Env Config ===")
        cmd = "cat /data/harbor/common/config/core/env | grep ADMIN_PASSWORD"
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode().strip()
        print(f"Output: {output}")
        
        # 2. Check Core Logs for user initialization
        print("\n=== Checking Core Logs for Admin User Init ===")
        # Look for "User id: 1" messages
        cmd = "docker logs harbor-core 2>&1 | grep 'User id: 1'"
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_admin_creds()
