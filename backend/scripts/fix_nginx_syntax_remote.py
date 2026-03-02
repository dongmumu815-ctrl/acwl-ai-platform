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
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASS)
        
        # Read file
        print(f"Reading {FILE_PATH}...")
        cmd = f"cat {FILE_PATH}"
        stdin, stdout, stderr = client.exec_command(cmd)
        content = stdout.read().decode()
        
        if not content:
            print("Error: File is empty or could not be read")
            sys.exit(1)

        # Fix the syntax errors
        print("Fixing syntax errors...")
        new_content = content.replace("proxy_set_header Host ;", "proxy_set_header Host $host;")
        new_content = new_content.replace("proxy_set_header X-Real-IP ;", "proxy_set_header X-Real-IP $remote_addr;")
        new_content = new_content.replace("proxy_set_header X-Forwarded-For ;", "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
        
        # Verify changes
        if "proxy_set_header Host $host;" not in new_content:
            print("Error: Replacement failed or pattern not found")
            sys.exit(1)

        # Write back to file
        # We use a temporary file to avoid sudo shell redirection issues with complex content
        temp_remote_path = "/tmp/nginx.conf.fixed"
        
        # Write to local temp file then scp? No, just write using SFTP
        sftp = client.open_sftp()
        with sftp.file(temp_remote_path, 'w') as f:
            f.write(new_content)
        
        print(f"Wrote fixed content to {temp_remote_path}")
        
        # Move it to the correct location with sudo
        print("Moving file to destination with sudo...")
        cmd = f"echo '{PASS}' | sudo -S mv {temp_remote_path} {FILE_PATH}"
        client.exec_command(cmd)
        
        # Restart Nginx
        print("Restarting Nginx container...")
        cmd = f"echo '{PASS}' | sudo -S docker restart nginx"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print(f"Stderr: {err}")

        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
