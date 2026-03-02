
import paramiko
import sys
import time

def force_reset_admin_password():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # SQL to reset password for user id 1 (admin)
        # We need to know the salt and password structure. Harbor uses bcrypt?
        # Actually Harbor stores password in 'harbor_user' table.
        # But for v2.0+, it might be different.
        
        # Let's first check the user table structure
        print("\n=== Checking User Table Structure ===")
        cmd = "docker exec harbor-db psql -U postgres -d registry -c \"SELECT * FROM harbor_user WHERE user_id = 1;\""
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        # Since we can't easily generate bcrypt hash in shell without tools,
        # We can try to update the email or something to verify access,
        # OR we can delete the user 1 and let Harbor recreate it? No, that might break foreign keys.
        
        # Plan B: Check if there are other users?
        
        # Plan C: Use Harbor's internal tool or API if possible?
        # But we are unauthorized.
        
        # Let's try to set it to a known hash if possible.
        # Default 'Harbor12345' hash is often used in examples.
        # Hash for 'Harbor12345' with default salt (if salt is stored separately)
        
        # Wait, if the previous log said "User id: 1 updated its encrypted password successfully",
        # it means it picked up the ENV variable.
        # Maybe the ENV variable had special characters that were escaped wrong?
        # The password is "2wsx1QAZaczt"
        
        # Let's try to force reset it to "Harbor12345" via ENV and restart Core again.
        # But this time we will write it explicitly to the file.
        
        print("\n=== Forcing Simple Password in Env ===")
        new_pass = "Harbor12345"
        
        # 1. Update Env file
        cmd = f"echo '{password}' | sudo -S sed -i 's/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD={new_pass}/' /data/harbor/common/config/core/env"
        client.exec_command(cmd)
        
        # 2. Verify Env file
        cmd = "cat /data/harbor/common/config/core/env | grep ADMIN_PASSWORD"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"New Env Config: {stdout.read().decode().strip()}")
        
        # 3. We also need to clear the "already encrypted" flag if Harbor stores it?
        # Harbor Core checks if password in DB matches?
        # If we change ENV, Harbor Core on restart *should* update it if it differs?
        # Let's check logs again after restart.
        
        print("Restarting Harbor Core...")
        cmd = f"echo '{password}' | sudo -S docker restart harbor-core"
        client.exec_command(cmd)
        
        print("Waiting 15s...")
        time.sleep(15)
        
        print("Checking Logs...")
        cmd = "docker logs --tail 20 harbor-core"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    force_reset_admin_password()
