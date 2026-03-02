
import paramiko
import sys
import time

def recreate_admin_user():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        
        print("1. Stopping Core...")
        cmd = f"echo '{password}' | sudo -S docker stop harbor-core"
        client.exec_command(cmd)
        time.sleep(5)
        
        print("2. Deleting Admin User (ID 1) from DB...")
        cmd = "docker exec harbor-db psql -U postgres -d registry -c \"DELETE FROM harbor_user WHERE user_id = 1;\""
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("3. Starting Core (expecting it to recreate admin)...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-core"
        client.exec_command(cmd)
        time.sleep(20)
        
        print("4. Checking Logs...")
        cmd = "docker logs --tail 20 harbor-core"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("5. Verifying Login...")
        cmd = "curl -i -u 'admin:Harbor12345' http://127.0.0.1/api/v2.0/users/current"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    recreate_admin_user()
