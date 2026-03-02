
import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("=== 1. Checking Containers ===")
        stdin, stdout, stderr = ssh.exec_command(f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml ps")
        print(stdout.read().decode())
        
        print("\n=== 2. Checking Core Logs (Tail 50) ===")
        stdin, stdout, stderr = ssh.exec_command(f"echo '{PASS}' | sudo -S docker logs --tail 50 harbor-core")
        print(stdout.read().decode())
        print(stderr.read().decode())

        print("\n=== 3. Testing Login via Curl ===")
        token_url = "http://10.20.1.204:5000/c/login"
        # Try both admin/Harbor12345 and admin/Harbor12345
        cmd = f"curl -v -X POST -H 'Content-Type: application/x-www-form-urlencoded' -d 'principal=admin&password=Harbor12345' '{token_url}' 2>&1"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
