
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
    # 1. Read docker-compose.yml
    print("\n--- Reading docker-compose.yml ---")
    await run_remote_command("cat /data/harbor/docker-compose.yml")
    
    # 2. Read registry config
    print("\n--- Reading registry config.yml ---")
    await run_remote_command("cat /data/harbor/common/config/registry/config.yml")
    
    # 3. Test notification endpoint manually again (trailing slash)
    test_cmd = """
    SECRET=$(docker exec harbor-core env | grep JOBSERVICE_SECRET | cut -d= -f2)
    echo "Using Secret: $SECRET"
    docker exec registry curl -v -H "Authorization: Harbor-Secret $SECRET" -H "Content-Type: application/json" -d '{"events": []}' http://core:8080/service/notifications/
    """
    print("\n--- Testing Notification Endpoint (Trailing Slash) ---")
    await run_remote_command(test_cmd)

if __name__ == "__main__":
    asyncio.run(main())
