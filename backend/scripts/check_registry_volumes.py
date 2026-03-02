import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Checking Registry Volumes...")
        cmd = f"echo '{PASS}' | sudo -S cat /data/harbor/docker-compose.yml"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        lines = stdout.read().decode().split('\n')
        in_registry = False
        in_volumes = False
        for line in lines:
            if "container_name: registry" in line:
                in_registry = True
                print("Found registry service")
            elif in_registry and "volumes:" in line:
                in_volumes = True
                print("Volumes:")
            elif in_registry and in_volumes and line.strip().startswith("-"):
                print(line)
            elif in_registry and line.strip() and not line.startswith(" ") and not line.startswith("-") and not "container_name" in line:
                # End of service definition
                if in_volumes: # Only break if we were in volumes and indentation changed back
                     pass 
            
            if in_registry and "services:" in line: 
                pass

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
