import paramiko
import time
import hashlib
import secrets

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Fixing Admin Password (SHA256 Strategy) ===")
    
    # 1. Generate Salt and Hash
    salt = secrets.token_hex(16) # 32 chars
    password = "Harbor12345"
    # Try salt + password
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    
    print(f"Salt: {salt}")
    print(f"Hash: {h}")
    
    # 2. Update DB
    print("Updating DB...")
    query = f"UPDATE harbor_user SET password='{h}', salt='{salt}', password_version='sha256' WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    # 3. Verify DB
    print("Verifying DB...")
    query = "SELECT user_id, username, password, salt, password_version FROM harbor_user WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 4. Verify Login
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
