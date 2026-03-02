import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Flushing Redis (Unlock User) ===")
    
    # Flush Redis
    print("Flushing Redis...")
    cmd = f"echo '{PASS}' | sudo -S docker exec redis redis-cli flushall"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
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
