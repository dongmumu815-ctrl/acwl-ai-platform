
import paramiko
import asyncio
import json

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
    # 1. Locate docker-compose.yml
    print("\n--- Locating docker-compose.yml ---")
    await run_remote_command("find / -name docker-compose.yml 2>/dev/null | grep harbor")
    
    # 3. Check logs of registry to see if it sent notification
    print("\n--- Checking Registry Logs for Notification ---")
    await run_remote_command("docker logs registry 2>&1 | tail -n 50")
    
    # 4. Check Core logs for notification error (more context)
    print("\n--- Checking Core Logs for Notification Processing ---")
    await run_remote_command("docker logs harbor-core 2>&1 | grep -C 5 'notification' | tail -n 50")
    
    # 5. Try manual sync via API?
    # No public API for triggering sync from registry to DB in standard Harbor.
    # But we can try to restart core?
    
    # Let's see if we can access the registry catalog directly via API
    print("\n--- Checking Registry Catalog directly ---")
    # Registry API is at /v2/_catalog
    cmd_reg = "curl -u 'admin:Harbor12345' http://localhost:5000/v2/_catalog"
    await run_remote_command(cmd_reg)
    
    print("\n--- Checking Tags for actable-server in Registry ---")
    cmd_tags = "curl -u 'admin:Harbor12345' http://localhost:5000/v2/prod/actable-server/tags/list"
    await run_remote_command(cmd_tags)

if __name__ == "__main__":
    asyncio.run(main())
