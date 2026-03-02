
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
    # Fix registry config
    print("\n--- Fixing registry config ---")
    # Replace [Harbor-Secret ...] with Harbor-Secret ... (remove brackets)
    # Use explicit sed
    # Pattern: Authorization: [Harbor-Secret ...]
    # To: Authorization: Harbor-Secret ...
    
    # sed -i 's/Authorization: \[\(.*\)]/Authorization: \1/' /data/harbor/common/config/registry/config.yml
    cmd = "sed -i 's/Authorization: \[\(.*\)]/Authorization: \1/' /data/harbor/common/config/registry/config.yml"
    await run_remote_command(cmd)
    
    # Restart registry
    print("\n--- Restarting registry ---")
    await run_remote_command("docker restart registry")
    
    # Wait for registry to be ready
    print("\n--- Waiting for registry ---")
    await asyncio.sleep(10)
    
    # Verify config again
    print("\n--- Verifying config ---")
    await run_remote_command("grep Authorization /data/harbor/common/config/registry/config.yml")
    
    # Push 0.87
    print("\n--- Pushing 0.87 ---")
    # We assume 0.86 is still present in local docker cache (from previous push)
    # Check images first
    # await run_remote_command("docker images")
    
    # Tag and Push
    # We use localhost:5000 directly
    await run_remote_command("docker tag localhost:5000/prod/actable-server:0.86 localhost:5000/prod/actable-server:0.87")
    await run_remote_command("docker push localhost:5000/prod/actable-server:0.87")
    
    # Check API
    print("\n--- Checking API for 0.87 ---")
    cmd_api = "curl -u 'admin:Harbor12345' -H 'Content-Type: application/json' 'http://localhost:5000/api/v2.0/projects/prod/repositories/actable-server/artifacts?page=1&page_size=10'"
    await run_remote_command(cmd_api)

if __name__ == "__main__":
    asyncio.run(main())
