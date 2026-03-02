import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Fixing Admin Password (htpasswd on Host) ===")
    
    # 1. Install apache2-utils
    print("Installing apache2-utils...")
    cmd = f"echo '{PASS}' | sudo -S apt-get update && echo '{PASS}' | sudo -S apt-get install -y apache2-utils"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 2. Generate Hash
    print("Generating Hash...")
    cmd = "htpasswd -B -n -b admin Harbor12345"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    # admin:$2y$05$.....
    
    if ":" in out:
        hash_val = out.split(":")[1]
        print(f"Generated Hash: {hash_val}")
        
        # Harbor uses $2a$, htpasswd might give $2y$. Convert.
        if hash_val.startswith("$2y$"):
            final_hash = "$2a$" + hash_val[4:]
        else:
            final_hash = hash_val
            
        print(f"Final Hash: {final_hash}")
        escaped_hash = final_hash.replace("$", "\\$")
        
        # 3. Update DB
        print("Updating DB...")
        query = f"UPDATE harbor_user SET password='{escaped_hash}', salt='', password_version='v2' WHERE username='admin';"
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        # 4. Remove Env Var (To prevent reset)
        print("Removing ADMIN_PASSWORD from env file...")
        cmd = f"echo '{PASS}' | sudo -S sed -i '/ADMIN_PASSWORD/d' /data/harbor/common/config/core/env"
        ssh.exec_command(cmd)
        
        # 5. Restart Core
        print("Restarting Core...")
        cmd = f"echo '{PASS}' | sudo -S docker restart harbor-core"
        ssh.exec_command(cmd)
        
        print("Waiting for Core (20s)...")
        time.sleep(20)
        
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
            
    else:
        print(f"Failed to generate hash: {out}")

    ssh.close()

if __name__ == "__main__":
    main()
