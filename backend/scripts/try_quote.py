
import paramiko
import sys

def try_quoted_password():
    hostname = "10.20.1.204"
    username = "ubuntu"
    password = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, username=username, password=password)
        
        print("Trying with quotes: 'Harbor12345!'")
        # curl -u "admin:'Harbor12345!'"
        cmd = "curl -i -u \"admin:'Harbor12345!'\" http://127.0.0.1/api/v2.0/users/current"
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        if "200 OK" in out:
            print("SUCCESS with quotes!")
        else:
            print("Failed with quotes.")
            print(out)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    try_quoted_password()
