
import paramiko
import sys
import time

def nuke_harbor():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected. Starting FULL CLEANUP...")
        
        # 1. Stop and remove all harbor containers
        print("1. Removing containers...")
        # Get list of harbor containers
        cmd = "docker ps -a -q -f name=harbor -f name=registry -f name=redis -f name=nginx"
        stdin, stdout, stderr = client.exec_command(cmd)
        containers = stdout.read().decode().strip().split()
        
        if containers:
            cmd = f"echo '{password}' | sudo -S docker rm -f {' '.join(containers)}"
            print(f"Running: {cmd}")
            client.exec_command(cmd)
        else:
            print("No containers found.")
            
        # 2. Prune networks
        print("2. Pruning networks...")
        cmd = f"echo '{password}' | sudo -S docker network prune -f"
        client.exec_command(cmd)
        
        # 3. Prune volumes (optional, but good)
        print("3. Pruning volumes...")
        cmd = f"echo '{password}' | sudo -S docker volume prune -f"
        client.exec_command(cmd)
        
        # 4. REMOVE DATA DIRECTORY - THE MOST IMPORTANT PART
        print("4. WIPING /data/harbor...")
        cmd = f"echo '{password}' | sudo -S rm -rf /data/harbor"
        print(f"Running: {cmd}")
        client.exec_command(cmd)
        
        # 5. Verify
        print("5. Verifying cleanup...")
        cmd = "ls -la /data/harbor"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("\nCleanup Complete. The server is ready for a fresh install.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    nuke_harbor()
