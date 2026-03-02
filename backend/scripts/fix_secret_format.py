
import paramiko
import sys
import time

def fix_secret_format():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    # 16 bytes of '1234567890123456' base64 encoded
    BASE64_KEY = "MTIzNDU2Nzg5MDEyMzQ1Ng==" 
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print(f"Connected to {hostname}.")
        
        print("1. Stopping Harbor Services...")
        cmd = f"echo '{password}' | sudo -S docker stop harbor-core harbor-jobservice harbor-db registry registryctl"
        client.exec_command(cmd)
        time.sleep(5)
        
        print("2. Overwriting 'secretkey' with valid Base64 string...")
        # Write clean key - use printf to guarantee no newline
        cmd = f"echo '{password}' | sudo -S bash -c \"printf '{BASE64_KEY}' > /data/harbor/common/config/core/certificates/secretkey\""
        client.exec_command(cmd)
        
        # Permissions
        cmd = f"echo '{password}' | sudo -S chmod 644 /data/harbor/common/config/core/certificates/secretkey"
        client.exec_command(cmd)
        cmd = f"echo '{password}' | sudo -S chown 10000:10000 /data/harbor/common/config/core/certificates/secretkey"
        client.exec_command(cmd)
        
        print("3. Fixing JobService Secret (Consistency)...")
        cmd = f"echo '{password}' | sudo -S bash -c \"printf 'Harbor12345' > /data/harbor/common/config/secret/jobservice_secret\""
        client.exec_command(cmd)
        
        # Update Envs
        print("4. Updating Environment Variables...")
        cmd = f"echo '{password}' | sudo -S sed -i 's/^JOBSERVICE_SECRET=.*/JOBSERVICE_SECRET=Harbor12345/' /data/harbor/common/config/core/env"
        client.exec_command(cmd)
        cmd = f"echo '{password}' | sudo -S sed -i 's/^JOBSERVICE_SECRET=.*/JOBSERVICE_SECRET=Harbor12345/' /data/harbor/common/config/jobservice/env"
        client.exec_command(cmd)
        
        # Reset Password in Env just in case
        cmd = f"echo '{password}' | sudo -S sed -i 's/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=Harbor12345/' /data/harbor/common/config/core/env"
        client.exec_command(cmd)
        
        print("5. Wiping Database (Final Reset)...")
        cmd = f"echo '{password}' | sudo -S rm -rf /data/harbor/database/*"
        client.exec_command(cmd)
        
        print("6. Starting Harbor DB...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-db"
        client.exec_command(cmd)
        print("Waiting 15s...")
        time.sleep(15)
        
        print("7. Starting Harbor Core...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-core"
        client.exec_command(cmd)
        print("Waiting 25s...")
        time.sleep(25)
        
        print("8. Starting other services...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-jobservice registry registryctl"
        client.exec_command(cmd)
        
        print("9. Verifying Login via Curl...")
        cmd = "curl -i -u 'admin:Harbor12345' http://127.0.0.1/api/v2.0/users/current"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        print(out)
        
        if "200 OK" in out or '"username":"admin"' in out:
            print("\n>>> FIX SUCCESSFUL <<<")
        else:
            print("\n>>> FIX FAILED <<<")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    fix_secret_format()
