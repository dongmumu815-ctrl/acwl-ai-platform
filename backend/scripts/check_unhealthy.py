
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
    # 1. Inspect harbor-portal health check config
    print("\n--- Inspecting harbor-portal health check config ---")
    await run_remote_command("docker inspect --format='{{json .Config.Healthcheck}}' harbor-portal")
    
    # 2. Inspect registryctl health check config
    print("\n--- Inspecting registryctl health check config ---")
    await run_remote_command("docker inspect --format='{{json .Config.Healthcheck}}' registryctl")
    
    # 3. Check portal health check manually inside
    print("\n--- Checking portal health manual curl inside ---")
    await run_remote_command("docker exec harbor-portal curl -v http://localhost:8080")
    print("\n--- Checking portal health manual curl 80 inside ---")
    await run_remote_command("docker exec harbor-portal curl -v http://localhost:80")
    
    # 4. Check registryctl health check manual on ipv6
    print("\n--- Checking registryctl health manual curl inside (ipv6) ---")
    await run_remote_command("docker exec registryctl curl -v -g http://[::]:37777/api/health")
    
    # 5. Check portal ipv6
    print("\n--- Checking portal health manual curl inside (ipv6) ---")
    await run_remote_command("docker exec harbor-portal curl -v -g http://[::]:80")

if __name__ == "__main__":
    asyncio.run(main())
