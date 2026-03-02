
import paramiko
import sys
import time

def debug_login():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # 1. Try to login via Curl to Core directly
        # Core is at http://127.0.0.1:8080 mapped to host 80 (via nginx)
        # But we can access Core container IP or localhost:80
        
        print("\n=== Testing Login via Curl (admin:Harbor12345) ===")
        # Harbor v2 API: GET /api/v2.0/users/current
        cmd = "curl -i -u 'admin:Harbor12345' http://127.0.0.1:80/api/v2.0/users/current"
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\n=== Testing Login via Curl (admin:2wsx1QAZaczt) ===")
        cmd = "curl -i -u 'admin:2wsx1QAZaczt' http://127.0.0.1:80/api/v2.0/users/current"
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        # 2. Check Core Logs for the last minute to see login failure reason
        print("\n=== Recent Core Logs ===")
        cmd = "docker logs --tail 50 harbor-core"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        # 3. Dump DB user info again (full width)
        print("\n=== DB User Info ===")
        cmd = "docker exec harbor-db psql -U postgres -d registry -c \"SELECT user_id, username, password_version, creation_time, update_time FROM harbor_user WHERE user_id = 1;\""
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_login()
