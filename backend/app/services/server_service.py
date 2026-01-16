#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器服务类
处理服务器管理的核心逻辑，包括连接测试、监控数据收集等
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import paramiko
import psutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.models.server import Server, GPUResource, ServerMetrics, ServerStatus
from app.core.config import settings
from app.core.exceptions import GPUError, NotFoundError, ACWLException

logger = logging.getLogger(__name__)


class ServerService:
    """
    服务器服务类
    负责处理服务器管理的完整功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _run_sync(self, func, *args, **kwargs):
        """在线程池中运行同步函数"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    @staticmethod
    def _ssh_task(server_info: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """
        执行 SSH 任务的同步方法
        
        Args:
            server_info: 服务器连接信息字典
            task_type: 任务类型 'test_and_info' | 'scan_gpu' | 'collect_metrics' | 'restart'
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        result = {"success": False, "message": "", "data": {}}
        
        try:
            # 建立连接
            connected = False
            last_error = None
            
            # 1. 优先尝试 Key 认证
            if server_info.get("ssh_key_path"):
                try:
                    ssh_client.connect(
                        hostname=server_info["ip_address"],
                        port=server_info["ssh_port"],
                        username=server_info["ssh_username"],
                        key_filename=server_info["ssh_key_path"],
                        timeout=15
                    )
                    connected = True
                    logger.info(f"SSH连接成功 (Key认证): {server_info['ip_address']}")
                except Exception as e:
                    logger.warning(f"SSH Key认证失败: {str(e)}，尝试密码认证")
                    last_error = e
            
            # 2. 如果未连接且提供了密码，尝试密码认证
            if not connected and server_info.get("ssh_password"):
                try:
                    ssh_client.connect(
                        hostname=server_info["ip_address"],
                        port=server_info["ssh_port"],
                        username=server_info["ssh_username"],
                        password=server_info["ssh_password"],
                        timeout=15
                    )
                    connected = True
                    logger.info(f"SSH连接成功 (密码认证): {server_info['ip_address']}")
                except Exception as e:
                    logger.error(f"SSH 密码认证失败: {str(e)}")
                    last_error = e
            
            if not connected:
                raise last_error or Exception("无法建立SSH连接，请检查认证信息")
            
            if task_type == 'test_and_info':
                # 1. 测试连接
                stdin, stdout, stderr = ssh_client.exec_command('echo "connection_test"')
                output = stdout.read().decode().strip()
                if output != "connection_test":
                    raise Exception("连接测试响应不正确")
                
                result["success"] = True
                result["message"] = "SSH连接测试成功"
                
                # 2. 获取硬件信息
                info = {}
                # CPU
                try:
                    stdin, stdout, stderr = ssh_client.exec_command("nproc")
                    cpu = stdout.read().decode().strip()
                    if cpu.isdigit(): info["total_cpu_cores"] = int(cpu)
                except: pass
                
                # Memory
                try:
                    stdin, stdout, stderr = ssh_client.exec_command("free -m | awk '/^Mem:/{print $2}'")
                    mem = stdout.read().decode().strip()
                    if mem.isdigit():
                        mem_gb = round(int(mem) / 1024, 1)
                        info["total_memory"] = f"{int(mem_gb)}GB" if mem_gb.is_integer() else f"{mem_gb}GB"
                except: pass
                
                # OS
                try:
                    stdin, stdout, stderr = ssh_client.exec_command("cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'")
                    os_info = stdout.read().decode().strip()
                    if not os_info:
                        stdin, stdout, stderr = ssh_client.exec_command("uname -sr")
                        os_info = stdout.read().decode().strip()
                    if os_info: info["os_info"] = os_info
                except: pass
                
                result["data"]["sys_info"] = info
                
                # 3. 扫描 GPU (复用连接)
                try:
                    gpu_list = ServerService._scan_gpus_internal(ssh_client)
                    result["data"]["gpu_list"] = gpu_list
                except Exception as e:
                    logger.warning(f"SSH测试连接时扫描GPU失败: {e}")
                    result["data"]["gpu_list"] = []

            elif task_type == 'scan_gpu':
                gpu_list = ServerService._scan_gpus_internal(ssh_client)
                result["success"] = True
                result["data"]["gpu_list"] = gpu_list
                
            elif task_type == 'restart':
                ssh_client.exec_command('nohup sudo reboot > /dev/null 2>&1 &')
                result["success"] = True
                result["message"] = "重启命令已发送"

            elif task_type == 'change_password':
                new_password = server_info.get("new_password")
                username = server_info["ssh_username"]
                current_password = server_info.get("ssh_password")
                
                if not new_password:
                     raise Exception("未提供新密码")
                
                # 转义单引号
                safe_password = new_password.replace("'", "'\\''")
                
                if username == 'root':
                    cmd = f"echo '{username}:{safe_password}' | chpasswd"
                else:
                    if not current_password:
                         # 尝试无密码 sudo
                         cmd = f"echo '{username}:{safe_password}' | sudo -n chpasswd"
                    else:
                         safe_current_password = current_password.replace("'", "'\\''")
                         # sudo -S 从 stdin 读取密码
                         # 使用 sh -c 来执行管道命令
                         cmd = f"echo '{safe_current_password}' | sudo -S sh -c \"echo '{username}:{safe_password}' | chpasswd\""
                
                stdin, stdout, stderr = ssh_client.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                err = stderr.read().decode().strip()
                
                if exit_status != 0:
                    raise Exception(f"修改密码失败 (Exit {exit_status}): {err}")
                
                result["success"] = True
                result["message"] = "密码修改成功"
                
        except Exception as e:
            result["success"] = False
            result["message"] = str(e)
            # 对于 GPU 扫描错误，可能需要特殊处理，但这里统一返回失败
        finally:
            ssh_client.close()
            
        return result

    @staticmethod
    def _scan_gpus_internal(ssh_client: paramiko.SSHClient) -> List[Dict[str, Any]]:
        """内部使用的 GPU 扫描逻辑，假设 ssh_client 已连接"""
        # 检查 nvidia-smi
        stdin, stdout, stderr = ssh_client.exec_command("command -v nvidia-smi || which nvidia-smi || true")
        if not stdout.read().decode().strip():
            # 没有 nvidia-smi，返回空列表而不是报错，或者视业务需求而定
            # 这里为了不中断流程，返回空
            return []

        # 查询信息
        stdin, stdout, stderr = ssh_client.exec_command(
            "nvidia-smi --query-gpu=name,memory.total,uuid --format=csv,noheader,nounits"
        )
        query_output = stdout.read().decode().strip()
        
        # 获取 CUDA 版本
        stdin, stdout, stderr = ssh_client.exec_command(
            "nvidia-smi | grep -oP 'CUDA Version:\s*\K[0-9.]+'"
        )
        cuda_version = stdout.read().decode().strip() or None
        
        gpu_list = []
        if query_output:
            for line in query_output.splitlines():
                parts = [p.strip() for p in line.split(',') if p.strip()]
                if len(parts) >= 3:
                    name, mem_total, uuid = parts[0], parts[1], parts[2]
                    gpu_list.append({
                        "gpu_name": name,
                        "gpu_type": name,
                        "memory_size": f"{mem_total} MiB",
                        "cuda_version": cuda_version,
                        "device_id": uuid,
                        "is_available": True
                    })
        return gpu_list

    async def test_ssh_connection(self, server_id: int) -> Dict[str, Any]:
        """
        测试服务器SSH连接
        
        Args:
            server_id: 服务器ID
            
        Returns:
            连接测试结果
        """
        try:
            # 获取服务器信息
            result = await self.db.execute(
                select(Server).where(Server.id == server_id)
            )
            server = result.scalar_one_or_none()
            
            if not server:
                raise ValueError(f"服务器 {server_id} 不存在")
            
            # 准备连接信息
            server_info = {
                "ip_address": server.ip_address,
                "ssh_port": server.ssh_port,
                "ssh_username": server.ssh_username,
                "ssh_password": server.ssh_password,
                "ssh_key_path": server.ssh_key_path
            }
            
            # 使用 _ssh_task 执行连接测试和信息收集
            task_result = await self._run_sync(self._ssh_task, server_info, 'test_and_info')
            
            if task_result["success"]:
                # 提取系统信息
                sys_info = task_result["data"].get("sys_info", {})
                gpu_list = task_result["data"].get("gpu_list", [])
                
                # 更新服务器信息
                update_values = {
                    "status": ServerStatus.online,
                    "updated_at": datetime.now()
                }
                
                if "os_info" in sys_info:
                    update_values["os_info"] = sys_info["os_info"]
                if "total_cpu_cores" in sys_info:
                    update_values["total_cpu_cores"] = sys_info["total_cpu_cores"]
                if "total_memory" in sys_info:
                    update_values["total_memory"] = sys_info["total_memory"]
                
                # 更新服务器记录
                await self.db.execute(
                    update(Server)
                    .where(Server.id == server_id)
                    .values(**update_values)
                )
                
                # 更新 GPU 信息
                # 先删除旧的
                await self.db.execute(
                    delete(GPUResource).where(GPUResource.server_id == server_id)
                )
                
                # 添加新的
                for gpu_data in gpu_list:
                    gpu_data["server_id"] = server_id
                    await self.add_gpu_resource(gpu_data)
                
                await self.db.commit()
                
                return {
                    "success": True,
                    "message": "SSH连接测试成功",
                    "server_name": server.name,
                    "ip_address": server.ip_address,
                    "data": {
                        **sys_info,
                        "gpu_count": len(gpu_list),
                        "status": "online"
                    }
                }
            else:
                raise Exception(task_result["message"])

        except Exception as e:
            logger.error(f"SSH连接测试失败: {str(e)}")
            
            # 更新服务器状态为离线
            try:
                await self.db.execute(
                    update(Server)
                    .where(Server.id == server_id)
                    .values(status=ServerStatus.offline)
                )
                await self.db.commit()
            except:
                pass
            
            return {
                "success": False,
                "message": f"SSH连接测试失败: {str(e)}",
                "server_name": server.name if 'server' in locals() and server else "未知",
                "ip_address": server.ip_address if 'server' in locals() and server else "未知"
            }
    
    async def collect_server_metrics(self, server_id: int) -> Dict[str, Any]:
        """
        收集服务器监控指标
        
        Args:
            server_id: 服务器ID
            
        Returns:
            监控指标数据
        """
        try:
            # 获取服务器信息
            result = await self.db.execute(
                select(Server).where(Server.id == server_id)
            )
            server = result.scalar_one_or_none()
            
            if not server:
                raise ValueError(f"服务器 {server_id} 不存在")
            
            # 准备连接信息
            server_info = {
                "ip_address": server.ip_address,
                "ssh_port": server.ssh_port,
                "ssh_username": server.ssh_username,
                "ssh_password": server.ssh_password,
                "ssh_key_path": server.ssh_key_path
            }
            
            # 通过SSH收集远程服务器指标
            task_result = await self._run_sync(self._ssh_task, server_info, 'collect_metrics')
            
            if not task_result["success"]:
                raise Exception(task_result["message"])
                
            metrics = task_result["data"].get("metrics", {})
            
            # 保存监控数据到数据库
            server_metrics = ServerMetrics(
                server_id=server_id,
                cpu_usage=metrics.get("cpu_usage"),
                memory_usage=metrics.get("memory_usage"),
                disk_usage=metrics.get("disk_usage"),
                network_in=metrics.get("network_in"),
                network_out=metrics.get("network_out"),
                gpu_metrics=metrics.get("gpu_metrics"),
                timestamp=datetime.now()
            )
            
            self.db.add(server_metrics)
            await self.db.commit()
            
            return {
                "success": True,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"收集服务器指标失败: {str(e)}")
            return {
                "success": False,
                "message": f"收集服务器指标失败: {str(e)}"
            }
    
    # _collect_remote_metrics 已废弃，功能合并到 _ssh_task 中
    
    async def get_server_status(self, server_id: int) -> Dict[str, Any]:
        """
        获取服务器状态信息
        
        Args:
            server_id: 服务器ID
            
        Returns:
            服务器状态信息
        """
        try:
            # 获取服务器基本信息
            result = await self.db.execute(
                select(Server).where(Server.id == server_id)
            )
            server = result.scalar_one_or_none()
            
            if not server:
                raise ValueError(f"服务器 {server_id} 不存在")
            
            # 获取最新的监控指标
            metrics_result = await self.db.execute(
                select(ServerMetrics)
                .where(ServerMetrics.server_id == server_id)
                .order_by(ServerMetrics.created_at.desc())
                .limit(1)
            )
            latest_metrics = metrics_result.scalar_one_or_none()
            
            # 获取GPU资源信息
            gpu_result = await self.db.execute(
                select(GPUResource).where(GPUResource.server_id == server_id)
            )
            gpu_resources = gpu_result.scalars().all()
            
            return {
                "server_id": server.id,
                "name": server.name,
                "ip_address": server.ip_address,
                "status": server.status,
                "server_type": server.server_type,
                "os_info": server.os_info,
                "total_memory": server.total_memory,
                "total_cpu_cores": server.total_cpu_cores,
                "gpu_count": len(gpu_resources),
                "available_gpus": len([gpu for gpu in gpu_resources if gpu.is_available]),
                "latest_metrics": {
                    "cpu_usage": latest_metrics.cpu_usage if latest_metrics else None,
                    "memory_usage": latest_metrics.memory_usage if latest_metrics else None,
                    "disk_usage": latest_metrics.disk_usage if latest_metrics else None,
                    "timestamp": latest_metrics.timestamp.isoformat() if latest_metrics else None
                } if latest_metrics else None
            }
            
        except Exception as e:
            logger.error(f"获取服务器状态失败: {str(e)}")
            raise
    
    async def update_server_status(self, server_id: int, status: ServerStatus) -> bool:
        """
        更新服务器状态
        
        Args:
            server_id: 服务器ID
            status: 新状态
            
        Returns:
            更新是否成功
        """
        try:
            await self.db.execute(
                update(Server)
                .where(Server.id == server_id)
                .values(status=status)
            )
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新服务器状态失败: {str(e)}")
            return False
            
    async def create_server(self, server_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        创建新服务器
        
        Args:
            server_data: 服务器数据
            user_id: 创建用户ID（仅用于记录，不存储在模型中）
            
        Returns:
            创建的服务器信息
        """
        try:
            # 创建服务器对象
            server = Server(
                name=server_data.get("name"),
                ip_address=server_data.get("ip_address"),
                ssh_port=server_data.get("ssh_port"),
                ssh_username=server_data.get("ssh_username"),
                ssh_password=server_data.get("ssh_password"),
                ssh_key_path=server_data.get("ssh_key_path"),
                server_type=server_data.get("server_type"),
                os_info=server_data.get("os_info"),
                status=server_data.get("status", ServerStatus.offline),
                total_memory=server_data.get("total_memory"),
                total_storage=server_data.get("total_storage"),
                total_cpu_cores=server_data.get("total_cpu_cores")
            )
            
            self.db.add(server)
            await self.db.commit()
            await self.db.refresh(server)
            
            return {
                "id": server.id,
                "name": server.name,
                "ip_address": server.ip_address,
                "server_type": server.server_type,
                "status": server.status,
                "created_at": server.created_at.isoformat() if server.created_at else None
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建服务器失败: {str(e)}")
            raise
    
    async def get_servers(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        获取服务器列表
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数限制
            
        Returns:
            服务器列表
        """
        try:
            # 获取总记录数
            count_result = await self.db.execute(select(Server))
            total = len(count_result.scalars().all())
            
            # 获取分页数据
            result = await self.db.execute(
                select(Server)
                .offset(skip)
                .limit(limit)
                .order_by(Server.created_at.desc())
            )
            servers = result.scalars().all()
            
            items = []
            for server in servers:
                # 获取GPU数量
                gpu_result = await self.db.execute(
                    select(GPUResource).where(GPUResource.server_id == server.id)
                )
                gpu_count = len(gpu_result.scalars().all())
                
                items.append({
                    "id": server.id,
                    "name": server.name,
                    "ip_address": server.ip_address,
                    "server_type": server.server_type,
                    "status": server.status,
                    "os_info": server.os_info,
                    "total_cpu_cores": server.total_cpu_cores,
                    "total_memory": server.total_memory,
                    "gpu_count": gpu_count,
                    "created_at": server.created_at.isoformat() if server.created_at else None
                })
            
            return {
                "items": items,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"获取服务器列表失败: {str(e)}")
            raise
    
    async def update_server(self, server_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新服务器信息
        
        Args:
            server_id: 服务器ID
            update_data: 更新数据
            
        Returns:
            更新后的服务器信息
        """
        try:
            # 获取服务器
            result = await self.db.execute(
                select(Server).where(Server.id == server_id)
            )
            server = result.scalar_one_or_none()
            
            if not server:
                raise ValueError(f"服务器 {server_id} 不存在")
            
            # 更新服务器信息
            await self.db.execute(
                update(Server)
                .where(Server.id == server_id)
                .values(**update_data)
            )
            await self.db.commit()
            
            # 获取更新后的服务器信息
            result = await self.db.execute(
                select(Server).where(Server.id == server_id)
            )
            updated_server = result.scalar_one_or_none()
            
            return {
                "id": updated_server.id,
                "name": updated_server.name,
                "ip_address": updated_server.ip_address,
                "server_type": updated_server.server_type,
                "status": updated_server.status,
                "os_info": updated_server.os_info,
                "updated_at": updated_server.updated_at.isoformat() if updated_server.updated_at else None
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新服务器失败: {str(e)}")
            raise
    
    async def add_gpu_resource(self, gpu_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加GPU资源
        
        Args:
            gpu_data: GPU资源数据
            
        Returns:
            创建的GPU资源信息
        """
        try:
            # 创建GPU资源对象
            gpu = GPUResource(
                server_id=gpu_data.get("server_id"),
                gpu_name=gpu_data.get("gpu_name"),
                gpu_type=gpu_data.get("gpu_type"),
                memory_size=gpu_data.get("memory_size"),
                cuda_version=gpu_data.get("cuda_version"),
                device_id=gpu_data.get("device_id"),
                is_available=gpu_data.get("is_available", True)
            )
            
            self.db.add(gpu)
            await self.db.commit()
            await self.db.refresh(gpu)
            
            return {
                "id": gpu.id,
                "server_id": gpu.server_id,
                "gpu_name": gpu.gpu_name,
                "gpu_type": gpu.gpu_type,
                "memory_size": gpu.memory_size,
                "cuda_version": gpu.cuda_version,
                "device_id": gpu.device_id,
                "is_available": gpu.is_available,
                "created_at": gpu.created_at.isoformat() if gpu.created_at else None,
                "updated_at": gpu.updated_at.isoformat() if gpu.updated_at else None,
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"添加GPU资源失败: {str(e)}")
            raise
    
    async def scan_server_gpus(self, server_id: int, ssh_client: Optional[paramiko.SSHClient] = None) -> List[Dict[str, Any]]:
        """
        通过SSH扫描服务器上的GPU，并将信息写入数据库
        
        Args:
            server_id: 服务器ID
            ssh_client: (已弃用，保留兼容性) 可选的已连接SSH客户端
        
        Returns:
            持久化后的GPU资源列表
        """
        try:
            # 获取服务器信息
            result = await self.db.execute(select(Server).where(Server.id == server_id))
            server = result.scalar_one_or_none()
            if not server:
                raise NotFoundError("服务器不存在", detail={"server_id": server_id})
            
            # 准备连接信息
            server_info = {
                "ip_address": server.ip_address,
                "ssh_port": server.ssh_port,
                "ssh_username": server.ssh_username,
                "ssh_password": server.ssh_password,
                "ssh_key_path": server.ssh_key_path
            }
            
            # 在线程池中执行
            task_result = await self._run_sync(self._ssh_task, server_info, 'scan_gpu')
            
            if not task_result["success"]:
                 raise GPUError(task_result["message"], detail={"server_id": server_id})

            gpu_list = task_result["data"].get("gpu_list", [])
            
            # 持久化
            gpu_result = await self.db.execute(select(GPUResource).where(GPUResource.server_id == server_id))
            for gpu in gpu_result.scalars().all():
                await self.db.delete(gpu)
            await self.db.commit()
            
            scanned: List[Dict[str, Any]] = []
            for gpu_data in gpu_list:
                gpu_data["server_id"] = server_id
                created = await self.add_gpu_resource(gpu_data)
                scanned.append(created)
            
            return scanned

        except ACWLException:
            raise
        except Exception as e:
            logger.error(f"扫描GPU失败: {str(e)}", exc_info=True)
            raise GPUError("扫描GPU失败", detail=str(e))
    
    async def get_server(self, server_id: int) -> Dict[str, Any]:
        """
        获取服务器详情
        
        Args:
            server_id: 服务器ID
            
        Returns:
            服务器详情
        """
        try:
            # 获取服务器基本信息
            result = await self.db.execute(
                select(Server).where(Server.id == server_id)
            )
            server = result.scalar_one_or_none()
            
            if not server:
                raise ValueError(f"服务器 {server_id} 不存在")
            
            # 获取GPU资源
            gpu_result = await self.db.execute(
                select(GPUResource).where(GPUResource.server_id == server_id)
            )
            gpus = gpu_result.scalars().all()
            
            gpu_resources = [
                {
                    "id": gpu.id,
                    "gpu_name": gpu.gpu_name,
                    "gpu_type": gpu.gpu_type,
                    "memory_size": gpu.memory_size,
                    "cuda_version": gpu.cuda_version,
                    "device_id": gpu.device_id,
                    "is_available": gpu.is_available
                }
                for gpu in gpus
            ]
            
            return {
                "id": server.id,
                "name": server.name,
                "ip_address": server.ip_address,
                "ssh_port": server.ssh_port,
                "ssh_username": server.ssh_username,
                "server_type": server.server_type,
                "os_info": server.os_info,
                "status": server.status,
                "total_memory": server.total_memory,
                "total_storage": server.total_storage,
                "total_cpu_cores": server.total_cpu_cores,
                "gpu_resources": gpu_resources,
                "created_at": server.created_at.isoformat() if server.created_at else None,
                "updated_at": server.updated_at.isoformat() if server.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"获取服务器详情失败: {str(e)}")
            raise
    
    async def delete_server(self, server_id: int) -> bool:
        """
        删除服务器
        
        Args:
            server_id: 服务器ID
            
        Returns:
            删除是否成功
        """
        try:
            # 获取服务器
            result = await self.db.execute(
                select(Server).where(Server.id == server_id)
            )
            server = result.scalar_one_or_none()
            
            if not server:
                raise ValueError(f"服务器 {server_id} 不存在")
            
            # 删除相关的GPU资源
            gpu_result = await self.db.execute(
                select(GPUResource).where(GPUResource.server_id == server_id)
            )
            gpus = gpu_result.scalars().all()
            
            for gpu in gpus:
                await self.db.delete(gpu)
            
            # 删除服务器
            await self.db.delete(server)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除服务器失败: {str(e)}")
            raise

    async def batch_test_ssh_connection(self, server_ids: List[int]) -> List[Dict[str, Any]]:
        """
        批量测试服务器SSH连接
        
        Args:
            server_ids: 服务器ID列表
            
        Returns:
            测试结果列表
        """
        results = []
        for server_id in server_ids:
            try:
                result = await self.test_ssh_connection(server_id)
                results.append(result)
            except Exception as e:
                results.append({
                    "server_id": server_id,
                    "success": False,
                    "message": f"测试失败: {str(e)}"
                })
        return results

    async def batch_update_password(self, server_ids: List[int], password: str) -> List[Dict[str, Any]]:
        """
        批量更新服务器SSH密码
        
        Args:
            server_ids: 服务器ID列表
            password: 新密码
            
        Returns:
            更新结果列表
        """
        results = []
        try:
            # 批量获取服务器
            query = select(Server).where(Server.id.in_(server_ids))
            result = await self.db.execute(query)
            servers = result.scalars().all()
            
            for server in servers:
                try:
                    # DEBUG: 检查密码一致性
                    if server.ssh_password == password:
                         logger.warning(f"服务器 {server.id} ({server.ip_address}) 的数据库密码与新密码相同，可能已经更新过")
                    else:
                         logger.info(f"服务器 {server.id} ({server.ip_address}) 准备更新密码。数据库中密码长度: {len(server.ssh_password) if server.ssh_password else 0}, 新密码长度: {len(password)}")

                    # 1. 尝试更新远程服务器密码
                    server_info = {
                        "ip_address": server.ip_address,
                        "ssh_port": server.ssh_port,
                        "ssh_username": server.ssh_username,
                        "ssh_password": server.ssh_password, # 使用旧密码连接
                        "ssh_key_path": server.ssh_key_path,
                        "new_password": password
                    }
                    
                    # 执行远程修改
                    task_result = await self._run_sync(self._ssh_task, server_info, 'change_password')
                    
                    if not task_result["success"]:
                        raise Exception(task_result["message"])
                    
                    # 2. 更新数据库中的密码
                    server.ssh_password = password
                    
                    results.append({
                        "server_id": server.id,
                        "success": True,
                        "message": "密码更新成功"
                    })
                except Exception as e:
                    logger.error(f"服务器 {server.id} 更新密码失败: {str(e)}")
                    results.append({
                        "server_id": server.id,
                        "success": False,
                        "message": f"密码更新失败: {str(e)}"
                    })
            
            await self.db.commit()
            return results
        except Exception as e:
            logger.error(f"批量更新密码失败: {str(e)}")
            raise

    async def restart_server(self, server_id: int) -> Dict[str, Any]:
        """
        重启服务器
        
        Args:
            server_id: 服务器ID
            
        Returns:
            操作结果
        """
        try:
            # 获取服务器信息
            result = await self.db.execute(
                select(Server).where(Server.id == server_id)
            )
            server = result.scalar_one_or_none()
            
            if not server:
                raise ValueError(f"服务器 {server_id} 不存在")
            
            # 连接SSH执行重启命令
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                if server.ssh_key_path:
                    ssh_client.connect(
                        hostname=server.ip_address,
                        port=server.ssh_port,
                        username=server.ssh_username,
                        key_filename=server.ssh_key_path,
                        timeout=10
                    )
                else:
                    ssh_client.connect(
                        hostname=server.ip_address,
                        port=server.ssh_port,
                        username=server.ssh_username,
                        password=server.ssh_password,
                        timeout=10
                    )
                
                # 异步执行重启命令，因为重启会断开连接
                # 使用 nohup 和 & 让命令在后台运行
                ssh_client.exec_command('nohup sudo reboot > /dev/null 2>&1 &')
                
                return {
                    "success": True,
                    "message": "重启命令已发送",
                    "server_id": server_id
                }
                
            finally:
                ssh_client.close()
                
        except Exception as e:
            logger.error(f"重启服务器失败: {str(e)}")
            raise