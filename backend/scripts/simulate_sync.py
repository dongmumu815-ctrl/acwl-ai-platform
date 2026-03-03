
import paramiko
import asyncio
import json

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
    # Tags to simulate
    tags = ["0.11", "0.87-fixed"]
    
    # Construct notification payloads
    payload_template = {
        "events": [
            {
                "id": "asdf-1234",
                "timestamp": "2026-03-02T10:00:00.000Z",
                "action": "push",
                "target": {
                    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                    "size": 1234,
                    "digest": "sha256:fake",
                    "length": 1234,
                    "repository": "prod/actable-server",
                    "url": "http://registry:5000/v2/prod/actable-server/manifests/TAG",
                    "tag": "TAG"
                },
                "request": {
                    "id": "req-1234",
                    "addr": "127.0.0.1",
                    "host": "registry",
                    "method": "PUT",
                    "useragent": "docker/19.03"
                },
                "actor": {
                    "name": "admin"
                },
                "source": {
                    "addr": "registry:5000",
                    "instanceID": "instance-1"
                }
            }
        ]
    }
    
    for tag in tags:
        print(f"\n--- Simulating Notification for tag: {tag} ---")
        
        # Modify payload
        current_payload = payload_template.copy()
        current_payload["events"][0]["target"]["tag"] = tag
        current_payload["events"][0]["target"]["url"] = current_payload["events"][0]["target"]["url"].replace("TAG", tag)
        
        payload_json = json.dumps(current_payload).replace('"', '\\"')
        
        # Get secret and send
        cmd = f"""
        SECRET=$(grep JOBSERVICE_SECRET /data/harbor/common/config/core/env | cut -d= -f2 | tr -d '\\r')
        echo "Using Secret: '$SECRET'"
        
        docker exec harbor-core curl -v -H "Authorization: Harbor-Secret $SECRET" \\
            -H "Content-Type: application/json" \\
            -d "{payload_json}" \\
            http://localhost:8080/service/notifications
        """
        await run_remote_command(cmd)

    # Verify API
    print("\n--- Verifying API ---")
    cmd_artifacts = """curl -s -u 'admin:Harbor12345' -H 'Content-Type: application/json' 'http://localhost:5000/api/v2.0/projects/prod/repositories/actable-server/artifacts?page=1&page_size=10&with_tag=true'"""
    await run_remote_command(cmd_artifacts)

if __name__ == "__main__":
    asyncio.run(main())
