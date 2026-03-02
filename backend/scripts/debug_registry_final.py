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
        
        print("Enabling Debug Logs in Registry...")
        cmd = f"echo '{PASS}' | sudo -S sed -i 's|level: info|level: debug|g' /data/harbor/common/config/registry/config.yml"
        ssh.exec_command(cmd)
        
        print("Restarting Registry...")
        cmd = f"echo '{PASS}' | sudo -S docker restart registry"
        ssh.exec_command(cmd)
        time.sleep(3)
        
        print("Tail Logs before request...")
        cmd = f"echo '{PASS}' | sudo -S docker logs --tail 0 -f registry > /tmp/registry_debug.log 2>&1 & echo $!"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        pid = stdout.read().decode().strip()
        print(f"Log tailing PID: {pid}")
        
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
            return

        cmd = f"echo '{PASS}' | sudo -S curl -v -H 'Authorization: Bearer {token}' http://127.0.0.1:5000/v2/"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("Request Done.")
        
        time.sleep(2)
        # Kill tail
        cmd = f"echo '{PASS}' | sudo -S kill {pid}"
        ssh.exec_command(cmd)
        
        # Read log
        print("Registry Debug Logs:")
        cmd = f"echo '{PASS}' | sudo -S cat /tmp/registry_debug.log"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
