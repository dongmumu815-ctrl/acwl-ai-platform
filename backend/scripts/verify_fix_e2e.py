
import paramiko
import asyncio
import json
import base64

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

async def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASS)
        
        # 0. Get Token
        print("Getting Token...")
        # Note: Using docker exec registry to curl core, because localhost on registry container resolves to registry loopback,
        # but core is another container. 'core' hostname should work inside docker network.
        token_cmd = "curl -s -u 'admin:Harbor12345' 'http://core:8080/service/token?service=harbor-registry&scope=repository:prod/actable-server:pull,push'"
        
        stdin, stdout, stderr = client.exec_command(f"echo '{PASS}' | sudo -S docker exec registry {token_cmd}")
        token_resp = stdout.read().decode('utf-8')
        
        # Parse token
        if "{" in token_resp:
             token_resp = token_resp[token_resp.find("{"):token_resp.rfind("}")+1]
        
        try:
            token_data = json.loads(token_resp)
            token = token_data.get("token")
            if not token:
                print(f"No token in response: {token_resp}")
                return
            print(f"Got Token: {token[:20]}...")
        except Exception as e:
            print(f"Failed to parse token: {token_resp} Error: {e}")
            return

        # 1. Get manifest
        # We fetch manifest from localhost:5000 (Host mapped port) using the token
        print("Fetching manifest for 0.81...")
        accept_header = "Accept: application/vnd.docker.distribution.manifest.v2+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.oci.image.index.v1+json"
        cmd_get = f"curl -i -s -H 'Authorization: Bearer {token}' -H '{accept_header}' 'http://localhost:5000/v2/prod/actable-server/manifests/0.81'"
        
        stdin, stdout, stderr = client.exec_command(f"echo '{PASS}' | sudo -S {cmd_get}")
        resp_str = stdout.read().decode('utf-8')
        
        if "[sudo] password" in resp_str:
            resp_str = resp_str.replace("[sudo] password for ubuntu: ", "").strip()

        # Parse headers and body
        headers, body = resp_str.split("\r\n\r\n", 1)
        content_type = "application/vnd.docker.distribution.manifest.v2+json" # default
        for line in headers.split("\r\n"):
            if line.lower().startswith("content-type:"):
                content_type = line.split(":", 1)[1].strip()
                break
        
        print(f"Got manifest (Content-Type: {content_type})")
        manifest_str = body

        # 2. Save manifest to /tmp/manifest.json on REMOTE HOST
        b64_manifest = base64.b64encode(manifest_str.encode()).decode()
        cmd_save = f"python3 -c \"import base64; open('/tmp/manifest.json', 'wb').write(base64.b64decode('{b64_manifest}'))\""
        stdin, stdout, stderr = client.exec_command(f"echo '{PASS}' | sudo -S {cmd_save}")
        stdout.read() # Wait for completion
        
        # 3. PUT manifest as new tag 'test-verify'
        print("Putting manifest as test-verify...")
        cmd_put = f"curl -v -X PUT -H 'Authorization: Bearer {token}' -H 'Content-Type: {content_type}' --data-binary @/tmp/manifest.json 'http://localhost:5000/v2/prod/actable-server/manifests/test-verify'"
        
        stdin, stdout, stderr = client.exec_command(f"echo '{PASS}' | sudo -S {cmd_put}")
        out_put = stdout.read().decode('utf-8')
        err_put = stderr.read().decode('utf-8')
        
        print("[PUT STDOUT]:", out_put)
        print("[PUT STDERR]:", err_put)
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
