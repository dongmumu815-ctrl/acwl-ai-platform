import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        # The python script was failing because I didn't wrap the python code properly in the string
        # and the shell escaping might be weird.
        # Let's write the python script to a file and run it.
        
        verify_script = """
import jwt
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import json
import subprocess
import sys

try:
    # 1. Fetch Token
    cmd = "curl -s -u 'admin:Harbor12345' 'http://127.0.0.1:5000/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry&scope=registry:catalog:*'"
    output = subprocess.check_output(cmd, shell=True).decode()
    print("Token JSON Response:", output)
    
    token_data = json.loads(output)
    token = token_data.get('token')
    
    if not token:
        print("ERROR: No token found in response")
        sys.exit(1)
        
    print(f"Token: {token[:20]}...")
    
    # 2. Verify
    with open('/data/harbor/common/config/registry/root.crt', 'rb') as f:
        cert_data = f.read()
        
    cert = load_pem_x509_certificate(cert_data, default_backend())
    public_key = cert.public_key()
    
    # We skip audience check here just to see if signature is valid
    # But usually audience must match 'harbor-registry'
    decoded = jwt.decode(token, public_key, algorithms=['RS256'], audience='harbor-registry')
    
    print("SUCCESS: Token is VALID.")
    print("Decoded Claims:", json.dumps(decoded, indent=2))
    
except Exception as e:
    print("FAILURE:")
    print(e)
    import traceback
    traceback.print_exc()
"""
        
        # Upload script
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/verify_v3.py", "w") as f:
            f.write(verify_script)
        sftp.close()
        
        print("Running verification script v3...")
        cmd = f"echo '{PASS}' | sudo -S python3 /tmp/verify_v3.py"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
