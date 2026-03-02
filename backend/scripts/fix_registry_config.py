import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Updating Registry Config...")
        # Replace http://reg.mydomain.com/service/token with http://10.20.1.204:5000/service/token
        cmd = f"echo '{PASS}' | sudo -S sed -i 's|realm: http://reg.mydomain.com/service/token|realm: http://10.20.1.204:5000/service/token|g' /data/harbor/common/config/registry/config.yml"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print("Restarting Registry...")
        cmd = f"echo '{PASS}' | sudo -S docker restart registry"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        print("Done. Waiting for startup...")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
