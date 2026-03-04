
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
    digest = "98c665f9194f4bb29bc42118293c9a53d89ae9830c01cf79b43a58e4169f85c5"
    short_digest = digest[:2]
    
    # 1. Read manifest content
    print("\n--- Reading Manifest ---")
    blob_path = f"/data/harbor/registry/docker/registry/v2/blobs/sha256/{short_digest}/{digest}/data"
    manifest_content = await run_remote_command(f"cat {blob_path}")
    
    try:
        manifest = json.loads(manifest_content)
        print(f"MediaType: {manifest.get('mediaType')}")
        print(f"Config Digest: {manifest.get('config', {}).get('digest')}")
        print(f"Layers: {len(manifest.get('layers', []))}")
        
        # Calculate size (rough)
        # Actually size in DB is the size of the manifest blob itself? Or the image size?
        # Usually artifact.size is the manifest size.
        print(f"Manifest Size: {len(manifest_content)}")
        
    except:
        print("Failed to parse manifest JSON")

    # 2. Inspect DB Schema
    print("\n--- Inspecting DB Schema ---")
    # Psql command
    psql_cmd = "docker exec harbor-db psql -U postgres -d registry -c '\\d artifact'"
    await run_remote_command(psql_cmd)
    
    psql_cmd = "docker exec harbor-db psql -U postgres -d registry -c '\\d tag'"
    await run_remote_command(psql_cmd)
    
    # 3. Check existing artifact to copy values
    print("\n--- Checking existing artifact ---")
    psql_cmd = "docker exec harbor-db psql -U postgres -d registry -c 'SELECT * FROM artifact LIMIT 1'"
    await run_remote_command(psql_cmd)

if __name__ == "__main__":
    asyncio.run(main())
