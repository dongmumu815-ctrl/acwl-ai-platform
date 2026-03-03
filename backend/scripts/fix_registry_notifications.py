
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
    # 1. Get Secret
    print("\n--- Getting Secret ---")
    cmd = "grep JOBSERVICE_SECRET /data/harbor/common/config/core/env"
    secret_line = await run_remote_command(cmd)
    
    # Extract secret value (assuming JOBSERVICE_SECRET=xxx)
    secret = secret_line.strip().split('=')[1] if secret_line and '=' in secret_line else ""
    print(f"Secret found: {secret[:5]}...")
    
    if not secret:
        print("Failed to find JOBSERVICE_SECRET")
        return

    # 2. Append notifications section to registry/config.yml
    print("\n--- Updating Registry Config ---")
    
    # We need to construct the yaml content to append
    # Note: indentation is important.
    notifications_section = f"""
notifications:
  endpoints:
  - name: harbor
    disabled: false
    url: http://core:8080/service/notifications
    headers:
      Authorization: [Harbor-Secret {secret}]
    timeout: 3000ms
    threshold: 5
    backoff: 1s
"""
    
    # We'll use python on remote to append safely
    append_script = f"""
with open('/data/harbor/common/config/registry/config.yml', 'a') as f:
    f.write('''{notifications_section}''')
"""
    b64_script = base64.b64encode(append_script.encode()).decode()
    cmd = f"python3 -c \"import base64; exec(base64.b64decode('{b64_script}'))\""
    await run_remote_command(cmd)
    
    # Verify content
    print("\n--- Verifying Registry Config ---")
    await run_remote_command("tail -n 15 /data/harbor/common/config/registry/config.yml")
    
    # 3. Restart Registry
    print("\n--- Restarting Registry ---")
    await run_remote_command("docker restart registry")
    
    # 4. Wait a bit
    await asyncio.sleep(5)
    await run_remote_command("docker ps")

if __name__ == "__main__":
    asyncio.run(main())
