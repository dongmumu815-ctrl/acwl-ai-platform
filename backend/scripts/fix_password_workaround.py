import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Workaround: Set Env -> Restart -> Fix DB (No Restart) ===")
    
    # 1. Set ADMIN_PASSWORD in env file
    print("Setting ADMIN_PASSWORD=Harbor12345 in env file...")
    # Remove existing if any, then append
    cmd = f"echo '{PASS}' | sudo -S sed -i '/ADMIN_PASSWORD/d' /data/harbor/common/config/core/env"
    ssh.exec_command(cmd)
    cmd = f"echo '{PASS}' | sudo -S bash -c 'echo \"ADMIN_PASSWORD=Harbor12345\" >> /data/harbor/common/config/core/env'"
    ssh.exec_command(cmd)
    
    # 2. Recreate Core (to apply env)
    print("Recreating Core to apply env...")
    cmd = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d --force-recreate core"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    print("Waiting for Core (20s)...")
    time.sleep(20)
    
    # 3. Check DB (Should be SHA256 now)
    print("Checking DB (Expect SHA256)...")
    query = "SELECT user_id, username, password, password_version FROM harbor_user WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 4. Overwrite with Bcrypt
    print("Overwriting with Bcrypt Hash...")
    # Hash from previous success: $2a$12$96AMvgrfeGMfb8xXNWueP.hNtiNHXPqZ2r0q7pFKj8dW3nFLqeLJ6
    escaped_hash = r"\$2a\$12\$96AMvgrfeGMfb8xXNWueP.hNtiNHXPqZ2r0q7pFKj8dW3nFLqeLJ6"
    
    query = f"UPDATE harbor_user SET password='{escaped_hash}', salt='', password_version='v2' WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 5. Verify DB
    print("Verifying DB Update...")
    query = "SELECT user_id, username, password, password_version FROM harbor_user WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 6. Verify Login (Immediate)
    print("Verifying Login (Immediate)...")
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
