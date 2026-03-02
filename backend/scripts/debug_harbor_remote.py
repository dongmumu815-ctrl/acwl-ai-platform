
import paramiko
import time
import sys

def debug_remote_server():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # 1. Check container status
        print("\n=== Docker Container Status ===")
        stdin, stdout, stderr = client.exec_command("docker ps -a")
        output = stdout.read().decode()
        print(output)
        
        lines = output.strip().split('\n')
        if len(lines) > 1:
            headers = lines[0]
            for line in lines[1:]:
                # Check for restarting or exited containers
                # Also check harbor-core specifically
                if "Restarting" in line or "Exited" in line or "harbor-core" in line:
                    parts = line.split()
                    container_id = parts[0]
                    # The name is usually the last column
                    container_name = parts[-1] 
                    
                    print(f"\n[!] Checking logs for {container_name} ({container_id})...")
                    
                    # 2. Get logs for unhealthy containers
                    print(f"--- Logs for {container_name} ---")
                    stdin, stdout, stderr = client.exec_command(f"docker logs --tail 50 {container_id}")
                    logs = stdout.read().decode() + stderr.read().decode()
                    print(logs)
                    print("-------------------------------")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_remote_server()
