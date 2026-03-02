import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== FINAL FIX: Resize Column & Update Password ===")
    
    # 1. Resize Column (with error checking)
    print("Resizing Password Column to varchar(128)...")
    query = "ALTER TABLE harbor_user ALTER COLUMN password TYPE varchar(128);"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    print(f"STDOUT: {out}")
    if err:
        print(f"STDERR: {err}")
        
    # 2. Update Password (Bcrypt)
    # Using the hash generated previously: $2a$12$dtISKng6pR8HcyVyJoD7dOiPSVH8swIbo9/2r6JeUfyt4nUQyVQSG
    # Escaped for shell: \$2a\$12\$dtISKng6pR8HcyVyJoD7dOiPSVH8swIbo9/2r6JeUfyt4nUQyVQSG
    escaped_hash = r"\$2a\$12\$dtISKng6pR8HcyVyJoD7dOiPSVH8swIbo9/2r6JeUfyt4nUQyVQSG"
    
    print("Updating Password to Bcrypt...")
    query = f"UPDATE harbor_user SET password='{escaped_hash}', salt='', password_version='v2' WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    print(f"STDOUT: {out}")
    if err:
        print(f"STDERR: {err}")
        
    # 3. Verify DB State
    print("Verifying DB State...")
    query = "SELECT user_id, username, password, password_version FROM harbor_user WHERE username='admin';"
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
