
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
    # 1. Stop Harbor
    print("\n--- Stopping Harbor ---")
    await run_remote_command("sh -c 'cd /data/harbor && docker compose down'")
    
    # 2. Wipe Data (DB, Redis, Registry)
    # WARNING: This deletes everything!
    print("\n--- Wiping Data ---")
    await run_remote_command("rm -rf /data/harbor/database")
    await run_remote_command("rm -rf /data/harbor/redis")
    await run_remote_command("rm -rf /data/harbor/registry")
    await run_remote_command("rm -rf /data/harbor/job_logs")
    
    # 3. Re-run prepare (to ensure fresh config and secrets if needed, though config is static)
    # Just to be safe.
    print("\n--- Running prepare ---")
    await run_remote_command("sh -c 'cd /data/harbor && ./prepare --with-trivy'")
    
    # 4. Start Harbor
    print("\n--- Starting Harbor ---")
    await run_remote_command("sh -c 'cd /data/harbor && docker compose up -d'")
    
    # 5. Wait for startup
    print("\n--- Waiting for startup ---")
    await asyncio.sleep(20)
    await run_remote_command("docker ps")
    
    # 6. Check logs (just to be sure)
    print("\n--- Checking logs ---")
    await run_remote_command("docker logs harbor-core 2>&1 | tail -n 20")

if __name__ == "__main__":
    asyncio.run(main())
