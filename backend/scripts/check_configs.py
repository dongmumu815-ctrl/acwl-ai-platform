
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
    # 1. Read app.conf
    print("\n--- Reading app.conf ---")
    await run_remote_command("cat /data/harbor/common/config/core/app.conf")
    
    # 2. Read core/env
    print("\n--- Reading core/env ---")
    await run_remote_command("cat /data/harbor/common/config/core/env")
    
    # 3. Check registry env
    print("\n--- Checking Registry Env ---")
    await run_remote_command("docker exec registry env")

if __name__ == "__main__":
    asyncio.run(main())
