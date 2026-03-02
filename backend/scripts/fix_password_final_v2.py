import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Fixing Admin Password (Correct Escaping + Service Name) ===")
    
    # 1. Recreate Core Container (Service name: core)
    print("Recreating Harbor Core (compose up -d --force-recreate core)...")
    # Note: 'core' is the service name in standard harbor-compose.yml, let's verify if user uses standard names.
    # Previous logs showed 'harbor-core' container name.
    # If the file is /data/harbor/docker-compose.yml, usually service is 'core'.
    cmd = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d --force-recreate core"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    print("Waiting for Core (20s)...")
    time.sleep(20)
    
    # 2. Generate Hash ($2a$)
    cmd = """python3 -c "import crypt; print(crypt.crypt('Harbor12345', crypt.mksalt(crypt.METHOD_BLOWFISH)))" """
    stdin, stdout, stderr = ssh.exec_command(cmd)
    raw_hash = stdout.read().decode().strip()
    if raw_hash.startswith("$2b$"):
        new_hash = "$2a$" + raw_hash[4:]
    else:
        new_hash = raw_hash
    print(f"New Hash (Raw): {new_hash}")
    
    # ESCAPE $ for Shell
    escaped_hash = new_hash.replace("$", "\\$")
    print(f"New Hash (Escaped): {escaped_hash}")
    
    # 3. Update DB
    print("Updating DB...")
    # We use single quotes for SQL string, and escaped hash for shell
    query = f"UPDATE harbor_user SET password='{escaped_hash}', salt='', password_version='v2' WHERE username='admin';"
    # Also need to escape the query itself if it contains other shell-sensitive chars? No, just $
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 4. Verify DB State (Check for truncation)
    print("Verifying DB State...")
    query = "SELECT user_id, username, password, password_version FROM harbor_user WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 5. Verify Login
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
