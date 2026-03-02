import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {HOST}...")
    try:
        ssh.connect(HOST, username=USER, password=PASS)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # 1. Check /v2/ Headers (Realm & Service)
    print("\n=== Checking /v2/ Headers (Realm & Service) ===")
    cmd = "curl -v http://10.20.1.204:5000/v2/ 2>&1 | grep Www-Authenticate"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

    # 2. Try Docker Login
    print("\n=== Attempting Docker Login (on server) ===")
    # Note: --password-stdin is safer
    cmd = f"echo 'Harbor12345' | sudo -S docker login 10.20.1.204:5000 -u admin --password-stdin"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    print("STDOUT:", out)
    print("STDERR:", err)

    # 3. If login failed, check Registry Logs
    print("\n=== Registry Logs (Tail 50) ===")
    cmd = f"echo '{PASS}' | sudo -S docker logs --tail 50 registry"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())

    # 4. Check Cert Match
    print("\n=== Checking Certificate Match (Modulus) ===")
    # Core Private Key
    cmd1 = f"echo '{PASS}' | sudo -S openssl rsa -noout -modulus -in /data/harbor/common/config/core/private_key.pem | openssl md5"
    # Registry Root Cert
    cmd2 = f"echo '{PASS}' | sudo -S openssl x509 -noout -modulus -in /data/harbor/common/config/registry/root.crt | openssl md5"
    
    print("Core Private Key MD5:")
    stdin, stdout, stderr = ssh.exec_command(cmd1)
    print(stdout.read().decode().strip())
    
    print("Registry Root Cert MD5:")
    stdin, stdout, stderr = ssh.exec_command(cmd2)
    print(stdout.read().decode().strip())

    ssh.close()

if __name__ == "__main__":
    main()
