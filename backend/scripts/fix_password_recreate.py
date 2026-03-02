import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Fixing Admin Password (Recreate Container) ===")
    
    # 1. Remove ADMIN_PASSWORD from env file
    print("Removing ADMIN_PASSWORD from env file...")
    cmd = f"echo '{PASS}' | sudo -S sed -i '/ADMIN_PASSWORD/d' /data/harbor/common/config/core/env"
    ssh.exec_command(cmd)
    
    # 2. Recreate Core Container (Force env reload)
    print("Recreating Harbor Core (compose up -d --force-recreate)...")
    cmd = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d --force-recreate harbor-core"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    print("Waiting for Core (15s)...")
    time.sleep(15)
    
    # 3. Generate Hash ($2a$)
    cmd = """python3 -c "import crypt; print(crypt.crypt('Harbor12345', crypt.mksalt(crypt.METHOD_BLOWFISH)))" """
    stdin, stdout, stderr = ssh.exec_command(cmd)
    raw_hash = stdout.read().decode().strip()
    if raw_hash.startswith("$2b$"):
        new_hash = "$2a$" + raw_hash[4:]
    else:
        new_hash = raw_hash
    print(f"New Hash: {new_hash}")
    
    # 4. Update DB
    print("Updating DB...")
    query = f"UPDATE harbor_user SET password='{new_hash}', salt='', password_version='v2' WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 5. Verify DB State (Before Login)
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
