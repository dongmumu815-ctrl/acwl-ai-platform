import paramiko
import json

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("1. Fetching Token...")
        # Note: Use 127.0.0.1:5000 as configured in realm? No, realm is 10.20.1.204:5000
        # But we can access token service via localhost:5000/service/token?
        # Let's try to access the token service directly
        cmd = f"echo '{PASS}' | sudo -S curl -v -u 'admin:Harbor12345' 'http://127.0.0.1:5000/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry&scope=registry:catalog:*'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        
        if "HTTP/1.1 200 OK" not in err and "HTTP/1.1 200" not in err:
            print("Failed to get token!")
            print(out)
            print(err)
            return

        token_data = json.loads(out)
        token = token_data.get('token')
        print(f"Got Token: {token[:20]}...")
        
        # 2. Verify Token locally on remote
        print("\n2. Verifying Token Signature...")
        verify_script = f"""
import jwt
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import sys

token = '{token}'
try:
    with open('/data/harbor/common/config/registry/root.crt', 'rb') as f:
        cert = load_pem_x509_certificate(f.read(), default_backend())
    
    decoded = jwt.decode(token, cert.public_key(), algorithms=['RS256'], audience='harbor-registry')
    print('SUCCESS: Token Valid')
    print(decoded)
except Exception as e:
    print(f'FAILURE: {e}')
"""
        # Escape double quotes inside the script if any (none here except in f-string above)
        # But wait, we are wrapping in double quotes for the shell command
        # So we should escape double quotes inside verify_script?
        # Actually, using single quotes inside verify_script is safer if we wrap with double quotes in shell
        
        cmd = f"echo '{PASS}' | sudo -S python3 -c \"{verify_script}\""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 3. Use Token to access Registry
        print("\n3. Accessing Registry with Token...")
        cmd = f"echo '{PASS}' | sudo -S curl -v -H 'Authorization: Bearer {token}' http://127.0.0.1:5000/v2/"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
