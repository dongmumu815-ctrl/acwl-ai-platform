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
        
        # Token from previous output (pasted here for simplicity, or we can fetch again)
        # But wait, the previous output was truncated or didn't run the python verification part properly?
        # The python script was printed in the command logs but the output was empty after "Verification Output:"
        # This means the python script failed or didn't run.
        # Ah, the token_json in the python string literal might have newlines or issues.
        
        # Let's retry just the verification part with a cleaner script
        
        verify_script = """
import jwt
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import json
import subprocess

# Fetch fresh token with scope
cmd = "curl -s -u 'admin:Harbor12345' 'http://127.0.0.1:5000/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry&scope=registry:catalog:*'"
token_json = subprocess.check_output(cmd, shell=True).decode()
print(f"Token JSON: {token_json}")

try:
    token = json.loads(token_json)['token']
    
    # Load Root Cert
    with open('/data/harbor/common/config/registry/root.crt', 'rb') as f:
        cert_data = f.read()
    cert = load_pem_x509_certificate(cert_data, default_backend())
    
    # Decode
    decoded = jwt.decode(token, cert.public_key(), algorithms=['RS256'], audience='harbor-registry')
    print("SUCCESS: Token is VALID.")
    print("Claims:", json.dumps(decoded, indent=2))
    
except Exception as e:
    print("FAILURE:")
    print(e)
"""
        cmd = f"echo '{PASS}' | sudo -S python3 -c \"{verify_script}\""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
