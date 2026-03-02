import paramiko
import time

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Testing Full Auth Flow...")
        
        # 1. Get Token
        print("Getting Token...")
        cmd = f"echo '{PASS}' | sudo -S curl -s -u 'admin:Harbor12345' 'http://127.0.0.1:5000/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        token_json = stdout.read().decode().strip()
        
        if not token_json or "token" not in token_json:
            print("Failed to get token JSON")
            print(token_json)
            return

        # Simple extraction via python on local since we have the json string
        import json
        try:
            token_data = json.loads(token_json)
            token = token_data.get("token")
        except:
            print("Failed to parse token JSON")
            print(token_json)
            return
            
        print(f"Got Token: {token[:20]}...")
        
        # 2. Test Registry Access
        print("Testing Registry Access with Token...")
        cmd = f"echo '{PASS}' | sudo -S curl -v -H 'Authorization: Bearer {token}' http://127.0.0.1:5000/v2/"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        out = stdout.read().decode()
        err = stderr.read().decode()
        print("STDOUT:", out)
        print("STDERR:", err)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
