import paramiko
import asyncio
import os
import sys
import time

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from app.core.database import AsyncSessionLocal
from app.models.server import Server
from sqlalchemy import select

HOST = "10.20.1.221"

async def get_server_credentials():
    async with AsyncSessionLocal() as session:
        stmt = select(Server).where(Server.ip_address == HOST)
        result = await session.execute(stmt)
        server = result.scalar_one_or_none()
        if not server:
            raise Exception(f"Server {HOST} not found in DB")
        return server.ssh_username, server.ssh_password

async def run_remote_script(script_content):
    client = None
    try:
        user, password = await get_server_credentials()
        print(f"Connecting to {HOST} as {user}...")
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, port=22, username=user, password=password, timeout=15)
        
        # Write script to remote file
        script_path = "/tmp/migrate_docker.sh"
        sftp = client.open_sftp()
        with sftp.file(script_path, 'w') as f:
            f.write(script_content)
        sftp.chmod(script_path, 0o755)
        sftp.close()
        
        # Execute script with sudo
        print("Executing migration script...")
        command = f"echo '{password}' | sudo -S -p '' {script_path}"
        
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        
        # Stream output
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line.strip())
            
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("✅ Migration script completed successfully.")
        else:
            print(f"❌ Script failed with exit code {exit_status}")
            err = stderr.read().decode()
            if err:
                print(f"STDERR: {err}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if client:
            client.close()

SCRIPT = """#!/bin/bash
set -e

DATA_DIR="/data/docker-data"
BACKUP_DIR="/var/lib/docker.bak"

echo "Checking disk space..."
df -h / /data

if [ -d "$DATA_DIR" ]; then
    echo "Warning: $DATA_DIR already exists."
else
    echo "Creating $DATA_DIR..."
    mkdir -p "$DATA_DIR"
fi

echo "Stopping Docker service..."
systemctl stop docker

echo "Migrating data from /var/lib/docker to $DATA_DIR..."
# Use rsync to preserve permissions and links
if [ -d "/var/lib/docker" ]; then
    rsync -aP /var/lib/docker/ "$DATA_DIR/"
else
    echo "Warning: /var/lib/docker does not exist, skipping sync."
fi

echo "Backing up old data directory..."
if [ -d "/var/lib/docker" ]; then
    mv /var/lib/docker "$BACKUP_DIR"
fi

echo "Configuring Docker daemon..."
CONFIG_FILE="/etc/docker/daemon.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "{}" > "$CONFIG_FILE"
fi

# Use python to update json safely
python3 -c "
import json
import os

f_path = '$CONFIG_FILE'
target = '$DATA_DIR'

try:
    with open(f_path, 'r') as f:
        data = json.load(f)
except:
    data = {}

data['data-root'] = target

with open(f_path, 'w') as f:
    json.dump(data, f, indent=4)
print('Updated daemon.json')
"

echo "Starting Docker service..."
systemctl start docker

echo "Verifying..."
docker info | grep "Docker Root Dir"

echo "Migration Completed."
"""

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    print("WARNING: This will stop Docker service on 10.20.1.221 and migrate data to /data/docker-data.")
    print("Existing containers will be stopped and restarted.")
    # In a real scenario, we might ask for confirmation, but here we just prepare the script.
    # asyncio.run(run_remote_script(SCRIPT))
    print("Script is ready in backend/scripts/migrate_docker.py. Run it to execute migration.")
"""

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Check args
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        asyncio.run(run_remote_script(SCRIPT))
    else:
        print("This script will migrate Docker data on 10.20.1.221 to /data/docker-data.")
        print("To execute, run: python backend/scripts/migrate_docker.py --run")
