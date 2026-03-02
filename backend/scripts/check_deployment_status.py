import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Checking containers...")
        cmd = f"echo '{PASS}' | sudo -S docker ps --format '{{{{.Names}}}} {{{{.Status}}}}'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\nChecking Port 5000...")
        cmd = f"echo '{PASS}' | sudo -S netstat -tulpn | grep 5000"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\nChecking Private Key Format...")
        cmd = f"echo '{PASS}' | sudo -S head -n 1 /data/harbor/common/config/core/private_key.pem"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\nChecking Registry Realm...")
        cmd = f"echo '{PASS}' | sudo -S grep realm /data/harbor/common/config/registry/config.yml"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
