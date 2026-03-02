import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Trying Simpler Password (admin123) ===")
    
    # 1. Update Env File
    print("Setting ADMIN_PASSWORD=admin123...")
    cmd = f"echo '{PASS}' | sudo -S sed -i '/ADMIN_PASSWORD/d' /data/harbor/common/config/core/env"
    ssh.exec_command(cmd)
    cmd = f"echo '{PASS}' | sudo -S bash -c 'echo \"ADMIN_PASSWORD=admin123\" >> /data/harbor/common/config/core/env'"
    ssh.exec_command(cmd)
    
    # 2. Recreate Core
    print("Recreating Core...")
    cmd = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d --force-recreate core"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    print("Waiting for Core (20s)...")
    time.sleep(20)
    
    # 3. Verify Login
    print("Verifying Login (admin / admin123)...")
    token_url = "http://10.20.1.204:5000/service/token?service=harbor-registry&client_id=docker&offline_token=true"
    cmd = f"curl -v -u admin:admin123 '{token_url}' 2>&1"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    print(out)
    
    if "HTTP/1.1 200 OK" in out:
        print("SUCCESS: Login Verified with admin123!")
    else:
        print("FAILURE: Login Failed with admin123.")

    ssh.close()

if __name__ == "__main__":
    main()
