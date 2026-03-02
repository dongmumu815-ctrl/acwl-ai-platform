import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
# Escaped $ for shell execution
NEW_HASH = r"\$2b\$12\$jhYxM20l5gaVQN8ZqdyFhOC0.wER1u2JD8vw9GNtAr6AaMQBOvtT."

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("1. Ensuring ADMIN_PASSWORD is removed from env file...")
        cmd = f"echo '{PASS}' | sudo -S sed -i '/ADMIN_PASSWORD/d' /data/harbor/common/config/core/env"
        ssh.exec_command(cmd)
        
        print("2. Re-applying DB Fixes (Schema & Data)...")
        # Fix Schema
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c 'ALTER TABLE harbor_user ALTER COLUMN password TYPE character varying(128);'"
        ssh.exec_command(cmd)
        # Update Data
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"UPDATE harbor_user SET password = '{NEW_HASH}', salt = '', password_version = 'v3' WHERE user_id = 1;\""
        ssh.exec_command(cmd)
        
        print("3. Recreating Harbor Core Container...")
        # Remove
        cmd = f"echo '{PASS}' | sudo -S docker rm -f harbor-core"
        ssh.exec_command(cmd)
        
        # Up (Recreate)
        # We need to run docker compose up for harbor-core specifically or all
        # To be safe, let's just run up -d for everything, it will recreate core because it's missing
        cmd = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        print("Waiting for startup (10s)...")
        time.sleep(10)
        
        print("4. Verifying DB state (Should be v3)...")
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c 'SELECT password_version, password FROM harbor_user WHERE user_id = 1;'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
