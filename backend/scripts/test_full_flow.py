import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

# The token we just got (simplified)
# We need to get a FRESH token and then try to use it against /v2/
# So we'll do it all in one script on the remote machine
def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Testing Full Auth Flow...")
        
        # Script to run on remote
        remote_script = """
        # 1. Get Token
        TOKEN_JSON=$(curl -s -u 'admin:Harbor12345' 'http://127.0.0.1:5000/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry')
        echo "Token Response: $TOKEN_JSON"
        
        # Extract Token (using python usually safer than sed/awk for json)
        TOKEN=$(echo $TOKEN_JSON | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))")
        
        if [ -z "$TOKEN" ]; then
            echo "Failed to extract token!"
            exit 1
        fi
        
        echo "Extracted Token: ${TOKEN:0:20}..."
        
        # 2. Use Token to access Registry
        echo "Testing Registry Access..."
        curl -v -H "Authorization: Bearer $TOKEN" http://127.0.0.1:5000/v2/
        """
        
        cmd = f"echo '{PASS}' | sudo -S bash -c '{remote_script}'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
