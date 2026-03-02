import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Checking MD5 of keys/certs on Host vs Containers...")
        
        # Host files
        cmd = f"echo '{PASS}' | sudo -S md5sum /data/harbor/common/config/core/private_key.pem /data/harbor/common/config/registry/root.crt"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("Host:\n" + stdout.read().decode())
        
        # Core Container
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-core md5sum /etc/core/private_key.pem"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("Core Container:\n" + stdout.read().decode())
        
        # Registry Container
        cmd = f"echo '{PASS}' | sudo -S docker exec registry md5sum /etc/registry/root.crt"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("Registry Container:\n" + stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
