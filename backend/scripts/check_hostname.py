
import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Fixing hostname in core/env...")
        # Update EXT_ENDPOINT to use IP
        cmd = f"echo '{PASS}' | sudo -S sed -i 's|EXT_ENDPOINT=http://reg.mydomain.com|EXT_ENDPOINT=http://10.20.1.204|g' /data/harbor/common/config/core/env"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print("Restarting core and jobservice...")
        cmd = f"echo '{PASS}' | sudo -S docker restart harbor-core harbor-jobservice"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        print("Hostname updated to 10.20.1.204")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
