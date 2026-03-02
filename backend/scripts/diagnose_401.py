import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Diagnosing 401 Unauthorized ===")
    
    # 1. Check Core Logs (Last 50 lines)
    print("\n--- Harbor Core Logs (Login Failure) ---")
    cmd = f"echo '{PASS}' | sudo -S docker logs --tail 50 harbor-core"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 2. Check DB Content
    print("\n--- DB Admin User ---")
    query = "SELECT user_id, username, password, salt, password_version FROM harbor_user WHERE username='admin';"
    cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"{query}\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    main()
