
import paramiko
import asyncio

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
    # 1. Login
    # We need to configure daemon for insecure registry first?
    # Or just use http:// if possible? Docker CLI defaults to https.
    # The error "server gave HTTP response to HTTPS client" means we need to add to insecure-registries.
    
    # Check if we can add to daemon.json
    print("\n--- Checking daemon.json ---")
    await run_remote_command("cat /etc/docker/daemon.json")
    
    # Add insecure registry if needed
    # Or use localhost:5000 if we are on the same machine?
    # 10.20.1.204 is the host IP.
    # We can try pushing to localhost:5000 from the host itself.
    
    print("\n--- Pushing to localhost:5000 ---")
    await run_remote_command("docker login localhost:5000 -u admin -p Harbor12345")
    
    # We need to pull from the registry first to get the image ID
    # But we can't pull if we can't connect.
    # Is there any image already?
    # The user said they pushed it, but it's not in FS.
    # Maybe they pushed 'latest'?
    
    # Let's check images again.
    # await run_remote_command("docker images")
    
    # If no image is present, we can't tag it.
    # We need to pull 'latest' from localhost:5000.
    
    await run_remote_command("docker pull localhost:5000/prod/actable-server:latest")
    
    await run_remote_command("docker tag localhost:5000/prod/actable-server:latest localhost:5000/prod/actable-server:0.86")
    
    await run_remote_command("docker push localhost:5000/prod/actable-server:0.86")
    
    # 4. Verify
    print("\n--- Verifying Push ---")
    await run_remote_command("ls -la /data/harbor/registry/docker/registry/v2/repositories/prod/actable-server/_manifests/tags/0.86")

if __name__ == "__main__":
    asyncio.run(main())
