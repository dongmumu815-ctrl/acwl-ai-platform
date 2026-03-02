import paramiko
import sys

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS)
        
        # Get private key
        cmd = f"cat /data/harbor/common/config/core/private_key.pem"
        stdin, stdout, stderr = client.exec_command(cmd)
        key = stdout.read().decode()
        print(key)
        
        # Also check container names to be sure about DB
        cmd = f"echo '{PASS}' | sudo -S docker ps --format '{{{{.Names}}}}'"
        stdin, stdout, stderr = client.exec_command(cmd)
        print("\n--- Containers ---")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
