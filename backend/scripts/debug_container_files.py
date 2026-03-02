
import paramiko
import sys

def debug_container_files():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # 1. Check registryctl file access
        print("\n=== Checking RegistryCtl File Access ===")
        cmd = "docker exec registryctl ls -l /etc/registry/config.yml"
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("\n=== Cat RegistryCtl Config (Internal) ===")
        cmd = "docker exec registryctl cat /etc/registryctl/config.yml"
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\n=== Cat Registry Config (Internal via RegistryCtl) ===")
        cmd = "docker exec registryctl cat /etc/registry/config.yml"
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        # 2. Check JobService config
        print("\n=== Cat JobService Config (Internal) ===")
        cmd = "docker exec harbor-jobservice cat /etc/jobservice/config.yml"
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_container_files()
