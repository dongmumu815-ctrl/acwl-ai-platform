
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
    # Check portal ports and curl
    print("\n--- Portal Ports & Curl ---")
    await run_remote_command("docker exec harbor-portal netstat -tuln")
    await run_remote_command("docker exec harbor-portal which curl")
    await run_remote_command("docker exec harbor-portal curl -v http://127.0.0.1:8080 || echo 'Curl failed'")
    await run_remote_command("docker exec harbor-portal curl -v http://localhost:8080 || echo 'Curl failed'")

    # Check registryctl ports and curl
    print("\n--- Registryctl Ports & Curl ---")
    await run_remote_command("docker exec registryctl netstat -tuln")
    await run_remote_command("docker exec registryctl which curl")
    # Usually registryctl API is on 8080 or 80 or 37777?
    # Official docker-compose.yml often uses:
    # healthcheck:
    #   test: ["CMD-SHELL", "curl --fail -s http://127.0.0.1:8080/api/health || curl -k --fail -s https://127.0.0.1:8443/api/health || exit 1"]
    # Let's try to find where it listens.
    await run_remote_command("docker exec registryctl ps aux") # See command args
    
    # Check current healthcheck config
    print("\n--- Current Healthcheck Config ---")
    await run_remote_command("docker inspect --format='{{json .Config.Healthcheck}}' harbor-portal")
    await run_remote_command("docker inspect --format='{{json .Config.Healthcheck}}' registryctl")

if __name__ == "__main__":
    asyncio.run(main())
