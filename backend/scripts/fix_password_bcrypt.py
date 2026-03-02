import paramiko
import time
import json

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Fixing Admin Password (Force Bcrypt) ===")
    
    # 1. Generate Hash
    cmd = """python3 -c "import crypt; print(crypt.crypt('Harbor12345', crypt.mksalt(crypt.METHOD_BLOWFISH)))" """
    stdin, stdout, stderr = ssh.exec_command(cmd)
    raw_hash = stdout.read().decode().strip()
    if raw_hash.startswith("$2b$"):
        new_hash = "$2a$" + raw_hash[4:]
    else:
        new_hash = raw_hash
    print(f"New Hash: {new_hash}")
    
    # 2. Update DB
    print("Updating DB...")
    query = f"UPDATE harbor_user SET password='{new_hash}', salt='', password_version='v2' WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 3. Check and Remove Env Var
    print("Checking Env File...")
    cmd = f"echo '{PASS}' | sudo -S cat /data/harbor/common/config/core/env"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    env_content = stdout.read().decode()
    
    if "ADMIN_PASSWORD" in env_content:
        print("Removing ADMIN_PASSWORD from env file...")
        cmd = f"echo '{PASS}' | sudo -S sed -i '/ADMIN_PASSWORD/d' /data/harbor/common/config/core/env"
        ssh.exec_command(cmd)
    else:
        print("ADMIN_PASSWORD not found in env file (Good).")
        
    # 4. Restart Core
    print("Restarting Harbor Core...")
    cmd = f"echo '{PASS}' | sudo -S docker restart harbor-core"
    ssh.exec_command(cmd)
    
    print("Waiting for Core (15s)...")
    time.sleep(15)
    
    # 5. Verify DB State
    print("Verifying DB State...")
    query = "SELECT user_id, username, password, password_version FROM harbor_user WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 6. Verify Login
    print("Verifying Login...")
    token_url = "http://10.20.1.204:5000/service/token?service=harbor-registry&client_id=docker&offline_token=true"
    cmd = f"curl -v -u admin:Harbor12345 '{token_url}' 2>&1"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    print(out)
    
    if "HTTP/1.1 200 OK" in out:
        print("SUCCESS: Login Verified!")
    else:
        print("FAILURE: Login Failed.")

    ssh.close()

if __name__ == "__main__":
    main()
