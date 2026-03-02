
import paramiko
import sys

def check_secrets():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        
        print("--- secretkey ---")
        cmd = "cat /data/harbor/common/config/core/certificates/secretkey"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\n--- jobservice_secret ---")
        cmd = "cat /data/harbor/common/config/secret/jobservice_secret"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\n--- core env ---")
        cmd = "cat /data/harbor/common/config/core/env | grep SECRET"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\n--- jobservice env ---")
        cmd = "cat /data/harbor/common/config/jobservice/env | grep SECRET"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_secrets()
