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
        
        print("Waiting for Harbor Core to be healthy...")
        # Check health
        for i in range(12): # Wait up to 60s
            cmd = f"echo '{PASS}' | sudo -S docker inspect --format '{{{{.State.Health.Status}}}}' harbor-core"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            status = stdout.read().decode().strip()
            print(f"Core Status: {status}")
            if status == "healthy":
                break
            time.sleep(5)
            
        print("\nTesting Docker Login...")
        # Note: insecure-registry must be configured on the client (the remote machine itself)
        # We assume 127.0.0.1:5000 works without config or we use localhost
        
        cmd = f"echo '{PASS}' | sudo -S docker login -u admin -p Harbor12345 127.0.0.1:5000"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        out = stdout.read().decode()
        err = stderr.read().decode()
        print("STDOUT:", out)
        print("STDERR:", err)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
