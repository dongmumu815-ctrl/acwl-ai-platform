
import paramiko
import sys

def verify_now():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        
        print("1. Curl Login (admin:Harbor12345)...")
        cmd = "curl -i -u 'admin:Harbor12345' http://127.0.0.1/api/v2.0/users/current"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        print("\n2. Registry Logs (Recent)...")
        cmd = "docker logs --since 10m registry"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("\n3. JobService Logs (Why 401?)...")
        cmd = "docker logs --since 10m harbor-jobservice"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    verify_now()
