import paramiko
import os
import sys

def deploy_and_run_training(
    server_ip, 
    ssh_port, 
    username, 
    password, 
    job_id, 
    env_name, 
    swift_args
):
    """
    连接到通过 servers/index.vue 管理的 GPU 服务器，
    部署 run_ms_swift_training.sh 脚本，并执行微调任务。
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"[{server_ip}] 正在连接 GPU 服务器...")
        client.connect(hostname=server_ip, port=ssh_port, username=username, password=password)
        print(f"[{server_ip}] 连接成功！")
        
        # 1. 上传训练脚本到服务器的 /tmp 目录
        sftp = client.open_sftp()
        local_script = os.path.join(os.path.dirname(__file__), 'run_ms_swift_training.sh')
        remote_script = '/tmp/run_ms_swift_training.sh'
        
        sftp.put(local_script, remote_script)
        sftp.close()
        
        # 2. 赋予执行权限
        client.exec_command(f'chmod +x {remote_script}')
        print(f"[{server_ip}] 训练脚本上传并授权完毕: {remote_script}")
        
        # 3. 拼接命令
        # 参数必须按顺序传入脚本，先 job_id，再 env_name，剩下的全部交给 swift sft
        command = f'{remote_script} {job_id} {env_name} {swift_args}'
        print(f"[{server_ip}] 准备执行训练命令:\n{command}")
        
        # 4. 执行命令并实时获取输出（如果需要长时间运行，建议使用 nohup，并在后台监控）
        # 这里为了演示，我们直接在前台同步阻塞读取日志，生产环境建议用 nohup
        # nohup_command = f'nohup {command} > /tmp/training_deploy.log 2>&1 &'
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        
        # 实时打印日志
        for line in iter(stdout.readline, ""):
            print(f"[{server_ip} 训练日志] {line.strip()}")
            
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print(f"[{server_ip}] 训练任务 {job_id} 成功结束！")
        else:
            print(f"[{server_ip}] 训练任务 {job_id} 失败，退出码: {exit_status}")
            
    except Exception as e:
        print(f"连接或执行异常: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    # 模拟从前端 create.vue 获取到的配置，并在后端生成调度任务
    JOB_ID = "job_20231001_001"
    ENV_NAME = "ms_swift_env"
    
    # 构建 swift sft 的核心参数（对应前端选的 BERT 或 LLaMA）
    # 以微调 Qwen 为例
    SWIFT_ARGS = (
        "--model_type qwen1half-7b-chat "
        "--sft_type lora "
        "--dataset alpaca-zh "  # 示例数据集
        "--lora_rank 16 "
        "--learning_rate 1e-4 "
        "--num_train_epochs 3 "
        "--batch_size 16 "
        "--fp16 true"
    )
    
    # 替换为你实际管理的 GPU 服务器的 IP 和密码
    deploy_and_run_training(
        server_ip="192.168.1.100", 
        ssh_port=22, 
        username="root", 
        password="your_password", 
        job_id=JOB_ID, 
        env_name=ENV_NAME, 
        swift_args=SWIFT_ARGS
    )
