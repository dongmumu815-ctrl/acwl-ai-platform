
import paramiko
import asyncio
import json
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
        
        if output:
            print("\n[STDOUT]:")
            print(output)
        if error:
            clean_error = '\n'.join([line for line in error.split('\n') if "[sudo] password" not in line])
            if clean_error.strip():
                print("\n[STDERR]:")
                print(clean_error)
        
        return output
            
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        client.close()

if __name__ == "__main__":
    # Get Admin Token
    print("\n--- Getting Admin Token ---")
    cmd = "docker exec registry curl -s -u 'admin:Harbor12345' 'http://core:8080/service/token?service=harbor-registry&scope=repository:library/hello-world:push,pull'"
    output = asyncio.run(run_remote_command(cmd))
    
    token = None
    if output:
        try:
            # Clean output
            json_str = output
            if "[STDOUT]:" in output: # This check is for MY local logs, but output variable contains raw stdout from remote
                # Wait, output variable is raw stdout.
                # But earlier I saw logs where output was printed.
                pass
            
            # The output from remote curl is just the JSON.
            # But sudo might add password prompt to stderr, which is handled.
            # However, previous runs showed [STDOUT]: then the JSON.
            # My run_remote_command returns raw output.
            
            # Try to find JSON start
            start = output.find('{')
            end = output.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = output[start:end]
                data = json.loads(json_str)
                token = data.get("token")
        except Exception as e:
            print(f"Error parsing token: {e}")
            
    if token:
        print(f"Got Token: {token[:20]}...")
        
        print(f"\n--- Testing with Admin Token ---")
        auth_header = f"Authorization: Bearer {token}"
        content_type = "application/vnd.docker.distribution.events.v1+json"
        
        # Test /service/notifications
        url = "http://core:8080/service/notifications"
        cmd = f"docker exec registry curl -X POST -v -s -H 'Content-Type: {content_type}' -H '{auth_header}' -d '{{\"events\": []}}' {url}"
        asyncio.run(run_remote_command(cmd))
    else:
        print("Could not get admin token")
