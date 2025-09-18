import paramiko

# 服务器配置
host = 'bt.acoming.net'
port = 22
username = 'acoming'
password = '1qaz@WSXaczt'  # 建议改用密钥认证

# 创建SSH客户端
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # 连接服务器
    ssh.connect(host, port, username, password)
    
    # 执行命令（示例：获取系统信息）
    stdin, stdout, stderr = ssh.exec_command('uname -a && df -h')
    print(stdout.read().decode())
    
except Exception as e:
    print(f"连接失败: {e}")
finally:
    ssh.close()