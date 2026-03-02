
import paramiko
import asyncio

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

async def run_remote_command(command):
    print(f"Executing: {command}")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASS)
        full_cmd = f"echo '{PASS}' | sudo -S {command}"
        stdin, stdout, stderr = client.exec_command(full_cmd)
        
        out = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        
        if out: print(f"[STDOUT]:\n{out}")
        if err: 
            clean_err = '\n'.join([line for line in err.split('\n') if "[sudo] password" not in line])
            if clean_err.strip(): print(f"[STDERR]:\n{clean_err}")
            
        return out
    finally:
        client.close()

async def main():
    # Check jobservice config
    print("\n--- jobservice/config.yml ---")
    await run_remote_command("cat /data/harbor/common/config/jobservice/config.yml")
    
    # Check portal nginx conf
    print("\n--- portal/nginx.conf ---")
    await run_remote_command("cat /data/harbor/common/config/portal/nginx.conf")
    
    # Check core env (first 20 lines)
    print("\n--- core/env ---")
    await run_remote_command("head -n 20 /data/harbor/common/config/core/env")
    
    # Check internal config API
    # We need to know the secret to auth?
    # No, internal config API is usually protected by internal secret.
    # Jobservice uses secret from config.
    # We can try to curl it if we get the secret.
    
    # Get secret
    secret_cmd = "grep JOBSERVICE_SECRET /data/harbor/common/config/core/env | cut -d= -f2"
    print("\n--- Getting Secret ---")
    # Wait, env file format is key=value?
    # Or export key=value?
    # Usually key=value.
    
    test_cmd = """
    SECRET=$(grep JOBSERVICE_SECRET /data/harbor/common/config/core/env | cut -d= -f2 | tr -d '\\r')
    echo "Using Secret: '$SECRET'"
    
    # Try to curl from core container itself (to avoid network issues)
    docker exec harbor-core curl -v -H "Authorization: Harbor-Secret $SECRET" http://localhost:8080/api/v2.0/internalconfig
    """
    print("\n--- Testing Core API ---")
    await run_remote_command(test_cmd)

if __name__ == "__main__":
    asyncio.run(main())
