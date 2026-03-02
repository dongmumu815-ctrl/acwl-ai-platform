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
        
        print("1. Removing ADMIN_PASSWORD from env file...")
        cmd = f"echo '{PASS}' | sudo -S sed -i '/ADMIN_PASSWORD/d' /data/harbor/common/config/core/env"
        ssh.exec_command(cmd)
        
        print("2. Fixing Schema (Just in case)...")
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c 'ALTER TABLE harbor_user ALTER COLUMN password TYPE character varying(128);'"
        ssh.exec_command(cmd)
        
        print("3. Updating Password to Bcrypt (v3)...")
        # Update password AND password_version
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"UPDATE harbor_user SET password = '{NEW_HASH}', salt = '', password_version = 'v3' WHERE user_id = 1;\""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        print("4. Restarting Core...")
        cmd = f"echo '{PASS}' | sudo -S docker restart harbor-core"
        ssh.exec_command(cmd)
        
        print("Waiting for startup (10s)...")
        time.sleep(10)
        
        print("5. Verifying DB state...")
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c 'SELECT password_version, password FROM harbor_user WHERE user_id = 1;'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
