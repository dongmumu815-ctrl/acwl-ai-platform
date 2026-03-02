import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {HOST}...")
    try:
        ssh.connect(HOST, username=USER, password=PASS)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    print("\n=== Docker PS (Nginx) ===")
    cmd = f"echo '{PASS}' | sudo -S docker ps -a --filter name=nginx"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

    print("\n=== Nginx Logs (Tail 20) ===")
    cmd = f"echo '{PASS}' | sudo -S docker logs --tail 20 nginx"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())

    ssh.close()

if __name__ == "__main__":
    main()
