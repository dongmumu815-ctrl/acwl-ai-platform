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
        
        print("1. Rewriting env file without ADMIN_PASSWORD...")
        # Read current env
        cmd = f"echo '{PASS}' | sudo -S cat /data/harbor/common/config/core/env"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        lines = stdout.read().decode().splitlines()
        
        # Filter
        new_lines = [l for l in lines if "ADMIN_PASSWORD" not in l]
        new_content = "\n".join(new_lines) + "\n"
        
        # Write back (using temporary file to avoid sudo permission issues with redirection)
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/core_env", "w") as f:
            f.write(new_content)
        sftp.close()
        
        cmd = f"echo '{PASS}' | sudo -S mv /tmp/core_env /data/harbor/common/config/core/env"
        ssh.exec_command(cmd)
        
        print("2. Re-applying DB Fixes...")
        # Fix Schema
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c 'ALTER TABLE harbor_user ALTER COLUMN password TYPE character varying(128);'"
        ssh.exec_command(cmd)
        # Update Data
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"UPDATE harbor_user SET password = '{NEW_HASH}', salt = '', password_version = 'v3' WHERE user_id = 1;\""
        ssh.exec_command(cmd)
        
        print("3. Recreating Harbor Core Container (to reload env)...")
        cmd = f"echo '{PASS}' | sudo -S docker rm -f harbor-core"
        ssh.exec_command(cmd)
        cmd = f"echo '{PASS}' | sudo -S docker compose -f /data/harbor/docker-compose.yml up -d"
        ssh.exec_command(cmd)
        
        print("Waiting for startup (10s)...")
        time.sleep(10)
        
        print("4. Checking Core Logs for password update message...")
        cmd = f"echo '{PASS}' | sudo -S docker logs --tail 20 harbor-core"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        logs = stdout.read().decode()
        if "updated its encrypted password" in logs:
            print("WARNING: Core STILL updated the password!")
        else:
            print("SUCCESS: Core did not update the password (presumably).")
            
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
