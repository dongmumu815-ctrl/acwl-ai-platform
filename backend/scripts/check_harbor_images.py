import paramiko
import sys

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS)
        
        # 1. Check storage
        print("\n=== Checking Storage ===")
        cmd = f"echo '{PASS}' | sudo -S ls -R /data/harbor/registry/docker/registry/v2/repositories/prod"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        if "No such file or directory" in err or "No such file or directory" in out:
             print("Directory /data/harbor/registry/docker/registry/v2/repositories/prod does not exist.")
        else:
             print(out)
             print(err)

        # 2. Check Registry Config for notifications
        print("\n=== Checking Registry Config ===")
        cmd = f"cat /data/harbor/common/config/registry/config.yml"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        # 3. Check DB Artifacts
        print("\n=== Checking DB Artifacts ===")
        # We need to find the project_id for 'prod' first
        sql_proj = "select project_id, name from project where name='prod';"
        cmd_proj = f"echo '{PASS}' | sudo -S docker exec postgres psql -U postgres -d registry -c \"{sql_proj}\""
        stdin, stdout, stderr = client.exec_command(cmd_proj)
        proj_out = stdout.read().decode()
        print(proj_out)
        
        # If we can parse the ID, check artifacts
        # Assuming ID is in the output
        
        sql_art = "select * from artifact limit 5;"
        cmd_art = f"echo '{PASS}' | sudo -S docker exec postgres psql -U postgres -d registry -c \"{sql_art}\""
        stdin, stdout, stderr = client.exec_command(cmd_art)
        print(stdout.read().decode())
        print(stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
