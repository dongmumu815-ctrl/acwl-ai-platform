import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Checking for auth_basic in Nginx Config...")
        cmd = f"echo '{PASS}' | sudo -S grep -r 'auth_basic' /data/harbor/common/config/nginx/"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        if out:
            print("Found auth_basic:")
            print(out)
        else:
            print("No auth_basic found.")
            
        print("\nListing Nginx Config Directory...")
        cmd = f"echo '{PASS}' | sudo -S ls -R /data/harbor/common/config/nginx/"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
