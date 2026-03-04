
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
    # 1. Try a few endpoints
    endpoints = [
        "/service/notifications/",
        "/api/v2.0/systeminfo",
        "/api/v2.0/statistics",
        "/api/v2.0/configurations",
        "/api/internal/configurations"
    ]
    
    # Secrets to try (for auth)
    # We found JOBSERVICE_SECRET=321ilUSKFowXa4ix and CORE_SECRET=8bwwVONJVT7s43Qb
    # Usually internal API uses JOBSERVICE_SECRET or CORE_SECRET.
    # But let's just use empty auth first to check 404 vs 401.
    
    for ep in endpoints:
        print(f"\n--- Trying {ep} ---")
        await run_remote_command(f"docker exec harbor-core curl -v -I http://127.0.0.1:8080{ep}")

    # 2. Check logs for the previous 404s
    print("\n--- Checking logs for 404 ---")
    await run_remote_command("docker logs harbor-core 2>&1 | tail -n 50")

if __name__ == "__main__":
    asyncio.run(main())
