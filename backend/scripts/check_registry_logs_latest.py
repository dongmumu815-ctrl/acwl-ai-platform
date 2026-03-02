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

    print("\n=== Registry Logs (Tail 100) ===")
    # Look for python-requests user agent or errors
    cmd = f"echo '{PASS}' | sudo -S docker logs --tail 100 registry"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    logs = stdout.read().decode() + stderr.read().decode()
    print(logs)

    ssh.close()

if __name__ == "__main__":
    main()
