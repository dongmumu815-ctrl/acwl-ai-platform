
import paramiko
import sys

def check_secretkey_type():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        print("Connected.")
        
        cmd = "ls -ld /data/harbor/common/config/core/certificates/secretkey"
        print(f"Checking secretkey: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode().strip()
        print(output)
        
        if output.startswith("d"):
            print("\n!!! IT IS A DIRECTORY !!!")
        else:
            print("\nIt is a file (or missing).")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_secretkey_type()
