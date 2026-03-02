
import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Verifying HTTP Registry Endpoint...")
        # Check /v2/ endpoint which should return 401 Unauthorized if working
        cmd = f"curl -i http://127.0.0.1:80/v2/"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        print(out)
        
        if "401 Unauthorized" in out:
            print("SUCCESS: Registry is reachable via HTTP (expecting 401 for unauthenticated request).")
        else:
            print("WARNING: Unexpected response from registry.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
