import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Fixing Registry Realm...")
        cmd = f"echo '{PASS}' | sudo -S sed -i 's|realm: http://reg.mydomain.com/service/token|realm: http://10.20.1.204:5000/service/token|g' /data/harbor/common/config/registry/config.yml"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print("Fixing Private Key Format (Force PKCS#1)...")
        # openssl rsa -in key.pem -out key.pem will convert PKCS#8 to PKCS#1 on many versions
        # If openssl is 3.0+, we need -traditional
        cmd = f"echo '{PASS}' | sudo -S openssl rsa -in /data/harbor/common/config/core/private_key.pem -out /data/harbor/common/config/core/private_key.pem"
        # Check if we need -traditional
        # We can try appending it if the first one fails or just blindly try
        # But let's check version first?
        # Let's just run it. If it fails, we catch it.
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        print(out)
        print(err)
        
        # Verify header
        cmd = f"echo '{PASS}' | sudo -S head -n 1 /data/harbor/common/config/core/private_key.pem"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        header = stdout.read().decode().strip()
        print(f"New Header: {header}")
        
        if "BEGIN RSA PRIVATE KEY" not in header:
            print("Trying with -traditional flag...")
            cmd = f"echo '{PASS}' | sudo -S openssl rsa -in /data/harbor/common/config/core/private_key.pem -out /data/harbor/common/config/core/private_key.pem -traditional"
            ssh.exec_command(cmd)
            
            cmd = f"echo '{PASS}' | sudo -S head -n 1 /data/harbor/common/config/core/private_key.pem"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(f"New Header 2: {stdout.read().decode().strip()}")

        print("Restarting all services...")
        cmd = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml restart"
        ssh.exec_command(cmd)
        
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
