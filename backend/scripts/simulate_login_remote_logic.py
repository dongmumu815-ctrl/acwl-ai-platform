import requests
import re
import sys

BASE_URL = "http://10.20.1.204:5000"
USER = "admin"
PASS = "Harbor12345"

def main():
    print(f"=== 1. Probing {BASE_URL}/v2/ ===")
    try:
        r = requests.get(f"{BASE_URL}/v2/")
        print(f"Status: {r.status_code}")
        print(f"Headers: {r.headers}")
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    if r.status_code != 401:
        print("Expected 401, got", r.status_code)
        # If 200, it means no auth required?
        if r.status_code == 200:
            print("Registry is open? Success?")
            sys.exit(0)
        sys.exit(1)

    auth_header = r.headers.get('Www-Authenticate', '')
    print(f"Www-Authenticate: {auth_header}")

    # Parse realm and service
    # Bearer realm="http://10.20.1.204:5000/service/token",service="harbor-registry"
    realm_match = re.search(r'realm="([^"]+)"', auth_header)
    service_match = re.search(r'service="([^"]+)"', auth_header)

    if not realm_match:
        print("Could not find realm in header")
        sys.exit(1)

    realm = realm_match.group(1)
    service = service_match.group(1) if service_match else None
    
    print(f"Realm: {realm}")
    print(f"Service: {service}")

    # 2. Get Token
    print(f"\n=== 2. Getting Token from {realm} ===")
    params = {
        'client_id': 'simulate_script',
        'offline_token': 'true',
        'service': service
    }
    
    try:
        r = requests.get(realm, params=params, auth=(USER, PASS))
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Failed to get token: {e}")
        sys.exit(1)

    if r.status_code != 200:
        print("Failed to authenticate with Core.")
        sys.exit(1)

    token_data = r.json()
    token = token_data.get('token')
    if not token:
        print("No token in response")
        sys.exit(1)
    
    print(f"Got Token (len={len(token)})")

    # 3. Use Token
    print(f"\n=== 3. Using Token to access {BASE_URL}/v2/ ===")
    headers = {
        'Authorization': f"Bearer {token}"
    }
    try:
        r = requests.get(f"{BASE_URL}/v2/", headers=headers)
        print(f"Status: {r.status_code}")
        print(f"Headers: {r.headers}")
    except Exception as e:
        print(f"Failed to use token: {e}")
        sys.exit(1)

    if r.status_code == 200:
        print("\nSUCCESS: Docker Login Flow Simulated Successfully!")
    else:
        print(f"\nFAILURE: Registry rejected token with status {r.status_code}")

if __name__ == "__main__":
    main()
