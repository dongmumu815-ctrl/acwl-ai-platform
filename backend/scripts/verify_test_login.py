import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    print("=== Verifying Logins ===")
    
    # 1. Test User
    print("\n--- Testing 'test' user (test1234) ---")
    token_url = "http://10.20.1.204:5000/service/token?service=harbor-registry&client_id=docker&offline_token=true"
    cmd = f"curl -v -u test:test1234 '{token_url}' 2>&1"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    if "HTTP/1.1 200 OK" in out:
        print("SUCCESS: test user login worked!")
    else:
        print("FAILURE: test user login failed.")
        
    # 2. Admin User
    print("\n--- Testing 'admin' user (Harbor12345) ---")
    cmd = f"curl -v -u admin:Harbor12345 '{token_url}' 2>&1"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    if "HTTP/1.1 200 OK" in out:
        print("SUCCESS: admin user login worked!")
    else:
        print("FAILURE: admin user login failed.")

    ssh.close()

if __name__ == "__main__":
    main()
