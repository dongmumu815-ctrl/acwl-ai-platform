#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微调训练部署模块
支持异步执行和 WebSocket 进度推送
"""

import paramiko1
import os
import sys
import json
import time
import threading
import asyncio
from datetime import datetime
from typing import Optional, Callable, Dict, Any

class FineTuningDeployer:
    """
    微调训练部署器
    支持异步执行和进度回调
    """

    def __init__(
        self,
        server_ip: str,
        ssh_port: int,
        username: str,
        password: str,
        job_id: str,
        env_name: str = "msswift",
        log_dir: str = "/tmp/training_logs"
    ):
        self.server_ip = server_ip
        self.ssh_port = ssh_port
        self.username = username
        self.password = password
        self.job_id = job_id
        self.env_name = env_name
        self.log_dir = log_dir
        self.log_file = None
        self.is_running = False
        self.progress_callback: Optional[Callable] = None
        self.client: Optional[paramiko.SSHClient] = None

    def set_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """设置进度回调函数"""
        self.progress_callback = callback

    def _notify_progress(self, progress: int, status: str, message: str, epoch: Optional[int] = None, total_epochs: Optional[int] = None):
        """通知进度更新"""
        if self.progress_callback:
            self.progress_callback({
                "job_id": self.job_id,
                "progress": progress,
                "status": status,
                "message": message,
                "epoch": epoch,
                "total_epochs": total_epochs,
                "timestamp": datetime.now().isoformat()
            })

    def connect(self) -> bool:
        """建立 SSH 连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.server_ip,
                port=self.ssh_port,
                username=self.username,
                password=self.password,
                timeout=30
            )
            self._notify_progress(5, "preparing", f"已连接到服务器 {self.server_ip}")
            return True
        except Exception as e:
            self._notify_progress(0, "failed", f"连接失败: {str(e)}")
            return False

    def upload_script(self) -> bool:
        """上传训练脚本到远程服务器"""
        try:
            sftp = self.client.open_sftp()
            local_script = os.path.join(os.path.dirname(__file__), 'run_ms_swift_training.sh')
            remote_script = '/tmp/run_ms_swift_training.sh'

            if not os.path.exists(local_script):
                raise FileNotFoundError(f"本地脚本不存在: {local_script}")

            sftp.put(local_script, remote_script)
            sftp.close()

            self.client.exec_command(f'chmod +x {remote_script}')
            self._notify_progress(10, "preparing", "训练脚本上传成功")
            return True
        except Exception as e:
            self._notify_progress(0, "failed", f"脚本上传失败: {str(e)}")
            return False

    def prepare_log_dir(self) -> bool:
        """准备日志目录"""
        try:
            self.log_file = f"{self.log_dir}/{self.job_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.log"
            mkdir_cmd = f'mkdir -p {self.log_dir}'
            self.client.exec_command(mkdir_cmd)
            self._notify_progress(15, "preparing", "日志目录准备完毕")
            return True
        except Exception as e:
            self._notify_progress(0, "failed", f"日志目录准备失败: {str(e)}")
            return False

    def start_training(self, swift_args: str) -> bool:
        """启动训练任务（异步后台执行）"""
        try:
            remote_script = '/tmp/run_ms_swift_training.sh'
            command = f'{remote_script} {self.job_id} {self.env_name} {swift_args}'

            nohup_cmd = f'nohup {command} > {self.log_file} 2>&1 &'
            self.client.exec_command(nohup_cmd)

            self._notify_progress(20, "running", "训练任务已启动")
            self.is_running = True
            return True
        except Exception as e:
            self._notify_progress(0, "failed", f"启动训练失败: {str(e)}")
            return False

    def monitor_training(self, poll_interval: int = 30, max_wait_time: int = 86400) -> Dict[str, Any]:
        """
        监控训练进度
        通过轮询日志文件来更新进度
        """
        if not self.log_file:
            return {"status": "failed", "message": "日志文件未设置"}

        start_time = time.time()
        last_position = 0

        while self.is_running and (time.time() - start_time) < max_wait_time:
            try:
                sftp = self.client.open_sftp()
                with sftp.open(self.log_file) as f:
                    f.seek(last_position)
                    new_lines = f.read().decode('utf-8', errors='ignore').splitlines()
                    last_position = f.tell()
                sftp.close()

                for line in new_lines:
                    self._parse_and_notify(line)

                if self._check_training_complete():
                    self.is_running = False
                    self._notify_progress(100, "completed", "训练任务完成")
                    return {"status": "completed", "log_file": self.log_file}

                if self._check_training_failed():
                    self.is_running = False
                    self._notify_progress(0, "failed", "训练任务失败")
                    return {"status": "failed", "log_file": self.log_file}

            except Exception as e:
                print(f"监控进度失败: {e}")

            time.sleep(poll_interval)

        if (time.time() - start_time) >= max_wait_time:
            self._notify_progress(0, "failed", "训练超时")
            return {"status": "timeout", "message": "训练超时"}

        return {"status": "running", "log_file": self.log_file}

    def _parse_and_notify(self, line: str):
        """解析日志行并通知进度"""
        import re

        epoch_match = re.search(r"epoch[:\s]+(\d+)/(\d+)", line, re.IGNORECASE)
        if epoch_match:
            current = int(epoch_match.group(1))
            total = int(epoch_match.group(2))
            progress = int(current * 100 / total)
            self._notify_progress(progress, "running", f"训练中: Epoch {current}/{total}", current, total)
            return

        step_match = re.search(r"step[:\s]+(\d+)/(\d+)", line, re.IGNORECASE)
        if step_match:
            current = int(step_match.group(1))
            total = int(step_match.group(2))
            progress = int(current * 100 / total)
            self._notify_progress(progress, "running", f"训练中: Step {current}/{total}")
            return

        loss_match = re.search(r"loss[:\s=]+([0-9.]+)", line, re.IGNORECASE)
        if loss_match:
            loss = float(loss_match.group(1))

    def _check_training_complete(self) -> bool:
        """检查训练是否完成"""
        if not self.log_file:
            return False
        try:
            sftp = self.client.open_sftp()
            with sftp.open(self.log_file) as f:
                content = f.read().decode('utf-8', errors='ignore')
            sftp.close()
            return "训练任务成功完成" in content or "Training completed" in content
        except Exception:
            return False

    def _check_training_failed(self) -> bool:
        """检查训练是否失败"""
        if not self.log_file:
            return False
        try:
            sftp = self.client.open_sftp()
            with sftp.open(self.log_file) as f:
                content = f.read().decode('utf-8', errors='ignore')
            sftp.close()
            return "ERROR" in content or "训练任务失败" in content
        except Exception:
            return False

    def cancel_training(self) -> bool:
        """取消训练任务"""
        try:
            self.is_running = False
            kill_cmd = f"pkill -f 'run_ms_swift_training.sh.*{self.job_id}'"
            self.client.exec_command(kill_cmd)
            self._notify_progress(0, "cancelled", "训练任务已取消")
            return True
        except Exception as e:
            print(f"取消训练失败: {e}")
            return False

    def disconnect(self):
        """断开 SSH 连接"""
        if self.client:
            self.client.close()
            self.client = None

    def deploy(self, swift_args: str) -> Dict[str, Any]:
        """
        执行完整的部署流程（同步版本）
        """
        if not self.connect():
            return {"status": "failed", "message": "连接服务器失败"}

        if not self.upload_script():
            self.disconnect()
            return {"status": "failed", "message": "上传脚本失败"}

        if not self.prepare_log_dir():
            self.disconnect()
            return {"status": "failed", "message": "准备日志目录失败"}

        if not self.start_training(swift_args):
            self.disconnect()
            return {"status": "failed", "message": "启动训练失败"}

        result = self.monitor_training()

        self.disconnect()
        return result

    def deploy_async(self, swift_args: str) -> threading.Thread:
        """
        执行部署流程（异步版本，返回线程）
        """
        thread = threading.Thread(target=self._deploy_thread, args=(swift_args,))
        thread.daemon = True
        thread.start()
        return thread

    def _deploy_thread(self, swift_args: str):
        """异步部署线程"""
        try:
            self.deploy(swift_args)
        except Exception as e:
            self._notify_progress(0, "failed", f"部署异常: {str(e)}")
        finally:
            self.disconnect()


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
    连接到 GPU 服务器，部署训练脚本，并执行微调任务（同步版本）
    """
    deployer = FineTuningDeployer(
        server_ip=server_ip,
        ssh_port=ssh_port,
        username=username,
        password=password,
        job_id=job_id,
        env_name=env_name
    )

    result = deployer.deploy(swift_args)
    return result


async def deploy_and_run_training_async(
    server_ip: str,
    ssh_port: int,
    username: str,
    password: str,
    job_id: str,
    env_name: str,
    swift_args: str,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    异步部署训练任务
    """
    loop = asyncio.get_event_loop()
    deployer = FineTuningDeployer(
        server_ip=server_ip,
        ssh_port=ssh_port,
        username=username,
        password=password,
        job_id=job_id,
        env_name=env_name
    )

    if progress_callback:
        deployer.set_progress_callback(progress_callback)

    result = await loop.run_in_executor(None, deployer.deploy, swift_args)
    return result


if __name__ == "__main__":
    JOB_ID = "job_20231001_001"
    ENV_NAME = "msswift"

    SWIFT_ARGS = (
        "--model_type qwen1half-7b-chat "
        "--sft_type lora "
        "--dataset alpaca-zh "
        "--lora_rank 16 "
        "--learning_rate 1e-4 "
        "--num_train_epochs 3 "
        "--batch_size 16 "
        "--fp16 true"
    )

    def progress_handler(progress_info):
        print(f"[进度] {progress_info['progress']}% - {progress_info['message']}")

    result = deploy_and_run_training(
        server_ip="192.168.1.100",
        ssh_port=22,
        username="root",
        password="your_password",
        job_id=JOB_ID,
        env_name=ENV_NAME,
        swift_args=SWIFT_ARGS
    )

    print(f"部署结果: {result}")