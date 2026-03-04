
import paramiko
import asyncio
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
    # Restart services with docker compose (confirmed available)
    print("\n--- Restarting Harbor Services (docker compose) ---")
    
    # Use docker compose (plugin)
    # Note: docker compose automatically picks up docker-compose.override.yml if present!
    # But let's be explicit to be safe.
    cmd = "sh -c 'cd /data/harbor && docker compose -f docker-compose.yml -f docker-compose.override.yml up -d'"
    
    await run_remote_command(cmd)
    
    # Wait for a bit
    print("\n--- Waiting for 20 seconds ---")
    await asyncio.sleep(20)
    
    # Check status
    print("\n--- Checking Container Status ---")
    await run_remote_command("docker ps")

if __name__ == "__main__":
    asyncio.run(main())
