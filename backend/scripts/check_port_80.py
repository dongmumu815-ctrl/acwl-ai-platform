
import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Checking port 80 usage...")
        cmd = f"echo '{PASS}' | sudo -S netstat -tulpn | grep :80"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        print(out)
        
        if not out:
             # Try ss if netstat output is empty or command missing
             print("Trying ss...")
             cmd = f"echo '{PASS}' | sudo -S ss -tulpn | grep :80"
             stdin, stdout, stderr = ssh.exec_command(cmd)
             print(stdout.read().decode())

        print("\nChecking docker ps for nginx...")
        cmd = f"echo '{PASS}' | sudo -S docker ps | grep nginx"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\nChecking for apache service...")
        cmd = f"echo '{PASS}' | sudo -S systemctl status apache2"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        cmd = f"echo '{PASS}' | sudo -S systemctl status httpd"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
