
import paramiko
import asyncio
import os

# Configuration
HOST = "10.20.1.204"
PORT = 22
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

async def run_remote_command(command):
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, password=PASS)
        print(f"Executing: {command}")
        stdin, stdout, stderr = client.exec_command(command)
        
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if output:
            print("\n[STDOUT]:")
            print(output)
        if error:
            print("\n[STDERR]:")
            print(error)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    # Read harbor.yml
    cmd = f"echo '{PASS}' | sudo -S cat /data/harbor/harbor.yml"
    asyncio.run(run_remote_command(cmd))
