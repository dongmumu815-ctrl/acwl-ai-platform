
import paramiko
import asyncio

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

async def run_remote_command(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASS)
        full_cmd = f"echo '{PASS}' | sudo -S {command}"
        stdin, stdout, stderr = client.exec_command(full_cmd)
        return stdout.read().decode('utf-8')
    finally:
        client.close()

async def main():
    # 1. Get Secret
    out = await run_remote_command("docker exec harbor-core env | grep JOBSERVICE_SECRET")
    secret = out.split('=')[1].strip() if '=' in out else "ttvSp4wGBUebD56ryYbbgw"
    
    print(f"Testing notification with secret: {secret}")
    
    # 2. Test with curl from Registry container
    # Header format: Authorization: Harbor-Secret <secret>
    # Wait, in the config I wrote: Authorization: [Harbor-Secret <secret>]
    # This means the YAML list format.
    # In YAML: 
    # headers:
    #   Authorization: [val1]
    # Means the header value is "val1" (if list of size 1).
    # Or does it mean multiple headers?
    # Registry config parses headers as map[string]string or map[string][]string?
    # If it's map[string]interface{}, [val] might be serialized.
    
    # Let's try sending the request with the raw header that Core expects.
    # Core expects "Harbor-Secret <secret>" (without brackets).
    # If I configured Registry with brackets, maybe that's correct for YAML to ensure it's a list?
    # Or maybe it's incorrect?
    
    # Let's first test what Core accepts.
    url = "http://core:8080/service/notifications"
    content_type = "application/vnd.docker.distribution.events.v1+json"
    
    # Try 1: Raw Harbor-Secret
    print("\n--- Testing Raw Harbor-Secret ---")
    auth_header = f"Authorization: Harbor-Secret {secret}"
    cmd = f"docker exec registry curl -v -s -H 'Content-Type: {content_type}' -H '{auth_header}' -d '{{\"events\": []}}' {url}"
    print(await run_remote_command(cmd))

if __name__ == "__main__":
    asyncio.run(main())
