
import paramiko
import time
import sys

def check_file_timestamp():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # Check timestamp of jobservice env
        cmd = "ls -l /data/harbor/common/config/jobservice/env"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"\nChecking JobService Env: {cmd}")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # Check content of jobservice env (to see if secret is there)
        cmd = "cat /data/harbor/common/config/jobservice/env"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"\nContent of JobService Env:")
        print(stdout.read().decode())
        
        # Check Core env content
        cmd = "cat /data/harbor/common/config/core/env"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"\nContent of Core Env:")
        content = stdout.read().decode()
        print(content)

        # Check RegistryCtl config
        cmd = "ls -l /data/harbor/common/config/registryctl/config.yml"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"\nChecking RegistryCtl Config: {cmd}")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        cmd = "cat /data/harbor/common/config/registryctl/config.yml"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"\nContent of RegistryCtl Config:")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_file_timestamp()
