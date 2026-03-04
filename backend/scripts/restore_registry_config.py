
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
    # Correct content without brackets and safe formatting
    config_content = """version: 0.1
log:
  level: debug
  fields:
    service: registry
storage:
  cache:
    layerinfo: redis
  filesystem:
    rootdirectory: /storage
  maintenance:
    uploadpurging:
      enabled: false
  delete:
    enabled: true
http:
  addr: :5000
  secret: Harbor12345
  debug:
    addr: localhost:5001
auth:
  token:
    realm: http://10.20.1.204:5000/service/token
    service: harbor-registry
    issuer: harbor-token-issuer
    rootcertbundle: /etc/registry/root.crt
redis:
  addr: redis:6379
  db: 1
  dial_timeout: 10ms
  read_timeout: 10ms
  write_timeout: 10ms
  pool:
    maxidle: 16
    maxactive: 64
    idletimeout: 300s
notifications:
  endpoints:
    - name: harbor
      url: http://core:8080/service/notifications
      headers:
        Authorization: [Harbor-Secret ttvSp4wGBUebD56ryYbbgw]
      timeout: 3000ms
      threshold: 5
      backoff: 1s
"""
    # Write to file using base64
    print("\n--- Restoring registry config.yml (with brackets) ---")
    b64_content = base64.b64encode(config_content.encode()).decode()
    cmd_write = f"python3 -c \"import base64; open('/data/harbor/common/config/registry/config.yml', 'wb').write(base64.b64decode('{b64_content}'))\""
    await run_remote_command(cmd_write)
    
    # Restart registry
    print("\n--- Restarting registry ---")
    await run_remote_command("docker restart registry")
    
    # Wait
    print("\n--- Waiting for registry ---")
    await asyncio.sleep(5)
    
    # Check logs
    print("\n--- Checking Registry Logs ---")
    await run_remote_command("docker logs registry 2>&1 | tail -n 20")

if __name__ == "__main__":
    asyncio.run(main())
