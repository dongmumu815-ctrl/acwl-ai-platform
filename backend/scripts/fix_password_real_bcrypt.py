import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Checking for python3-bcrypt on remote ===")
    
    cmd = "python3 -c 'import bcrypt; print(bcrypt.hashpw(b\"Harbor12345\", bcrypt.gensalt()).decode())'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode()
    
    if out and out.startswith("$2b$"):
        print(f"Success! Generated hash: {out}")
        real_bcrypt_hash = out
    else:
        print(f"bcrypt not installed: {err}")
        print("Installing python3-bcrypt...")
        cmd = f"echo '{PASS}' | sudo -S apt-get update && echo '{PASS}' | sudo -S apt-get install -y python3-bcrypt"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        # Check again
        cmd = "python3 -c 'import bcrypt; print(bcrypt.hashpw(b\"Harbor12345\", bcrypt.gensalt()).decode())'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode().strip()
        if out and out.startswith("$2b$"):
             print(f"Success after install! Hash: {out}")
             real_bcrypt_hash = out
        else:
             print("Still failed. Fallback to crypt module.")
             # Fallback
             cmd = """python3 -c "import crypt; print(crypt.crypt('Harbor12345', crypt.mksalt(crypt.METHOD_BLOWFISH)))" """
             stdin, stdout, stderr = ssh.exec_command(cmd)
             real_bcrypt_hash = stdout.read().decode().strip()

    # Convert $2b$ to $2a$ (Harbor prefers 2a usually)
    if real_bcrypt_hash.startswith("$2b$"):
        final_hash = "$2a$" + real_bcrypt_hash[4:]
    else:
        final_hash = real_bcrypt_hash
        
    print(f"Final Hash for DB: {final_hash}")
    escaped_hash = final_hash.replace("$", "\\$")
    
    # Update DB
    print("Updating DB...")
    query = f"UPDATE harbor_user SET password='{escaped_hash}', salt='', password_version='v2' WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # Restart Core
    print("Restarting Core...")
    cmd = f"echo '{PASS}' | sudo -S docker restart harbor-core"
    ssh.exec_command(cmd)
    
    print("Waiting for Core (20s)...")
    time.sleep(20)
    
    # Verify Login
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
