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
        
        # Try alternate endpoint
        print("\n=== Connectivity Check (Alternate Endpoint) ===")
        cmd = f"echo '{PASS}' | sudo -S docker exec registry curl -v http://core:8080/service/notifications/jobs/adminjob"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        print(out)
        print(err)
        
        if "401 Unauthorized" in out or "401 Unauthorized" in err:
            print("ENDPOINT EXISTS (401 is good)")
        elif "404 Not Found" in out or "404 Not Found" in err:
            print("ENDPOINT MISSING (404)")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
