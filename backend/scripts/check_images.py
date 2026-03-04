
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
            # Filter sudo prompt
            clean_err = '\n'.join([line for line in err.split('\n') if "[sudo] password" not in line])
            if clean_err.strip(): print(f"[STDERR]:\n{clean_err}")
            
        return out
    finally:
        client.close()

async def main():
    # Remove 0.86 tag
    print("\n--- Removing 0.86 tag ---")
    await run_remote_command("ls -R /data/harbor/registry/docker/registry/v2/repositories/prod/actable-server/_manifests/tags")
    # await run_remote_command("rm -rf /data/harbor/registry/docker/registry/v2/repositories/prod/actable-server/_manifests/tags/0.86")

if __name__ == "__main__":
    asyncio.run(main())
