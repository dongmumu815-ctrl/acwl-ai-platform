
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
        return stdout.read().decode('utf-8'), stderr.read().decode('utf-8')
    finally:
        client.close()

async def main():
    # 1. 获取 Secret
    out, err = await run_remote_command("docker exec harbor-core env | grep JOBSERVICE_SECRET")
    secret = out.split('=')[1].strip() if '=' in out else "ttvSp4wGBUebD56ryYbbgw"
    print(f"Using Secret: {secret}")

    # 2. 构造新的通知配置内容
    # 注意：Harbor 要求 Authorization 头部是一个列表格式 [Harbor-Secret ...]
    notif_config = f"""
notifications:
  endpoints:
    - name: harbor
      url: http://core:8080/service/notifications
      timeout: 3000ms
      threshold: 5
      backoff: 1s
      headers:
        Authorization: [Harbor-Secret {secret}]
"""
    
    # 3. 删除旧的 notifications 部分
    # sed -i '/notifications:/,$d' /data/harbor/common/config/registry/config.yml
    cmd_del = "sed -i '/^notifications:/,$d' /data/harbor/common/config/registry/config.yml"
    # Execute with sudo
    await run_remote_command(cmd_del)
    
    # 4. 追加新配置
    import base64
    # The config string to append
    config_str = f"""
notifications:
  endpoints:
    - name: harbor
      url: http://core:8080/service/notifications
      headers:
        Authorization: [Harbor-Secret {secret}]
      timeout: 3000ms
      threshold: 5
      backoff: 1s
"""
    encoded_config = base64.b64encode(config_str.encode()).decode()
    
    # Use sh -c to handle permissions for redirection
    cmd_append = f"sh -c 'echo {encoded_config} | base64 -d >> /data/harbor/common/config/registry/config.yml'"
    await run_remote_command(cmd_append)

    # 5. 重启 Registry 使配置生效
    await run_remote_command("docker restart registry")
    print("Registry restarted with new notification config.")

if __name__ == "__main__":
    asyncio.run(main())
