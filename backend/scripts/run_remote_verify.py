import paramiko
import os

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        # Upload script
        sftp = ssh.open_sftp()
        local_path = "backend/scripts/verify_token_payload.py"
        remote_path = "/tmp/verify_token_payload.py"
        sftp.put(local_path, remote_path)
        sftp.close()
        
        print("Installing dependencies...")
        # Try apt first for system packages
        cmd = f"echo '{PASS}' | sudo -S apt-get update && sudo -S apt-get install -y python3-pip python3-cryptography python3-jwt"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        if "python3-jwt" in out or "python3-jwt" in err: # Installed via apt
             pass
        else: # Try pip
             cmd = f"echo '{PASS}' | sudo -S pip3 install pyjwt cryptography requests"
             ssh.exec_command(cmd)

        print("Running verification script...")
        cmd = f"echo '{PASS}' | sudo -S python3 /tmp/verify_token_payload.py"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
