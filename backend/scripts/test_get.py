
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
    endpoints = [
        "/service/notifications",
        "/service/registry/notifications",
        "/api/v2.0/notifications"
    ]
    
    # Try GET method
    for ep in endpoints:
        print(f"\n--- GET {ep} ---")
        await run_remote_command(f"docker exec harbor-core curl -v http://127.0.0.1:8080{ep}")

    # Also try to grep for the route in the binary (last resort)
    # print("\n--- Grep strings in harbor-core binary ---")
    # await run_remote_command("docker exec harbor-core strings /harbor/harbor_core | grep notification | head -n 20")

if __name__ == "__main__":
    asyncio.run(main())
