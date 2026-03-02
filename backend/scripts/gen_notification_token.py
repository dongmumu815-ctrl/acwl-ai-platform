import jwt
import time
from cryptography.hazmat.primitives import serialization

KEY_PATH = r"D:\works\codes\acwl-ai-data\backend\scripts\private_key.pem"
# I will use the key content directly from previous output instead of reading a file that doesn't exist locally

KEY_CONTENT = """-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----"""

def main():
    payload = {
        "iss": "harbor-token-issuer",
        "sub": "harbor-registry",
        "aud": "harbor-core",
        "exp": int(time.time()) + 315360000, # 10 years
        "nbf": int(time.time()) - 60,
        "iat": int(time.time()),
    }
    
    # Load private key
    private_key = serialization.load_pem_private_key(
        KEY_CONTENT.encode(),
        password=None
    )
    
    token = jwt.encode(payload, private_key, algorithm="RS256")
    print("TOKEN:")
    print(token)

if __name__ == "__main__":
    main()
