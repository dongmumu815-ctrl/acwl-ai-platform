
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
    # Configure harbor.yml
    print("\n--- Configuring harbor.yml ---")
    
    # Set hostname
    cmd = "sed -i 's/hostname: reg.mydomain.com/hostname: 10.20.1.204/' /data/harbor/harbor.yml"
    await run_remote_command(cmd)
    
    # Set http port to 5000 (was 80 by default in tmpl)
    cmd = "sed -i 's/port: 80/port: 5000/' /data/harbor/harbor.yml"
    await run_remote_command(cmd)
    
    # Comment out https section (since user didn't seem to use it or it was not configured in old harbor.yml snippet I saw)
    # Wait, old harbor.yml snippet didn't show https section. It was likely commented out or removed.
    # The default tmpl has https enabled. We must disable it or configure it.
    # User's old config:
    # http:
    #   port: 5000
    # No https block visible in `cat /data/harbor/harbor.yml` output earlier.
    
    # So we comment out https block.
    # It's multi-line.
    # Easier to just remove lines?
    # Or use a script to rewrite config.
    
    # Let's use a python script ON THE REMOTE to update yaml safely.
    # This is better than sed for yaml.
    
    update_script = """
import yaml

config_path = '/data/harbor/harbor.yml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

config['hostname'] = '10.20.1.204'
config['http']['port'] = 5000
if 'https' in config:
    del config['https'] # Remove https section

config['harbor_admin_password'] = 'Harbor12345'
config['database']['password'] = 'root'
config['data_volume'] = '/data/harbor'

# Ensure trivy is enabled? 
# The installer script handles 'with-trivy'.
# But config might need trivy section? 
# harbor.yml.tmpl usually has trivy section.

with open(config_path, 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
"""
    
    import base64
    b64_script = base64.b64encode(update_script.encode()).decode()
    
    print("\n--- Running python config updater ---")
    # We need pyyaml installed. Standard python3 might not have it.
    # Check if pyyaml is installed.
    # If not, fall back to sed.
    
    check_cmd = "python3 -c 'import yaml; print(\"ok\")'"
    out = await run_remote_command(check_cmd)
    
    if "ok" in str(out):
        cmd = f"python3 -c \"import base64; exec(base64.b64decode('{b64_script}'))\""
        await run_remote_command(cmd)
    else:
        print("PyYAML not found, falling back to sed")
        # Sed fallback
        await run_remote_command("sed -i 's/hostname: reg.mydomain.com/hostname: 10.20.1.204/' /data/harbor/harbor.yml")
        await run_remote_command("sed -i 's/port: 80/port: 5000/' /data/harbor/harbor.yml")
        await run_remote_command("sed -i 's/Harbor12345/Harbor12345/' /data/harbor/harbor.yml") # It is default
        # Disable https by commenting out lines starting with https: and following indented lines?
        # Too risky.
        # Just rename https to https_disabled
        await run_remote_command("sed -i 's/^https:/https_disabled:/' /data/harbor/harbor.yml")
        
    # grep didn't return anything?
    # Maybe _version is not in the file?
    # Let's run prepare and see what happens.
    
    # Commands failed because of `cd` inside sudo.
    # Use sh -c for all compound commands.
    
    # 1. Stop existing Harbor
    print("\n--- Stopping Harbor ---")
    await run_remote_command("sh -c 'cd /data/harbor && docker-compose down'")
    
    # 2. Run prepare
    print("\n--- Running prepare ---")
    await run_remote_command("sh -c 'cd /data/harbor && ./prepare --with-trivy'")
    
    # 3. Start Harbor
    print("\n--- Starting Harbor ---")
    await run_remote_command("sh -c 'cd /data/harbor && docker-compose up -d'")
    
    # The `prepare` script is not updating docker-compose.yml!
    # Timestamp is 04:25:53, which is old (assuming current time is later).
    # Wait, 04:25:53 might be the time when I copied it?
    # No, I copied it just now.
    # But `prepare` should touch it.
    
    # Maybe `prepare` failed?
    # `run_remote_command` output was empty.
    # Let's try running prepare and capturing output to a file, then reading it.
    print("\n--- Running prepare with log capture ---")
    await run_remote_command("sh -c 'cd /data/harbor && ./prepare --with-trivy > /tmp/prepare.log 2>&1'")
    await run_remote_command("cat /tmp/prepare.log")
    
    # Also, why `docker-compose down` didn't remove containers?
    # Maybe because I'm running as `ubuntu` with `sudo` inside ssh?
    # `run_remote_command` does `echo PASS | sudo -S command`.
    # `sh -c 'cd ... && docker-compose down'`
    # Maybe `docker-compose` is not in path for sudo?
    # I checked `which docker-compose` earlier and it returned nothing?
    # Wait, `check_compose.py` output:
    # Executing: which docker-compose
    # (Empty output)
    # Executing: docker compose version
    # Docker Compose version v5.0.2
    
    # Ah! `docker-compose` (standalone) is NOT installed. `docker compose` (plugin) IS installed.
    # But I'm calling `docker-compose` in my commands!
    # `install.sh` and `prepare` usually use `docker-compose` if available, or `docker compose`.
    # But *I* am calling `docker-compose down` manually.
    # And `prepare` script might be generating `docker-compose.yml` but not being able to use it if it relies on `docker-compose` binary availability?
    # Actually `prepare` generates the file. It doesn't run docker-compose.
    # `install.sh` runs docker-compose.
    
    # So:
    # 1. My manual `docker-compose down` failed (silently? or `command not found` but ignored?).
    # 2. `prepare` ran but maybe didn't update file?
    
    # Let's fix my commands to use `docker compose`.
    print("\n--- Fixing commands to use 'docker compose' ---")
    
    # Stop
    await run_remote_command("sh -c 'cd /data/harbor && docker compose down'")
    
    # Run prepare again
    await run_remote_command("sh -c 'cd /data/harbor && ./prepare --with-trivy > /tmp/prepare.log 2>&1'")
    await run_remote_command("cat /tmp/prepare.log")
    
    # Start
    await run_remote_command("sh -c 'cd /data/harbor && docker compose up -d --force-recreate'")
    
    # Check
    await asyncio.sleep(15)
    await run_remote_command("docker ps")

if __name__ == "__main__":
    asyncio.run(main())
