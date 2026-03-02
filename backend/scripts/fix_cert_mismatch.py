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
        
        print("Regenerating Root Cert from Private Key...")
        
        # 1. Generate CSR using existing Private Key
        cmd = f"echo '{PASS}' | sudo -S openssl req -new -key /data/harbor/common/config/core/private_key.pem -out /data/harbor/common/config/registry/root.csr -subj '/C=CN/ST=BJ/L=BJ/O=Harbor/CN=harbor-registry'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # 2. Generate Self-Signed Cert using the SAME key
        cmd = f"echo '{PASS}' | sudo -S openssl x509 -req -days 3650 -in /data/harbor/common/config/registry/root.csr -signkey /data/harbor/common/config/core/private_key.pem -out /data/harbor/common/config/registry/root.crt"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        print(out)
        print(err)
        
        # 3. Verify match
        print("Verifying match...")
        cmd_verify = """
        KEY_MOD=$(openssl rsa -in /data/harbor/common/config/core/private_key.pem -noout -modulus)
        CERT_MOD=$(openssl x509 -in /data/harbor/common/config/registry/root.crt -noout -modulus)
        if [ "$KEY_MOD" = "$CERT_MOD" ]; then echo "MATCH"; else echo "MISMATCH"; fi
        """
        cmd = f"echo '{PASS}' | sudo -S bash -c '{cmd_verify}'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        
        # 4. Restart Registry
        print("Restarting Registry...")
        cmd = f"echo '{PASS}' | sudo -S docker restart registry"
        ssh.exec_command(cmd)
        
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
