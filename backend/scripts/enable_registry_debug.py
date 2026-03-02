import paramiko
import time

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

    # 1. Update Registry Config (log level: debug)
    print("Updating Registry Config (log level: debug)...")
    cmd = f"echo '{PASS}' | sudo -S sed -i 's/level: info/level: debug/g' /data/harbor/common/config/registry/config.yml"
    ssh.exec_command(cmd)

    # 2. Restart Registry
    print("Restarting Registry...")
    cmd = f"echo '{PASS}' | sudo -S docker restart registry"
    ssh.exec_command(cmd)
    time.sleep(10)

    # 3. Verify Config inside container (optional, but good sanity check)
    cmd = f"echo '{PASS}' | sudo -S docker exec registry cat /etc/registry/config.yml | grep level"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(f"Config Check: {stdout.read().decode().strip()}")

    ssh.close()

if __name__ == "__main__":
    main()
