
import paramiko
import asyncio

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

async def run_remote_command(command):
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS)
        
        full_cmd = f"echo '{PASS}' | sudo -S {command}"
        print(f"Executing: {full_cmd}")
        stdin, stdout, stderr = client.exec_command(full_cmd)
        
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if output:
            print("\n[STDOUT]:")
            print(output)
        if error:
            # Filter out sudo prompt
            clean_error = '\n'.join([line for line in error.split('\n') if "[sudo] password" not in line])
            if clean_error.strip():
                print("\n[STDERR]:")
                print(clean_error)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    # Append log_level = debug to app.conf
    # We use tee -a to append
    cmd = "echo 'log_level = debug' | tee -a /data/harbor/common/config/core/app.conf"
    asyncio.run(run_remote_command(cmd))
    
    # Restart harbor-core
    cmd = "docker restart harbor-core"
    asyncio.run(run_remote_command(cmd))
