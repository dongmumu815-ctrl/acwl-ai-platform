
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
    # Data for the new image (0.87-fixed)
    # Digest: sha256:98c665f9194f4bb29bc42118293c9a53d89ae9830c01cf79b43a58e4169f85c5
    # Repo ID: 1
    # Project ID: 2
    # Repo Name: prod/actable-server
    
    # 1. Insert into artifact table
    # We use some values from existing artifact 6
    insert_artifact_sql = """
    INSERT INTO artifact (
        project_id, repository_name, digest, type, 
        push_time, repository_id, media_type, manifest_media_type, 
        size, artifact_type
    ) VALUES (
        2, 'prod/actable-server', 'sha256:98c665f9194f4bb29bc42118293c9a53d89ae9830c01cf79b43a58e4169f85c5', 'IMAGE',
        NOW(), 1, 'application/vnd.oci.image.index.v1+json', 'application/vnd.oci.image.index.v1+json',
        856, 'IMAGE'
    ) RETURNING id;
    """
    
    print("\n--- Inserting Artifact ---")
    psql_artifact = f"docker exec harbor-db psql -U postgres -d registry -t -c \"{insert_artifact_sql}\""
    artifact_id_str = await run_remote_command(psql_artifact)
    
    artifact_id = artifact_id_str.strip()
    print(f"New Artifact ID: {artifact_id}")
    
    if not artifact_id:
        print("Failed to get artifact ID")
        return

    # 2. Insert into tag table
    insert_tag_sql = f"""
    INSERT INTO tag (
        repository_id, artifact_id, name, push_time
    ) VALUES (
        1, {artifact_id}, '0.87-fixed', NOW()
    );
    """
    
    print("\n--- Inserting Tag ---")
    psql_tag = f"docker exec harbor-db psql -U postgres -d registry -c \"{insert_tag_sql}\""
    await run_remote_command(psql_tag)
    
    # 3. Verify via API
    print("\n--- Final Verification ---")
    cmd_artifacts = """curl -s -u 'admin:Harbor12345' -H 'Content-Type: application/json' 'http://localhost:5000/api/v2.0/projects/prod/repositories/actable-server/artifacts?page=1&page_size=10&with_tag=true'"""
    await run_remote_command(cmd_artifacts)

if __name__ == "__main__":
    asyncio.run(main())
