import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Checking for python3-pip...")
        cmd = f"echo '{PASS}' | sudo -S which pip3"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        if not stdout.read():
             print("Installing pip3...")
             cmd = f"echo '{PASS}' | sudo -S apt-get update && sudo -S apt-get install -y python3-pip"
             ssh.exec_command(cmd)

        print("Installing pyjwt and cryptography...")
        cmd = f"echo '{PASS}' | sudo -S pip3 install pyjwt cryptography"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # Now run the verification script
        verify_script = """
import jwt
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import sys

try:
    # 1. Read Root Cert
    with open('/data/harbor/common/config/registry/root.crt', 'rb') as f:
        cert_data = f.read()
    
    cert = load_pem_x509_certificate(cert_data, default_backend())
    public_key = cert.public_key()
    
    # 2. Get Token (hardcoded or from stdin)
    # We will fetch a fresh token via curl
    import subprocess
    cmd = "curl -s -u 'admin:Harbor12345' 'http://127.0.0.1:5000/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry'"
    import json
    token_json = subprocess.check_output(cmd, shell=True).decode()
    token = json.loads(token_json)['token']
    
    print(f"Verifying Token: {token[:20]}...")
    
    # 3. Verify
    # Note: Harbor uses RS256
    # We need to skip audience check if we don't know it, or match it
    decoded = jwt.decode(token, public_key, algorithms=['RS256'], audience='harbor-registry')
    print("SUCCESS: Token signature is VALID.")
    print("Decoded Claims:", decoded)
    
except Exception as e:
    print("FAILURE: Token verification failed.")
    print(e)
    import traceback
    traceback.print_exc()
"""
        print("Running verification script...")
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
