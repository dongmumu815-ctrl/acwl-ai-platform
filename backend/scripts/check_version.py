
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
    # Check harbor-core env
    print("\n--- Checking harbor-core env ---")
    await run_remote_command("docker exec harbor-core env")
    
    # Check where prepare script is
    print("\n--- Searching for prepare script ---")
    await run_remote_command("find / -name prepare -type f 2>/dev/null | grep harbor")
    
    # Check if there is an install.sh
    print("\n--- Searching for install.sh ---")
    await run_remote_command("find / -name install.sh -type f 2>/dev/null | grep harbor")

if __name__ == "__main__":
    asyncio.run(main())
