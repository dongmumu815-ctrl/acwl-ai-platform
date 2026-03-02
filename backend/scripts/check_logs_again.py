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
        
        print("\n=== Registry Logs (Tail 100) ===")
        # Filter for notifications or errors
        cmd = f"echo '{PASS}' | sudo -S docker logs --tail 100 registry"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("\n=== Harbor Core Logs (Tail 100) ===")
        cmd = f"echo '{PASS}' | sudo -S docker logs --tail 100 harbor-core"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
