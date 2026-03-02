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
        
        print("Restarting Registry to clear logs...")
        cmd = f"echo '{PASS}' | sudo -S docker restart registry"
        ssh.exec_command(cmd)
        
        print("Waiting for startup (10s)...")
        time.sleep(10)
        
        # Make a request
        print("Making request with Token...")
        # Need to fetch a token first
        cmd = f"echo '{PASS}' | sudo -S curl -s -u 'admin:Harbor12345' 'http://127.0.0.1:5000/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry&scope=registry:catalog:*'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        token_json = stdout.read().decode()
        import json
        try:
            token = json.loads(token_json)['token']
        except:
            print("Failed to get token")
            print(token_json)
            return

        cmd = f"echo '{PASS}' | sudo -S curl -v -H 'Authorization: Bearer {token}' http://127.0.0.1:5000/v2/"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("Request Done.")
        print(stderr.read().decode()) # Print curl verbose output
        
        # Read log
        print("Registry Logs:")
        cmd = f"echo '{PASS}' | sudo -S docker logs registry"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
