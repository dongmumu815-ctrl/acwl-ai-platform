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
from sqlalchemy import select, update

from app.models.server import Server, GPUResource, ServerMetrics, ServerStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class ServerService:
    """
    服务器服务类
    负责处理服务器管理的完整功能
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
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
            
            # 测试SSH连接
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                # 根据认证方式连接
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
                
                # 执行简单命令测试
                stdin, stdout, stderr = ssh_client.exec_command('echo "connection_test"')
                output = stdout.read().decode().strip()
                
                if output == "connection_test":
                    # 更新服务器状态为在线
                    await self.db.execute(
                        update(Server)
                        .where(Server.id == server_id)
                        .values(status=ServerStatus.online)
                    )
                    await self.db.commit()
                    
                    return {
                        "success": True,
                        "message": "SSH连接测试成功",
                        "server_name": server.name,
                        "ip_address": server.ip_address
                    }
                else:
                    raise Exception("命令执行失败")
                    
            finally:
                ssh_client.close()
                
        except Exception as e:
            logger.error(f"SSH连接测试失败: {str(e)}")
            
            # 更新服务器状态为离线
            await self.db.execute(
                update(Server)
                .where(Server.id == server_id)
                .values(status=ServerStatus.offline)
            )
            await self.db.commit()
            
            return {
                "success": False,
                "message": f"SSH连接测试失败: {str(e)}",
                "server_name": server.name if server else "未知",
                "ip_address": server.ip_address if server else "未知"
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
            
            # 通过SSH收集远程服务器指标
            metrics = await self._collect_remote_metrics(server)
            
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
    
    async def _collect_remote_metrics(self, server: Server) -> Dict[str, Any]:
        """
        通过SSH收集远程服务器指标
        
        Args:
            server: 服务器对象
            
        Returns:
            指标数据字典
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # 连接到服务器
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
            
            metrics = {}
            
            # 收集CPU使用率
            stdin, stdout, stderr = ssh_client.exec_command(
                "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | awk -F'%' '{print $1}'"
            )
            cpu_output = stdout.read().decode().strip()
            if cpu_output:
                metrics["cpu_usage"] = float(cpu_output)
            
            # 收集内存使用率
            stdin, stdout, stderr = ssh_client.exec_command(
                "free | grep Mem | awk '{printf \"%.2f\", $3/$2 * 100.0}'"
            )
            memory_output = stdout.read().decode().strip()
            if memory_output:
                metrics["memory_usage"] = float(memory_output)
            
            # 收集磁盘使用率
            stdin, stdout, stderr = ssh_client.exec_command(
                "df -h / | awk 'NR==2{print $5}' | sed 's/%//'"
            )
            disk_output = stdout.read().decode().strip()
            if disk_output:
                metrics["disk_usage"] = float(disk_output)
            
            # 收集网络流量（简化版本）
            stdin, stdout, stderr = ssh_client.exec_command(
                "cat /proc/net/dev | grep eth0 | awk '{print $2, $10}'"
            )
            network_output = stdout.read().decode().strip()
            if network_output:
                parts = network_output.split()
                if len(parts) >= 2:
                    metrics["network_in"] = float(parts[0]) / 1024 / 1024  # 转换为MB
                    metrics["network_out"] = float(parts[1]) / 1024 / 1024  # 转换为MB
            
            # 收集GPU信息（如果有nvidia-smi）
            stdin, stdout, stderr = ssh_client.exec_command(
                "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"
            )
            gpu_output = stdout.read().decode().strip()
            if gpu_output and not stderr.read():
                gpu_metrics = []
                for line in gpu_output.split('\n'):
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 3:
                            gpu_metrics.append({
                                "utilization": float(parts[0]),
                                "memory_used": float(parts[1]),
                                "memory_total": float(parts[2])
                            })
                metrics["gpu_metrics"] = gpu_metrics
            
            return metrics
            
        finally:
            ssh_client.close()
    
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
                "created_at": gpu.created_at.isoformat() if gpu.created_at else None
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"添加GPU资源失败: {str(e)}")
            raise
    
    async def get_server_gpus(self, server_id: int) -> List[Dict[str, Any]]:
        """
        获取服务器GPU资源列表
        
        Args:
            server_id: 服务器ID
            
        Returns:
            GPU资源列表
        """
        try:
            result = await self.db.execute(
                select(GPUResource)
                .where(GPUResource.server_id == server_id)
                .order_by(GPUResource.device_id)
            )
            gpus = result.scalars().all()
            
            return [
                {
                    "id": gpu.id,
                    "server_id": gpu.server_id,
                    "gpu_name": gpu.gpu_name,
                    "gpu_type": gpu.gpu_type,
                    "memory_size": gpu.memory_size,
                    "cuda_version": gpu.cuda_version,
                    "device_id": gpu.device_id,
                    "is_available": gpu.is_available,
                    "created_at": gpu.created_at.isoformat() if gpu.created_at else None
                }
                for gpu in gpus
            ]
            
        except Exception as e:
            logger.error(f"获取服务器GPU资源失败: {str(e)}")
            raise
    
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