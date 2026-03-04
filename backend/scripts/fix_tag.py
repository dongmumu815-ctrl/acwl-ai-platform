
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
    # Insert tag for artifact 9
    insert_tag_sql = """
    INSERT INTO tag (
        repository_id, artifact_id, name, push_time
    ) VALUES (
        1, 9, '0.87-fixed', NOW()
    ) ON CONFLICT (repository_id, name) DO NOTHING;
    """
    
    print("\n--- Inserting Tag for Artifact 9 ---")
    psql_tag = f"docker exec harbor-db psql -U postgres -d registry -c \"{insert_tag_sql}\""
    await run_remote_command(psql_tag)
    
    # Final Verify
    print("\n--- Final API Verification ---")
    cmd_artifacts = """curl -s -u 'admin:Harbor12345' -H 'Content-Type: application/json' 'http://localhost:5000/api/v2.0/projects/prod/repositories/actable-server/artifacts?page=1&page_size=10&with_tag=true'"""
    await run_remote_command(cmd_artifacts)

if __name__ == "__main__":
    asyncio.run(main())
