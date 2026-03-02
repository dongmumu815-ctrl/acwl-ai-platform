import jwt
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import subprocess
import json
import sys
import requests

# Disable warnings
requests.packages.urllib3.disable_warnings()

try:
    print("Reading Root Cert...")
    with open('/data/harbor/common/config/registry/root.crt', 'rb') as f:
        cert_data = f.read()
    
    cert = load_pem_x509_certificate(cert_data, default_backend())
    public_key = cert.public_key()
    
    print("Fetching Token...")
    # Fetch token using requests
    url = "http://127.0.0.1:5000/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry"
    response = requests.get(url, auth=('admin', 'Harbor12345'))
    
    if response.status_code != 200:
        print(f"Failed to get token: {response.status_code}")
        print(response.text)
        sys.exit(1)
        
    token = response.json().get('token')
    if not token:
        print("No token in response")
        sys.exit(1)
        
    print(f"Got Token: {token[:20]}...")
    
    print("Verifying Signature...")
    # Verify
    decoded = jwt.decode(token, public_key, algorithms=['RS256'], audience='harbor-registry')
    print("SUCCESS: Token signature is VALID.")
    print("Decoded Claims:", decoded)

except jwt.ExpiredSignatureError:
    print("FAILURE: Token Expired")
except jwt.InvalidAudienceError:
    print("FAILURE: Invalid Audience")
except jwt.InvalidIssuerError:
    print("FAILURE: Invalid Issuer")
except jwt.InvalidSignatureError:
    print("FAILURE: Invalid Signature - The private key used to sign does NOT match the root.crt public key!")
except Exception as e:
    print(f"FAILURE: Verification Error: {e}")
    import traceback
    traceback.print_exc()
