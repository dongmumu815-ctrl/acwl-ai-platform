
import paramiko
import asyncio
import json
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

async def run_remote_command(command):
    print(f"Executing: {command}")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASS)
        full_cmd = f"echo '{PASS}' | sudo -S {command}"
        stdin, stdout, stderr = client.exec_command(full_cmd)
        
        out = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        
        if out: print(f"[STDOUT]:\n{out}")
        if err: 
            clean_err = '\n'.join([line for line in err.split('\n') if "[sudo] password" not in line])
            if clean_err.strip(): print(f"[STDERR]:\n{clean_err}")
            
        return out
    finally:
        client.close()

async def main():
    # Construct a valid notification payload
    # Wait, the structure of event is:
    # { "events": [ { "id": "...", "timestamp": "...", "action": "push", "target": { "mediaType": "...", "size": 1234, "digest": "sha256:fake", "length": 1234, "repository": "prod/actable-server", "url": "http://registry:5000/v2/prod/actable-server/manifests/0.87", "tag": "0.87" }, "request": { ... }, "actor": { ... }, "source": { ... } } ] }
    # But I need to be careful with python string formatting.
    
    # Let's use a simpler payload first.
    payload_str = '{"events":[{"id":"asdf","timestamp":"2026-03-02T10:00:00.000Z","action":"push","target":{"mediaType":"application/vnd.docker.distribution.manifest.v2+json","size":1234,"digest":"sha256:fake","length":1234,"repository":"prod/actable-server","url":"http://registry:5000/v2/prod/actable-server/manifests/0.87","tag":"0.87"},"request":{"id":"req-1234","addr":"127.0.0.1","host":"registry","method":"PUT","useragent":"docker/19.03"},"actor":{"name":"admin"},"source":{"addr":"registry:5000","instanceID":"instance-1"}}]}'
    
    # We need to escape double quotes for bash
    payload_bash = payload_str.replace('"', '\\"')
    
    test_cmd = f"""
    SECRET=$(docker exec harbor-core env | grep JOBSERVICE_SECRET | cut -d= -f2 | tr -d '\\r')
    echo "Using Secret: '$SECRET'"
    
    # Test 1: Standard endpoint
    echo "--- Test 1: /service/notifications ---"
    docker exec registry curl -v -H "Authorization: Harbor-Secret $SECRET" \\
        -H "Content-Type: application/json" \\
        -d "{payload_bash}" \\
        http://core:8080/service/notifications
        
    # Test 2: V2 endpoint (if exists)
    echo "\\n--- Test 2: /api/v2.0/notifications ---"
    docker exec registry curl -v -H "Authorization: Harbor-Secret $SECRET" \\
        -H "Content-Type: application/json" \\
        -d "{payload_bash}" \\
        http://core:8080/api/v2.0/notifications
        
    # Test 3: Registry endpoint?
    echo "\\n--- Test 3: /service/registry/notifications ---"
    docker exec registry curl -v -H "Authorization: Harbor-Secret $SECRET" \\
        -H "Content-Type: application/json" \\
        -d "{payload_bash}" \\
        http://core:8080/service/registry/notifications
    """
    
    print("\n--- Simulating Notification ---")
    await run_remote_command(test_cmd)

if __name__ == "__main__":
    asyncio.run(main())
