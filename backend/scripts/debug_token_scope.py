import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Fetching Token with explicitly requested scope...")
        # Add scope parameter to the request
        # Scope format: repository:library/hello-world:pull,push
        # But for login, usually it's just getting a token, but without scope it has no access
        # Wait, docker login usually requests a token for the registry catalog or similar?
        # Actually, when we do `docker login`, the registry returns 401 with a Www-Authenticate header
        # which tells the client what scope to request.
        # Let's check what the registry returns for /v2/
        
        cmd = f"echo '{PASS}' | sudo -S curl -v http://127.0.0.1:5000/v2/"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("Registry /v2/ Response Headers:")
        print(stderr.read().decode())
        
        print("\nTrying to get token WITH scope...")
        # Usually scope is 'registry:catalog:*' for admin? or just empty for login check?
        # If 'access' is None in the token, it means no permissions were granted.
        # But for a simple login check, Docker client might just want a valid token.
        
        # Let's try requesting a specific scope like 'registry:catalog:*'
        cmd = f"echo '{PASS}' | sudo -S curl -s -u 'admin:Harbor12345' 'http://127.0.0.1:5000/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry&scope=registry:catalog:*'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        token_json = stdout.read().decode()
        print(f"\nToken Response with scope: {token_json}")
        
        # Now verify this token
        verify_script = f"""
import jwt
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import json

token_json = '{token_json}'
try:
    token = json.loads(token_json)['token']
    with open('/data/harbor/common/config/registry/root.crt', 'rb') as f:
        cert = load_pem_x509_certificate(f.read(), default_backend())
    
    decoded = jwt.decode(token, cert.public_key(), algorithms=['RS256'], audience='harbor-registry')
    print("Decoded Claims:", decoded)
except Exception as e:
    print(e)
"""
        cmd = f"echo '{PASS}' | sudo -S python3 -c \"{verify_script}\""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("Verification Output:")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
