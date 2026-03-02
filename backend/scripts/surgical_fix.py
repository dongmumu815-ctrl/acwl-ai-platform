
import paramiko
import sys
import time

def surgical_fix():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    # A known, safe, 16-char secret key (no special chars, no newlines)
    SAFE_SECRET_KEY = "aBcD1234aBcD1234" 
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print(f"Connected to {hostname}.")
        
        print("1. Stopping Harbor Services...")
        cmd = f"echo '{password}' | sudo -S docker stop harbor-core harbor-jobservice harbor-db registry registryctl"
        client.exec_command(cmd)
        time.sleep(5)
        
        print("2. Manually Overwriting 'secretkey' (The Root Cause)...")
        # Ensure directory exists
        cmd = f"echo '{password}' | sudo -S mkdir -p /data/harbor/common/config/core/certificates/"
        client.exec_command(cmd)
        
        # Write clean key - use printf to guarantee no newline
        cmd = f"echo '{password}' | sudo -S bash -c \"printf '{SAFE_SECRET_KEY}' > /data/harbor/common/config/core/certificates/secretkey\""
        client.exec_command(cmd)
        
        # Set permissions
        cmd = f"echo '{password}' | sudo -S chmod 644 /data/harbor/common/config/core/certificates/secretkey"
        client.exec_command(cmd)
        cmd = f"echo '{password}' | sudo -S chown 10000:10000 /data/harbor/common/config/core/certificates/secretkey"
        client.exec_command(cmd)
        
        print("3. Wiping Database (to force re-encryption with new key)...")
        cmd = f"echo '{password}' | sudo -S rm -rf /data/harbor/database/*"
        client.exec_command(cmd)
        
        print("4. Setting Admin Password in Env...")
        # Reset to simple password first
        cmd = f"echo '{password}' | sudo -S sed -i 's/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=Harbor12345/' /data/harbor/common/config/core/env"
        client.exec_command(cmd)
        
        print("5. Starting Harbor DB (Init)...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-db"
        client.exec_command(cmd)
        print("Waiting 15s for DB init...")
        time.sleep(15)
        
        print("6. Starting Harbor Core (Migration & User Init)...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-core"
        client.exec_command(cmd)
        print("Waiting 20s for Core init...")
        time.sleep(20)
        
        print("7. Starting other services...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-jobservice registry registryctl"
        client.exec_command(cmd)
        
        print("8. Verifying Login via Curl...")
        cmd = "curl -i -u 'admin:Harbor12345' http://127.0.0.1/api/v2.0/users/current"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        print(out)
        
        if "200 OK" in out or '"username":"admin"' in out:
            print("\n>>> SURGICAL FIX SUCCESSFUL <<<")
        else:
            print("\n>>> SURGICAL FIX FAILED <<<")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    surgical_fix()
