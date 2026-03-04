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
        
        # 1. Check storage timestamp
        print("\n=== Storage Check (ls -lR) ===")
        cmd = f"echo '{PASS}' | sudo -S ls -lR /data/harbor/registry/docker/registry/v2/repositories/prod"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        if not out:
            print("No files found or error reading directory.")
            print(stderr.read().decode())
        else:
            print(out[-1000:]) # Last 1000 chars to see recent files
            
        # 2. Check DB Artifacts count
        print("\n=== DB Artifacts Check ===")
        sql = "select count(*) from artifact;"
        cmd = f"echo '{PASS}' | sudo -S docker exec postgres psql -U postgres -d registry -c \"{sql}\""
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

        # 3. Check Registry Logs for Notifications
        print("\n=== Registry Notification Logs ===")
        # Look for "response.status" which often indicates notification result
        cmd = f"echo '{PASS}' | sudo -S docker logs --tail 50 registry"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
