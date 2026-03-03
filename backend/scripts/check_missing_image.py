
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
    # 1. List Repositories via API
    print("\n--- Listing Repositories in 'prod' ---")
    # Using admin:Harbor12345
    # GET /projects/prod/repositories
    cmd_repos = """curl -s -u 'admin:Harbor12345' -H 'Content-Type: application/json' 'http://localhost:5000/api/v2.0/projects/prod/repositories?page=1&page_size=10'"""
    repos_json = await run_remote_command(cmd_repos)
    
    repos = []
    try:
        repos = json.loads(repos_json)
        print(f"Found {len(repos)} repositories: {[r['name'] for r in repos]}")
    except:
        print(f"Failed to parse JSON: {repos_json}")
        
    # 2. For each repo, list artifacts
    for repo in repos:
        repo_name = repo['name'] # format: prod/actable-server
        encoded_repo = repo_name.replace('/', '%2F')
        print(f"\n--- Artifacts in {repo_name} ---")
        cmd_artifacts = f"""curl -s -u 'admin:Harbor12345' -H 'Content-Type: application/json' 'http://localhost:5000/api/v2.0/projects/prod/repositories/{encoded_repo.split('/')[-1]}/artifacts?page=1&page_size=10&with_tag=true'"""
        # Wait, repository name in URL should be encoded project/repo? No, just repo name under project.
        # Actually API is /projects/{project_name}/repositories/{repository_name}/artifacts
        # repository_name is usually just the part after project name, e.g. 'actable-server'.
        # But `repo['name']` returns full path `prod/actable-server`.
        # So we need to split.
        short_name = repo_name.split('/')[-1]
        
        await run_remote_command(cmd_artifacts)

    # 3. Check Registry Logs (last 50 lines) to see pushes
    print("\n--- Registry Logs (Last 50) ---")
    await run_remote_command("docker logs registry 2>&1 | tail -n 50")
    
    # 4. Check Core Logs (last 50 lines) to see notifications
    print("\n--- Core Logs (Last 50) ---")
    await run_remote_command("docker logs harbor-core 2>&1 | tail -n 50")

    # 5. Check physical storage
    print("\n--- Physical Storage Check ---")
    await run_remote_command("ls -R /data/harbor/registry/docker/registry/v2/repositories/prod")

if __name__ == "__main__":
    asyncio.run(main())
