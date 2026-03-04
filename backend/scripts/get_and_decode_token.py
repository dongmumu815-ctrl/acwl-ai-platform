
import paramiko
import asyncio
import jwt
import sys

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

async def run_remote_command(command):
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS)
        
        full_cmd = f"echo '{PASS}' | sudo -S {command}"
        print(f"Executing: {full_cmd}")
        stdin, stdout, stderr = client.exec_command(full_cmd)
        
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        return output
            
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        client.close()

if __name__ == "__main__":
    # Request a token from Core
    # We need to use basic auth with admin credentials
    # ADMIN_PASSWORD=Harbor12345 (from env)
    
    # We need to base64 encode admin:Harbor12345
    # admin:Harbor12345 -> YWRtaW46SGFyYm9yMTIzNDU=
    
    cmd = "docker exec registry curl -s -u 'admin:Harbor12345' 'http://core:8080/service/token?service=harbor-registry&scope=repository:library/hello-world:pull'"
    output = asyncio.run(run_remote_command(cmd))
    
    if output:
        print("\nToken Response:")
        print(output)
        
        try:
            import json
            data = json.loads(output)
            token = data.get("token")
            if token:
                print("\nDecoded Token Headers:")
                print(jwt.get_unverified_header(token))
                print("\nDecoded Token Payload:")
                print(jwt.decode(token, options={"verify_signature": False}))
        except Exception as e:
            print(f"Failed to decode token: {e}")
