
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
    # Create docker-compose.override.yml content
    # Note: Use version '2.3' because 'healthcheck' is supported since v2.1.
    # Also, we use CMD-SHELL because docker-compose v2+ syntax prefers it.
    override_content = """version: '2.3'
services:
  portal:
    healthcheck:
      test: ["CMD-SHELL", "curl --fail -s http://localhost:80 || exit 1"]
      interval: 10s
      timeout: 10s
      retries: 3
  registryctl:
    healthcheck:
      test: ["CMD-SHELL", "curl --fail -s -g http://[::]:37777/api/health || exit 1"]
      interval: 10s
      timeout: 10s
      retries: 3
"""
    # Write to file
    print("\n--- Creating docker-compose.override.yml ---")
    
    # We write line by line to avoid shell complexity with cat <<EOF in python string
    # Or just use echo -e
    # But newlines in python string are real newlines.
    
    # Better: Use python to write to /tmp then sudo mv
    print("\n--- Writing to /tmp/docker-compose.override.yml ---")
    
    import base64
    b64_content = base64.b64encode(override_content.encode()).decode()
    
    # Write to /tmp (usually writable by user)
    # But wait, run_remote_command runs with sudo -S. So it runs as root?
    # No, sudo -S runs the command as root.
    # If I run `python3 -c ...` as root, it writes as root.
    # So I can write directly to /data/harbor/docker-compose.override.yml?
    # Yes! Why did `echo ... >> file` fail?
    # Because redirection `>>` happens by the shell BEFORE sudo.
    # But `python3 -c ...` runs entirely under sudo.
    
    cmd_write = f"python3 -c \"import base64; open('/data/harbor/docker-compose.override.yml', 'wb').write(base64.b64decode('{b64_content}'))\""
    await run_remote_command(cmd_write)
    
    # Verify file
    print("\n--- Verifying File ---")
    await run_remote_command("cat /data/harbor/docker-compose.override.yml")

if __name__ == "__main__":
    asyncio.run(main())
