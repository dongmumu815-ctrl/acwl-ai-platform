
import paramiko
import asyncio
import json

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
    # 1. Wait
    print("\n--- Waiting 15s ---")
    await asyncio.sleep(15)
    
    # 2. Check Status
    print("\n--- Checking Status ---")
    await run_remote_command("docker ps")
    
    # 3. Check jobservice logs (last 20)
    print("\n--- Jobservice Logs ---")
    await run_remote_command("docker logs harbor-jobservice 2>&1 | tail -n 20")
    
    # 4. Create project 'prod'
    # Default admin: Harbor12345
    # POST /api/v2.0/projects
    print("\n--- Creating Project 'prod' ---")
    cmd_create = """curl -u 'admin:Harbor12345' -H 'Content-Type: application/json' -d '{"project_name": "prod", "public": true}' http://localhost:5000/api/v2.0/projects"""
    await run_remote_command(cmd_create)
    
    # 5. Verify Project
    print("\n--- Verifying Project ---")
    cmd_verify = """curl -u 'admin:Harbor12345' -H 'Content-Type: application/json' http://localhost:5000/api/v2.0/projects/prod"""
    await run_remote_command(cmd_verify)
    
    # 6. Push image
    # We have localhost:5000/prod/actable-server:0.87 tagged locally?
    # Yes, from previous attempts. But we need to login again because DB wiped?
    # Docker client caches credentials.
    # But user credentials (admin) are same (Harbor12345).
    # So existing login might work.
    
    print("\n--- Pushing Image ---")
    # Retag just in case
    await run_remote_command("docker tag localhost:5000/prod/actable-server:0.87 localhost:5000/prod/actable-server:0.87-fixed")
    
    # Push
    await run_remote_command("docker push localhost:5000/prod/actable-server:0.87-fixed")
    
    # 7. Check API for artifacts
    print("\n--- Checking Artifacts in API ---")
    cmd_api = """curl -u 'admin:Harbor12345' -H 'Content-Type: application/json' 'http://localhost:5000/api/v2.0/projects/prod/repositories/actable-server/artifacts?page=1&page_size=10'"""
    await run_remote_command(cmd_api)

if __name__ == "__main__":
    asyncio.run(main())
