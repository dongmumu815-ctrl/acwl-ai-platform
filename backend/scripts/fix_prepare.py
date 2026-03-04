
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
    # Check directory content
    print("\n--- Checking /data/harbor content ---")
    await run_remote_command("ls -la /data/harbor")
    
    # Check if prepare exists and is executable
    print("\n--- Checking prepare script ---")
    await run_remote_command("ls -l /data/harbor/prepare")
    
    # Make executable
    print("\n--- Making prepare executable ---")
    await run_remote_command("chmod +x /data/harbor/prepare /data/harbor/install.sh /data/harbor/common.sh")
    
    # Run prepare again
    print("\n--- Running prepare ---")
    # Using full path to avoid issues with ./
    await run_remote_command("cd /data/harbor && /data/harbor/prepare --with-trivy")
    
    # Check docker-compose.yml timestamp again
    print("\n--- Checking docker-compose.yml timestamp ---")
    await run_remote_command("ls -l --time-style=full-iso /data/harbor/docker-compose.yml")
    
    # If successful, restart
    print("\n--- Restarting Harbor ---")
    await run_remote_command("cd /data/harbor && docker compose down")
    await run_remote_command("cd /data/harbor && docker compose up -d --force-recreate")
    
    # Wait and check
    await asyncio.sleep(15)
    await run_remote_command("docker ps")

if __name__ == "__main__":
    asyncio.run(main())
