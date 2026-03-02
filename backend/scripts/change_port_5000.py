
import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Updating docker-compose.yml to use port 5000...")
        # Replace port 80:8080 with 5000:8080
        cmd = f"echo '{PASS}' | sudo -S sed -i 's|- 80:8080|- 5000:8080|g' /data/harbor/docker-compose.yml"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print("Updating EXT_ENDPOINT in core/env...")
        # Update EXT_ENDPOINT to use port 5000
        cmd = f"echo '{PASS}' | sudo -S sed -i 's|EXT_ENDPOINT=http://10.20.1.204|EXT_ENDPOINT=http://10.20.1.204:5000|g' /data/harbor/common/config/core/env"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print("Restarting Harbor...")
        cmd = f"echo '{PASS}' | sudo -S cd /data/harbor && docker compose down && docker compose up -d"
        # Using full path to docker compose or docker-compose depending on version
        # Let's try standard docker compose first
        cmd = f"echo '{PASS}' | sudo -S sh -c 'cd /data/harbor && docker compose down && docker compose up -d'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("Harbor restarted on port 5000.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
