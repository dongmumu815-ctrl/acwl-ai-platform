#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署服务类
处理模型部署的核心逻辑，包括Docker容器管理、GPU资源分配等
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import paramiko
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.deployment import Deployment, DeploymentGPU, DeploymentStatus
from app.models.server import Server, GPUResource
from app.models.model import Model
from app.core.config import settings

logger = logging.getLogger(__name__)


class DeploymentService:
    """
    部署服务类
    负责处理模型部署的完整生命周期
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_deployment(
        self,
        deployment_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        创建新的部署
        
        Args:
            deployment_data: 部署配置数据
            user_id: 用户ID
            
        Returns:
            部署创建结果
        """
        try:
            # 1. 验证模型存在
            model = await self._validate_model(deployment_data.get("model_id"))
            
            # 2. 验证服务器资源
            server = await self._validate_server(deployment_data.get("server_id"))
            
            # 3. 验证和预留GPU资源
            gpu_configs = await self._validate_and_reserve_gpus(
                deployment_data.get("server_id"),
                deployment_data.get("gpu_ids", [])
            )
            
            # 4. 创建部署记录
            deployment = await self._create_deployment_record(
                deployment_data, model, server, user_id
            )
            
            # 5. 创建GPU关联记录
            await self._create_gpu_associations(deployment.id, gpu_configs)
            
            # 6. 异步启动部署任务
            asyncio.create_task(self._deploy_model_async(deployment.id))
            
            return {
                "deployment_id": deployment.id,
                "status": "deploying",
                "message": "部署任务已启动",
                "server_name": server.name,
                "gpu_count": len(gpu_configs)
            }
            
        except Exception as e:
            logger.error(f"创建部署失败: {str(e)}")
            raise
    
    async def _validate_model(self, model_id: str) -> Model:
        """
        验证模型存在且可用
        """
        if not model_id:
            raise ValueError("模型ID不能为空")
        
        result = await self.db.execute(
            select(Model).where(Model.id == model_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"模型 {model_id} 不存在")
        
        if model.status != "ready":
            raise ValueError(f"模型 {model.name} 状态不可用: {model.status}")
        
        return model
    
    async def _validate_server(self, server_id: int) -> Server:
        """
        验证服务器存在且在线
        """
        if not server_id:
            raise ValueError("服务器ID不能为空")
        
        result = await self.db.execute(
            select(Server).where(Server.id == server_id)
        )
        server = result.scalar_one_or_none()
        
        if not server:
            raise ValueError(f"服务器 {server_id} 不存在")
        
        if server.status != "online":
            raise ValueError(f"服务器 {server.name} 状态不可用: {server.status}")
        
        return server
    
    async def _validate_and_reserve_gpus(
        self, 
        server_id: int, 
        gpu_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        验证GPU资源可用性并预留
        """
        if not gpu_configs:
            raise ValueError("至少需要选择一个GPU资源")
        
        validated_gpus = []
        
        for gpu_config in gpu_configs:
            gpu_id = gpu_config.get("id")
            memory_limit = gpu_config.get("memory_limit")
            
            # 查询GPU资源
            result = await self.db.execute(
                select(GPUResource).where(
                    GPUResource.id == gpu_id,
                    GPUResource.server_id == server_id
                )
            )
            gpu = result.scalar_one_or_none()
            
            if not gpu:
                raise ValueError(f"GPU资源 {gpu_id} 不存在")
            
            if not gpu.is_available:
                raise ValueError(f"GPU {gpu.gpu_name} (设备ID: {gpu.device_id}) 正在被占用")
            
            # 验证显存限制
            max_memory = int(gpu.memory_size.replace('GB', ''))
            if memory_limit > max_memory:
                raise ValueError(
                    f"GPU {gpu.gpu_name} 显存限制 {memory_limit}GB 超过最大值 {max_memory}GB"
                )
            
            validated_gpus.append({
                "gpu_id": gpu_id,
                "memory_limit": memory_limit,
                "gpu": gpu
            })
        
        # 预留GPU资源（设置为不可用）
        for gpu_config in validated_gpus:
            await self.db.execute(
                update(GPUResource)
                .where(GPUResource.id == gpu_config["gpu_id"])
                .values(is_available=False)
            )
        
        await self.db.commit()
        return validated_gpus
    
    async def _create_deployment_record(
        self,
        deployment_data: Dict[str, Any],
        model: Model,
        server: Server,
        user_id: int
    ) -> Deployment:
        """
        创建部署记录
        """
        deployment = Deployment(
            deployment_name=deployment_data["name"],
            model_id=model.id,
            server_id=server.id,
            user_id=user_id,
            deployment_type=deployment_data.get("deployment_type", "docker"),
            status=DeploymentStatus.DEPLOYING,
            config=json.dumps({
                "environment": deployment_data.get("environment", "development"),
                "port": deployment_data.get("port", 8080),
                "max_concurrent_requests": deployment_data.get("max_concurrent_requests", 10),
                "restart_policy": deployment_data.get("restart_policy", "always"),
                "env_vars": deployment_data.get("env_vars", []),
                "health_check": deployment_data.get("health_check", {}),
                "description": deployment_data.get("description", ""),
                "tags": deployment_data.get("tags", [])
            }),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(deployment)
        await self.db.flush()  # 获取ID但不提交
        return deployment
    
    async def _create_gpu_associations(
        self,
        deployment_id: int,
        gpu_configs: List[Dict[str, Any]]
    ):
        """
        创建部署与GPU的关联记录
        """
        for gpu_config in gpu_configs:
            deployment_gpu = DeploymentGPU(
                deployment_id=deployment_id,
                gpu_id=gpu_config["gpu_id"],
                memory_limit=gpu_config["memory_limit"]
            )
            self.db.add(deployment_gpu)
        
        await self.db.commit()
    
    async def _deploy_model_async(self, deployment_id: int):
        """
        异步执行模型部署
        """
        try:
            # 获取部署信息
            result = await self.db.execute(
                select(Deployment)
                .where(Deployment.id == deployment_id)
            )
            deployment = result.scalar_one()
            
            # 获取服务器信息
            result = await self.db.execute(
                select(Server)
                .where(Server.id == deployment.server_id)
            )
            server = result.scalar_one()
            
            # 获取GPU配置
            result = await self.db.execute(
                select(DeploymentGPU, GPUResource)
                .join(GPUResource, DeploymentGPU.gpu_id == GPUResource.id)
                .where(DeploymentGPU.deployment_id == deployment_id)
            )
            gpu_associations = result.all()
            
            # 执行Docker部署
            await self._execute_docker_deployment(
                deployment, server, gpu_associations
            )
            
            # 更新部署状态为运行中
            await self.db.execute(
                update(Deployment)
                .where(Deployment.id == deployment_id)
                .values(
                    status=DeploymentStatus.RUNNING,
                    updated_at=datetime.utcnow(),
                    endpoint_url=f"http://{server.ip_address}:{json.loads(deployment.config)['port']}"
                )
            )
            await self.db.commit()
            
            logger.info(f"部署 {deployment.deployment_name} 启动成功")
            
        except Exception as e:
            logger.error(f"部署 {deployment_id} 失败: {str(e)}")
            
            # 更新部署状态为错误
            await self.db.execute(
                update(Deployment)
                .where(Deployment.id == deployment_id)
                .values(
                    status=DeploymentStatus.ERROR,
                    updated_at=datetime.utcnow()
                )
            )
            
            # 释放GPU资源
            await self._release_gpu_resources(deployment_id)
            await self.db.commit()
    
    async def _execute_docker_deployment(
        self,
        deployment: Deployment,
        server: Server,
        gpu_associations: List[tuple]
    ):
        """
        执行Docker部署
        """
        config = json.loads(deployment.config)
        
        # 构建GPU设备映射
        gpu_devices = []
        for deployment_gpu, gpu_resource in gpu_associations:
            gpu_devices.append(f"/dev/nvidia{gpu_resource.device_id}")
        
        # 构建Docker运行命令
        docker_cmd = self._build_docker_command(
            deployment, config, gpu_devices
        )
        
        # 通过SSH连接到服务器执行命令
        await self._execute_remote_command(server, docker_cmd)
    
    def _build_docker_command(
        self,
        deployment: Deployment,
        config: Dict[str, Any],
        gpu_devices: List[str]
    ) -> str:
        """
        构建Docker运行命令
        """
        container_name = f"acwl-{deployment.deployment_name}-{deployment.id}"
        port = config.get("port", 8080)
        
        # 基础命令
        cmd_parts = [
            "docker run -d",
            f"--name {container_name}",
            f"-p {port}:{port}",
            f"--restart {config.get('restart_policy', 'always')}"
        ]
        
        # GPU设备映射
        if gpu_devices:
            cmd_parts.append("--gpus all")
            for device in gpu_devices:
                cmd_parts.append(f"--device {device}")
        
        # 环境变量
        for env_var in config.get("env_vars", []):
            if env_var.get("key") and env_var.get("value"):
                cmd_parts.append(f"-e {env_var['key']}={env_var['value']}")
        
        # 健康检查
        health_check = config.get("health_check", {})
        if health_check.get("enabled"):
            health_path = health_check.get("path", "/health")
            health_interval = health_check.get("interval", 30)
            health_timeout = health_check.get("timeout", 10)
            cmd_parts.append(
                f"--health-cmd 'curl -f http://localhost:{port}{health_path} || exit 1'"
            )
            cmd_parts.append(f"--health-interval {health_interval}s")
            cmd_parts.append(f"--health-timeout {health_timeout}s")
        
        # 镜像名称（这里需要根据实际情况配置）
        image_name = f"acwl-model:{deployment.model_id}"
        cmd_parts.append(image_name)
        
        return " ".join(cmd_parts)
    
    async def _execute_remote_command(self, server: Server, command: str):
        """
        通过SSH执行远程命令
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # 连接到服务器
            ssh_client.connect(
                hostname=server.ip_address,
                port=server.ssh_port,
                username=server.ssh_username,
                password=server.ssh_password,
                # 这里需要配置SSH密钥或密码认证
                # key_filename=server.ssh_key_path
            )
            
            # 执行命令
            stdin, stdout, stderr = ssh_client.exec_command(command)
            
            # 等待命令执行完成
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode()
                raise Exception(f"Docker命令执行失败: {error_output}")
            
            logger.info(f"Docker容器启动成功: {command}")
            
        finally:
            ssh_client.close()
    
    async def _release_gpu_resources(self, deployment_id: int):
        """
        释放GPU资源
        """
        # 获取部署关联的GPU
        result = await self.db.execute(
            select(DeploymentGPU.gpu_id)
            .where(DeploymentGPU.deployment_id == deployment_id)
        )
        gpu_ids = [row[0] for row in result.all()]
        
        # 释放GPU资源
        if gpu_ids:
            await self.db.execute(
                update(GPUResource)
                .where(GPUResource.id.in_(gpu_ids))
                .values(is_available=True)
            )
    
    async def stop_deployment(self, deployment_id: int) -> Dict[str, Any]:
        """
        停止部署
        """
        try:
            # 获取部署信息
            result = await self.db.execute(
                select(Deployment, Server)
                .join(Server, Deployment.server_id == Server.id)
                .where(Deployment.id == deployment_id)
            )
            deployment, server = result.one()
            
            # 停止Docker容器
            container_name = f"acwl-{deployment.deployment_name}-{deployment.id}"
            stop_cmd = f"docker stop {container_name} && docker rm {container_name}"
            
            await self._execute_remote_command(server, stop_cmd)
            
            # 更新部署状态
            await self.db.execute(
                update(Deployment)
                .where(Deployment.id == deployment_id)
                .values(
                    status=DeploymentStatus.STOPPED,
                    updated_at=datetime.utcnow()
                )
            )
            
            # 释放GPU资源
            await self._release_gpu_resources(deployment_id)
            await self.db.commit()
            
            return {
                "message": "部署已停止",
                "deployment_id": deployment_id
            }
            
        except Exception as e:
            logger.error(f"停止部署失败: {str(e)}")
            raise
    
    async def restart_deployment(self, deployment_id: int) -> Dict[str, Any]:
        """
        重启部署
        """
        # 先停止
        await self.stop_deployment(deployment_id)
        
        # 等待一段时间
        await asyncio.sleep(2)
        
        # 重新启动
        await self._deploy_model_async(deployment_id)
        
        return {
            "message": "部署重启中",
            "deployment_id": deployment_id
        }
    
    async def delete_deployment(self, deployment_id: int) -> Dict[str, Any]:
        """
        删除部署
        """
        try:
            # 先停止部署
            deployment_result = await self.db.execute(
                select(Deployment).where(Deployment.id == deployment_id)
            )
            deployment = deployment_result.scalar_one_or_none()
            
            if not deployment:
                raise ValueError(f"部署 {deployment_id} 不存在")
            
            if deployment.status == DeploymentStatus.RUNNING:
                await self.stop_deployment(deployment_id)
            
            # 删除GPU关联记录
            await self.db.execute(
                select(DeploymentGPU).where(DeploymentGPU.deployment_id == deployment_id)
            )
            
            # 删除部署记录
            await self.db.delete(deployment)
            await self.db.commit()
            
            return {
                "message": "部署已删除",
                "deployment_id": deployment_id
            }
            
        except Exception as e:
            logger.error(f"删除部署失败: {str(e)}")
            raise