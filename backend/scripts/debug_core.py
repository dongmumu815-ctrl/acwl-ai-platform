
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
    # 1. Check harbor-core process and ports
    print("\n--- harbor-core process and ports ---")
    await run_remote_command("docker exec harbor-core ps aux")
    await run_remote_command("docker exec harbor-core netstat -tuln")
    
    # 2. Check app.conf
    print("\n--- harbor-core app.conf ---")
    await run_remote_command("cat /data/harbor/common/config/core/app.conf")
    
    # 3. Check env variables (for secrets)
    print("\n--- harbor-core env ---")
    await run_remote_command("docker exec harbor-core env | grep SECRET")
    
    # 4. Try curling a known API like /api/v2.0/ping inside core
    print("\n--- Curl /api/v2.0/ping inside core ---")
    await run_remote_command("docker exec harbor-core curl -v http://127.0.0.1:8080/api/v2.0/ping")
    
    # 5. Check if core is running on HTTPS?
    # No, usually HTTP on 8080.
    
    # 6. Check if localhost resolves to something weird?
    await run_remote_command("docker exec harbor-core cat /etc/hosts")

if __name__ == "__main__":
    asyncio.run(main())
