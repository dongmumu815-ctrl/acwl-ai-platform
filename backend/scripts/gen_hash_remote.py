import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Checking for bcrypt on remote...")
        cmd = f"echo '{PASS}' | sudo -S python3 -c 'import bcrypt; print(bcrypt.hashpw(b\"Harbor12345\", bcrypt.gensalt()).decode())'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        
        if out and out.startswith("$2"):
            print(f"Generated Hash: {out}")
        else:
            print("Failed to generate hash.")
            print(f"Error: {err}")
            
            # Fallback: Check if we can install it
            # print("Installing python3-bcrypt...")
            # cmd = f"echo '{PASS}' | sudo -S apt-get update && sudo -S apt-get install -y python3-bcrypt"
            # ssh.exec_command(cmd)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
