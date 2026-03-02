
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
    # Check registryctl ports
    print("\n--- Registryctl Ports ---")
    await run_remote_command("docker exec registryctl netstat -tuln")
    
    # Update override file with robust checks (127.0.0.1)
    print("\n--- Updating Override ---")
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
    # Wait, earlier netstat on registryctl showed NO port 8080. It showed [::]:37777.
    # But in fresh install, maybe it uses 8080?
    # Let's check netstat output first before deciding.
    
    # But I will write the python script to update IF needed.
    # Actually, I'll update it based on netstat output in the same script?
    # No, let's just run netstat first.

if __name__ == "__main__":
    asyncio.run(main())
