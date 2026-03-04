
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
    # 1. Check tarball existence
    print("\n--- Checking tarball ---")
    await run_remote_command("ls -l /tmp/harbor-online-installer-v2.12.1.tgz")
    
    # 2. Extract again to be sure (to /data/harbor/installer_files)
    print("\n--- Extracting to /data/harbor/installer_files ---")
    await run_remote_command("mkdir -p /data/harbor/installer_files")
    # Use tar directly to destination
    cmd = "tar xzvf /tmp/harbor-online-installer-v2.12.1.tgz -C /data/harbor/installer_files --strip-components=1"
    await run_remote_command(cmd)
    
    # 3. Verify extraction
    print("\n--- Verifying extraction ---")
    await run_remote_command("ls -l /data/harbor/installer_files")
    
    # 4. Copy scripts to /data/harbor
    print("\n--- Copying scripts ---")
    await run_remote_command("cp /data/harbor/installer_files/prepare /data/harbor/")
    await run_remote_command("cp /data/harbor/installer_files/install.sh /data/harbor/")
    await run_remote_command("cp /data/harbor/installer_files/common.sh /data/harbor/")
    
    # 5. Make executable
    print("\n--- Making executable ---")
    await run_remote_command("chmod +x /data/harbor/prepare /data/harbor/install.sh /data/harbor/common.sh")
    
    # 6. Run prepare (using sh -c for cd)
    print("\n--- Running prepare ---")
    await run_remote_command("sh -c 'cd /data/harbor && ./prepare --with-trivy'")
    
    # 7. Check docker-compose.yml timestamp
    print("\n--- Checking docker-compose.yml timestamp ---")
    await run_remote_command("ls -l --time-style=full-iso /data/harbor/docker-compose.yml")
    
    # 8. Restart Harbor (using docker compose)
    print("\n--- Restarting Harbor ---")
    await run_remote_command("sh -c 'cd /data/harbor && docker compose down'")
    await run_remote_command("sh -c 'cd /data/harbor && docker compose up -d --force-recreate'")
    
    # 9. Verify
    await asyncio.sleep(15)
    await run_remote_command("docker ps")

if __name__ == "__main__":
    asyncio.run(main())
