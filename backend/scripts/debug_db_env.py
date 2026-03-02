
import paramiko
import sys

def debug_db_env():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        
        print("1. DB User Dump...")
        cmd = "docker exec harbor-db psql -U postgres -d registry -c \"SELECT user_id, username, password, salt, creation_time FROM harbor_user WHERE user_id = 1;\""
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\n2. Core Process Env (JOBSERVICE_SECRET)...")
        # Get PID of harbor_core process inside container
        # Then cat /proc/PID/environ
        cmd = "docker exec harbor-core sh -c 'env | grep SECRET'"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\n3. Secret Key File Content (Hex)...")
        cmd = "hexdump -C /data/harbor/common/config/core/certificates/secretkey"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_db_env()
