
import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Checking for certificates...")
        # Check standard locations
        locations = [
            "/data/harbor/common/config/core/certificates",
            "/data/harbor/common/config/nginx",
            "/data/harbor/common/config/shared/trust-certificates"
        ]
        
        for loc in locations:
            print(f"\nChecking {loc}:")
            cmd = f"echo '{PASS}' | sudo -S ls -la {loc}"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(stdout.read().decode())
        
        # Check if nginx is listening on 8443
        print("\nChecking nginx listening ports inside container...")
        cmd = f"echo '{PASS}' | sudo -S docker exec nginx netstat -tuln"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        print(out)
        if "netstat: command not found" in out or "exec: \"netstat\": executable file not found" in out:
             # Try ss
             cmd = f"echo '{PASS}' | sudo -S docker exec nginx ss -tuln"
             stdin, stdout, stderr = ssh.exec_command(cmd)
             print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
