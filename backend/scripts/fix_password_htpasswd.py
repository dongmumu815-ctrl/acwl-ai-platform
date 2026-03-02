import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Restarting Core and Verifying ===")
    
    # 1. Restart Core
    print("Restarting Harbor Core...")
    cmd = f"echo '{PASS}' | sudo -S docker restart harbor-core"
    ssh.exec_command(cmd)
    
    print("Waiting for Core (15s)...")
    time.sleep(15)
    
    # 2. Verify Login
    print("Verifying Login...")
    token_url = "http://10.20.1.204:5000/service/token?service=harbor-registry&client_id=docker&offline_token=true"
    cmd = f"curl -v -u admin:Harbor12345 '{token_url}' 2>&1"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    print(out)
    
    if "HTTP/1.1 200 OK" in out:
        print("SUCCESS: Login Verified!")
        ssh.close()
        return

    print("FAILURE: Login Failed. Trying htpasswd hash strategy...")
    
    # 3. Generate Hash using Registry's htpasswd
    print("Generating hash using htpasswd in registry container...")
    # -B: use bcrypt
    # -n: display result on stdout
    # -b: use password from command line
    cmd = f"echo '{PASS}' | sudo -S docker exec registry htpasswd -B -n -b admin Harbor12345"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    htpasswd_out = stdout.read().decode().strip() # admin:$2y$05$....
    err = stderr.read().decode()
    
    if not htpasswd_out or ":" not in htpasswd_out:
        print(f"Failed to generate hash: {htpasswd_out} {err}")
        return
        
    # Extract hash (remove 'admin:')
    new_hash = htpasswd_out.split(':')[1].strip()
    print(f"New Hash from htpasswd: {new_hash}")
    
    # Convert $2y$ to $2a$ if needed (Harbor usually prefers 2a)
    if new_hash.startswith("$2y$"):
        final_hash = "$2a$" + new_hash[4:]
    else:
        final_hash = new_hash
    print(f"Final Hash for DB: {final_hash}")
    
    # Escape for shell
    escaped_hash = final_hash.replace("$", "\\$")
    
    # 4. Update DB
    print("Updating DB...")
    query = f"UPDATE harbor_user SET password='{escaped_hash}', salt='', password_version='v2' WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    # 5. Verify Login Again
    print("Verifying Login Again...")
    cmd = f"curl -v -u admin:Harbor12345 '{token_url}' 2>&1"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    print(out)
    
    if "HTTP/1.1 200 OK" in out:
        print("SUCCESS: Login Verified with htpasswd hash!")
    else:
        print("FAILURE: Login Failed with htpasswd hash.")

    ssh.close()

if __name__ == "__main__":
    main()
