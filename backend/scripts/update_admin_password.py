import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

# This hash is generated on the remote server using python3-bcrypt
# Escape $ for shell execution
NEW_HASH = r"\$2b\$12\$jhYxM20l5gaVQN8ZqdyFhOC0.wER1u2JD8vw9GNtAr6AaMQBOvtT."

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print(f"Updating admin password to hash: {NEW_HASH}")
        
        # 1. Fix Schema Length
        print("Fixing Schema Length...")
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c 'ALTER TABLE harbor_user ALTER COLUMN password TYPE character varying(128);'"
        ssh.exec_command(cmd)
        
        # 2. Update Password
        # Note: Set salt to empty string because bcrypt includes salt
        # Use single quotes for the SQL string value, and wrap the whole command carefully
        # We rely on the escaped $ in NEW_HASH to survive shell interpolation
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c \"UPDATE harbor_user SET password = '{NEW_HASH}', salt = '' WHERE user_id = 1;\""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        print(out)
        print(err)
        
        print("Verifying update...")
        cmd = f"echo '{PASS}' | sudo -S docker exec harbor-db psql -U postgres -d registry -c 'SELECT user_id, username, password, salt FROM harbor_user WHERE user_id = 1;'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        print("Restarting Harbor Core to flush cache (if any)...")
        cmd = f"echo '{PASS}' | sudo -S docker restart harbor-core"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
