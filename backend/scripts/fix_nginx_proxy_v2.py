import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {HOST}...")
    try:
        ssh.connect(HOST, username=USER, password=PASS)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # 1. Read nginx.conf
    print("Reading nginx.conf...")
    cmd = f"echo '{PASS}' | sudo -S cat /data/harbor/common/config/nginx/nginx.conf"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    content = stdout.read().decode()
    
    # 2. Modify /v2/ location
    # Find: proxy_pass http://core:8080/v2/;
    # Replace: proxy_pass http://registry:5000/v2/;
    
    if "proxy_pass http://core:8080/v2/;" in content:
        print("Found Core proxy target. replacing with Registry...")
        new_content = content.replace(
            "proxy_pass http://core:8080/v2/;",
            "proxy_pass http://registry:5000/v2/;"
        )
        
        # Write back
        cmd = f"echo '{PASS}' | sudo -S sh -c 'cat > /data/harbor/common/config/nginx/nginx.conf <<EOF\n{new_content}EOF'"
        ssh.exec_command(cmd)
        print("Nginx config updated.")
        
        # 3. Restart Nginx
        print("Restarting Nginx...")
        cmd = f"echo '{PASS}' | sudo -S docker restart nginx"
        ssh.exec_command(cmd)
        time.sleep(5)
    else:
        print("Nginx config already points to registry or pattern not found.")
        print("Content snippet:")
        # Print the v2 location block to be sure
        import re
        match = re.search(r'location /v2/ \{[^}]+\}', content)
        if match:
            print(match.group(0))

    ssh.close()

if __name__ == "__main__":
    main()
