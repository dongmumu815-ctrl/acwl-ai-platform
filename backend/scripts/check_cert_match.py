import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Comparing Key and Cert Modulus...")
        
        # Get modulus of private key
        cmd = f"echo '{PASS}' | sudo -S openssl rsa -in /data/harbor/common/config/core/private_key.pem -noout -modulus"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        key_mod = stdout.read().decode().strip()
        print(f"Key Modulus: {key_mod[:50]}...")
        
        # Get modulus of registry root cert
        cmd = f"echo '{PASS}' | sudo -S openssl x509 -in /data/harbor/common/config/registry/root.crt -noout -modulus"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        cert_mod = stdout.read().decode().strip()
        print(f"Cert Modulus: {cert_mod[:50]}...")
        
        if key_mod == cert_mod and key_mod != "":
            print("MATCH: Certificate matches Private Key.")
        else:
            print("MISMATCH: Certificate does NOT match Private Key!")
            print(f"Key: {key_mod}")
            print(f"Cert: {cert_mod}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
