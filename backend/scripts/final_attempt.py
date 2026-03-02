
import paramiko
import sys
import time

def final_attempt():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        
        print("1. Checking Login Status (admin:Harbor12345)...")
        cmd = "curl -i -u 'admin:Harbor12345' http://127.0.0.1/api/v2.0/users/current"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        print(out)
        
        if "200 OK" in out:
            print("LOGIN WORKS!")
            return

        print("\nLogin Failed. Overwriting JOBSERVICE_SECRET to 'Harbor12345'...")
        
        # Overwrite Secret File
        cmd = f"echo '{password}' | sudo -S bash -c \"printf 'Harbor12345' > /data/harbor/common/config/secret/jobservice_secret\""
        client.exec_command(cmd)
        
        # Update Core Env
        cmd = f"echo '{password}' | sudo -S sed -i 's/^JOBSERVICE_SECRET=.*/JOBSERVICE_SECRET=Harbor12345/' /data/harbor/common/config/core/env"
        client.exec_command(cmd)
        
        # Update JobService Env
        cmd = f"echo '{password}' | sudo -S sed -i 's/^JOBSERVICE_SECRET=.*/JOBSERVICE_SECRET=Harbor12345/' /data/harbor/common/config/jobservice/env"
        client.exec_command(cmd)
        
        print("Restarting Core & JobService...")
        cmd = f"echo '{password}' | sudo -S docker restart harbor-core harbor-jobservice"
        client.exec_command(cmd)
        
        print("Waiting 20s...")
        time.sleep(20)
        
        print("2. Re-Checking Login Status (admin:Harbor12345)...")
        cmd = "curl -i -u 'admin:Harbor12345' http://127.0.0.1/api/v2.0/users/current"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        print(out)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    final_attempt()
