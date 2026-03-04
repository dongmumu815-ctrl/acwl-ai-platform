
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
    # 1. Fix jobservice config.yml
    print("\n--- Fixing jobservice/config.yml ---")
    
    # We'll use python on remote to parse and modify yaml safely
    fix_jobservice_script = """
import yaml

config_path = '/data/harbor/common/config/jobservice/config.yml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Check if job_loggers is empty or None
if not config.get('job_loggers'):
    config['job_loggers'] = [
        {
            'name': 'STD_OUTPUT',
            'level': 'INFO'
        }
    ]

with open(config_path, 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
"""
    b64_script = base64.b64encode(fix_jobservice_script.encode()).decode()
    cmd = f"python3 -c \"import base64; exec(base64.b64decode('{b64_script}'))\""
    await run_remote_command(cmd)
    
    # Verify
    await run_remote_command("grep -A 5 job_loggers /data/harbor/common/config/jobservice/config.yml")
    
    # 2. Fix docker-compose.override.yml
    print("\n--- Fixing docker-compose.override.yml ---")
    
    # We update portal health check to use 8080
    override_content = """version: '2.3'
services:
  portal:
    healthcheck:
      test: ["CMD-SHELL", "curl --fail -s http://localhost:8080 || exit 1"]
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
    b64_override = base64.b64encode(override_content.encode()).decode()
    cmd = f"python3 -c \"import base64; open('/data/harbor/docker-compose.override.yml', 'wb').write(base64.b64decode('{b64_override}'))\""
    await run_remote_command(cmd)
    
    # 3. Restart services
    print("\n--- Restarting services ---")
    await run_remote_command("sh -c 'cd /data/harbor && docker compose restart jobservice portal registryctl'")
    
    # 4. Check status
    print("\n--- Checking status ---")
    await asyncio.sleep(10)
    await run_remote_command("docker ps")

if __name__ == "__main__":
    asyncio.run(main())
