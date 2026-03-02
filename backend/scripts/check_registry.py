
import paramiko
import sys

def check_registry_content():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        # Check repositories
        cmd = "ls -R /data/harbor/registry/docker/registry/v2/repositories"
        print(f"Checking registry content: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode()
        err = stderr.read().decode()
        
        if "No such file" in err:
            print("Registry directory does not exist or is empty.")
        elif not output.strip():
            print("Registry is empty.")
        else:
            print("Registry has content:")
            print(output)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_registry_content()
