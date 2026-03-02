
import paramiko
import sys
import time

def reset_with_strong_password():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        
        print("1. Stopping Harbor...")
        cmd = f"echo '{password}' | sudo -S docker stop harbor-core harbor-jobservice harbor-db"
        client.exec_command(cmd)
        time.sleep(5)
        
        print("2. Wiping DB...")
        cmd = f"echo '{password}' | sudo -S rm -rf /data/harbor/database/*"
        client.exec_command(cmd)
        
        print("3. Updating Password to Stronger One (Harbor12345!)...")
        new_pass = "Harbor12345!"
        cmd = f"echo '{password}' | sudo -S sed -i \"s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD='{new_pass}'/\" /data/harbor/common/config/core/env"
        client.exec_command(cmd)
        
        print("4. Fixing Permissions on SecretKey (just in case)...")
        cmd = f"echo '{password}' | sudo -S chmod 644 /data/harbor/common/config/core/certificates/secretkey"
        client.exec_command(cmd)
        cmd = f"echo '{password}' | sudo -S chown 10000:10000 /data/harbor/common/config/core/certificates/secretkey"
        client.exec_command(cmd)
        
        print("5. Starting DB...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-db"
        client.exec_command(cmd)
        time.sleep(15)
        
        print("6. Starting Core...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-core"
        client.exec_command(cmd)
        time.sleep(20)
        
        print("7. Starting JobService...")
        cmd = f"echo '{password}' | sudo -S docker start harbor-jobservice"
        client.exec_command(cmd)
        
        print("8. Verifying Login...")
        cmd = "curl -i -u 'admin:Harbor12345!' http://127.0.0.1/api/v2.0/users/current"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    reset_with_strong_password()
