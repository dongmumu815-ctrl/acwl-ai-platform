
import paramiko
import asyncio
import base64

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
    # Update override file
    print("\n--- Updating docker-compose.override.yml ---")
    
    override_content = """version: '2.3'
services:
  portal:
    healthcheck:
      test: ["CMD-SHELL", "curl --fail -s http://127.0.0.1:8080 || exit 1"]
      interval: 10s
      timeout: 10s
      retries: 3
  registryctl:
    healthcheck:
      test: ["CMD-SHELL", "curl --fail -s http://127.0.0.1:8080/api/health || exit 1"]
      interval: 10s
      timeout: 10s
      retries: 3
"""
    b64_override = base64.b64encode(override_content.encode()).decode()
    cmd = f"python3 -c \"import base64; open('/data/harbor/docker-compose.override.yml', 'wb').write(base64.b64decode('{b64_override}'))\""
    await run_remote_command(cmd)
    
    # Restart
    print("\n--- Restarting portal and registryctl ---")
    await run_remote_command("sh -c 'cd /data/harbor && docker compose restart portal registryctl'")
    
    # Check
    print("\n--- Checking status ---")
    await asyncio.sleep(5)
    await run_remote_command("docker ps")

if __name__ == "__main__":
    asyncio.run(main())
