
import paramiko
import asyncio
import base64

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
    # 1. Download online installer
    print("\n--- Downloading Harbor v2.12.1 Online Installer ---")
    url = "https://github.com/goharbor/harbor/releases/download/v2.12.1/harbor-online-installer-v2.12.1.tgz"
    cmd = f"curl -L -o /tmp/harbor-online-installer-v2.12.1.tgz {url}"
    await run_remote_command(cmd)
    
    # 2. Extract to /tmp/harbor first (user space)
    print("\n--- Extracting Installer to /tmp ---")
    cmd = "rm -rf /tmp/harbor && tar xzvf /tmp/harbor-online-installer-v2.12.1.tgz -C /tmp"
    await run_remote_command(cmd)
    
    # 3. Move to /data/harbor/installer_tmp
    # Use sudo cp -r ...
    # And make sure target dir is writable or created by root.
    # run_remote_command uses sudo for the whole command string.
    # But maybe wildcard expansion `*` happens before sudo in local shell?
    # Yes! `sudo cp /tmp/harbor/* ...` expands * as user, which is fine if user can read /tmp/harbor.
    # But `cp` failed with Permission denied.
    # This means destination is not writable?
    # /data/harbor/installer_tmp was created by root (sudo mkdir).
    # So `sudo cp` should work.
    
    # Wait, did I use sudo in the command string?
    # run_remote_command: full_cmd = f"echo '{PASS}' | sudo -S {command}"
    # So command runs as root.
    # Why permission denied?
    # Maybe /tmp/harbor files are owned by user, but root can read them.
    # Maybe AppArmor/SELinux?
    
    # Let's try explicitly listing files or copying directory itself.
    print("\n--- Moving to /data/harbor/installer_tmp ---")
    cmd = "rm -rf /data/harbor/installer_tmp && cp -r /tmp/harbor /data/harbor/installer_tmp"
    await run_remote_command(cmd)
    
    # 4. Check contents (verbose)
    print("\n--- Checking extracted files (verbose) ---")
    await run_remote_command("ls -la /data/harbor/installer_tmp")
    
    # 5. Move files to /data/harbor (prepare, install.sh, common.sh, harbor.yml.tmpl)
    # But backup old harbor.yml first
    print("\n--- Backing up harbor.yml ---")
    await run_remote_command("cp /data/harbor/harbor.yml /data/harbor/harbor.yml.bak.2.10.0")
    
    # Copy scripts
    print("\n--- Copying scripts to /data/harbor ---")
    cmd = "cp /data/harbor/installer_tmp/prepare /data/harbor/"
    await run_remote_command(cmd)
    cmd = "cp /data/harbor/installer_tmp/install.sh /data/harbor/"
    await run_remote_command(cmd)
    cmd = "cp /data/harbor/installer_tmp/common.sh /data/harbor/"
    await run_remote_command(cmd)
    
    # Create new harbor.yml from tmpl
    print("\n--- Creating new harbor.yml ---")
    cmd = "cp /data/harbor/installer_tmp/harbor.yml.tmpl /data/harbor/harbor.yml"
    await run_remote_command(cmd)

if __name__ == "__main__":
    asyncio.run(main())
