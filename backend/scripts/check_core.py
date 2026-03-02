
import paramiko
import sys
import time

def check_core_status():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        
        print("Checking docker ps...")
        stdin, stdout, stderr = client.exec_command("docker ps | grep harbor-core")
        print(stdout.read().decode())
        
        print("Checking logs...")
        stdin, stdout, stderr = client.exec_command("docker logs --tail 20 harbor-core")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_core_status()
