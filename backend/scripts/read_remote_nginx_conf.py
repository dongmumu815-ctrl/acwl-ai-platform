import paramiko
import sys

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
FILE_PATH = "/data/harbor/common/config/nginx/nginx.conf"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, username=USER, password=PASS)
        
        # Read file
        cmd = f"cat {FILE_PATH}"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        content = stdout.read().decode()
        error = stderr.read().decode()
        
        if error:
            print(f"Error reading file: {error}")
        else:
            # Print with line numbers for debugging
            lines = content.splitlines()
            for i, line in enumerate(lines):
                print(f"{i+1}: {line}")
                
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
