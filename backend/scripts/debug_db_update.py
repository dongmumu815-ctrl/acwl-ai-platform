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
    
    print("=== Debugging DB Update and Env Var ===")
    
    # 1. Check Env of Running Container
    print("Checking Env of running container...")
    cmd = f"echo '{PASS}' | sudo -S docker inspect harbor-core"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    inspect_out = stdout.read().decode()
    try:
        data = json.loads(inspect_out)
        env = data[0]['Config']['Env']
        admin_pw_env = [e for e in env if e.startswith('ADMIN_PASSWORD=')]
        print(f"ADMIN_PASSWORD in Env: {admin_pw_env}")
    except Exception as e:
        print(f"Could not parse inspect output: {e}")

    # 2. Try Update DB (with stderr check)
    print("Attempting DB Update...")
    new_hash = r"\$2a\$12\$dtISKng6pR8HcyVyJoD7dOiPSVH8swIbo9/2r6JeUfyt4nUQyVQSG" # Use escaped hash
    query = f"UPDATE harbor_user SET password='{new_hash}', salt='', password_version='v2' WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    print(f"STDOUT: {out}")
    print(f"STDERR: {err}")
    
    # 3. Verify DB State
    print("Verifying DB State...")
    query = "SELECT user_id, username, password, password_version FROM harbor_user WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    main()
