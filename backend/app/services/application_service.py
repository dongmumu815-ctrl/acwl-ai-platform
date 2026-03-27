#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用服务类
处理应用部署、生命周期管理等逻辑
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from jinja2 import Template

from app.models.application import AppInstance, AppDeployment, AppTemplate, AppStatus
from app.models.server import Server
from app.crud.application import app_instance
from app.services.server_service import ServerService
from app.core.deployment_logger import deployment_logger

logger = logging.getLogger(__name__)

class ApplicationService:
    """
    应用服务类
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.server_service = ServerService(db)
        self.db_lock = asyncio.Lock()

    async def uninstall_app(self, instance_id: int, clean_data: bool = False):
        """
        执行应用卸载任务
        """
        logger.info(f"开始卸载应用实例: {instance_id}, 清理数据: {clean_data}")
        
        # 清除旧日志
        deployment_logger.clear(f"instance_{instance_id}")
        
        try:
            # 1. 获取实例详情 (需要 eager load 部署信息)
            stmt = select(AppInstance).options(selectinload(AppInstance.deployments)).where(AppInstance.id == instance_id)
            result = await self.db.execute(stmt)
            instance = result.scalar_one_or_none()
            
            if not instance:
                logger.error(f"应用实例不存在: {instance_id}")
                return

            # 2. 更新状态为正在卸载
            instance.status = AppStatus.uninstalling
            await self.db.commit()

            # 3. 遍历所有部署目标，执行卸载
            uninstall_tasks = []
            global_config = instance.config if instance.config else {}
            for deployment in instance.deployments:
                uninstall_tasks.append(self._uninstall_from_server(deployment, global_config, clean_data))
            
            # 4. 并发执行卸载
            if uninstall_tasks:
                await asyncio.gather(*uninstall_tasks, return_exceptions=True)
            
            # 5. 删除数据库记录
            # 注意：由于 deployments 设置了 cascade="all, delete-orphan"，删除 instance 会自动删除 deployments
            await self.db.delete(instance)
            await self.db.commit()
            
            logger.info(f"应用实例 {instance_id} 卸载完成并已删除记录")

        except Exception as e:
            logger.error(f"应用卸载异常: {str(e)}")
            # 尝试更新状态为错误 (如果还没删除)
            try:
                stmt = update(AppInstance).where(AppInstance.id == instance_id).values(status=AppStatus.error)
                await self.db.execute(stmt)
                await self.db.commit()
            except:
                pass

    async def _uninstall_from_server(self, deployment: AppDeployment, global_config: Dict[str, Any] = None, clean_data: bool = False) -> bool:
        """
        从单个服务器卸载应用
        """
        try:
            server_id = deployment.server_id
            logger.info(f"正在从服务器 {server_id} 卸载应用...")
            
            # 定义日志回调
            channel_id = f"instance_{deployment.instance_id}"
            
            # 确保 deployment_logger 有正确的 loop，修复 "DeploymentLogger loop not ready" 问题
            current_loop = asyncio.get_running_loop()
            try:
                # 检查 loop 是否有效 (存在且运行中)
                # 注意：deployment_logger 是单例，.loop 属性应该在 lifespan 中初始化
                # 但如果在某些情况下丢失，我们需要重新设置
                if not getattr(deployment_logger, 'loop', None) or not deployment_logger.loop.is_running():
                    logger.warning(f"DeploymentLogger loop invalid ({getattr(deployment_logger, 'loop', 'None')}), updating to current loop")
                    deployment_logger.set_loop(current_loop)
            except Exception as e:
                logger.warning(f"Failed to check/update DeploymentLogger loop: {e}")

            def log_cb(msg):
                deployment_logger.log_sync(channel_id, msg)
            
            log_cb(f"Starting uninstall from server {server_id}...")
            
            # 获取服务器信息
            async with self.db_lock:
                stmt = select(Server).where(Server.id == server_id)
                result = await self.db.execute(stmt)
                server = result.scalar_one_or_none()
            
            if not server:
                logger.warning(f"服务器 {server_id} 不存在，跳过远程清理")
                return False

            # 准备参数
            server_info = {
                "ip_address": server.ip_address,
                "ssh_port": server.ssh_port,
                "ssh_username": server.ssh_username,
                "ssh_password": server.ssh_password, 
                "ssh_key_path": getattr(server, "ssh_key_path", None)
            }
            
            # 部署路径
            deploy_path = f"/opt/acwl-apps/instances/{deployment.instance_id}"
            
            # 确定需要清理的数据路径
            data_paths = []
            if clean_data:
                config = global_config or {}
                # 默认路径
                data_root_path = config.get("data_root_path", "/opt/acwl-apps/data")
                
                # 针对 Doris 的特殊处理
                # 如果是 Doris，通常会有 fe 和 be 目录
                role = deployment.role.lower() if deployment.role else ""
                if 'fe' in role:
                    data_paths.append(f"{data_root_path}/fe")
                if 'be' in role:
                    data_paths.append(f"{data_root_path}/be")
                
                logger.info(f"计划清理数据路径: {data_paths}")

            # 执行 SSH 卸载任务
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, 
                self._ssh_uninstall_task, 
                server_info, 
                deploy_path,
                data_paths,
                log_cb
            )

            if not result["success"]:
                logger.warning(f"服务器 {server_id} 卸载清理部分失败: {result['message']}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"服务器 {deployment.server_id} 卸载失败: {str(e)}")
            return False

    @staticmethod
    def _ssh_uninstall_task(server_info: Dict[str, Any], deploy_path: str, data_paths: List[str] = None, log_cb=None) -> Dict[str, Any]:
        """
        SSH 卸载任务 (同步执行)
        1. docker compose down
        2. rm -rf deploy_path
        3. rm -rf data_paths (if provided)
        """
        import paramiko
        
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        result = {"success": False, "message": "", "data": {}}
        
        try:
            if log_cb: log_cb(f"Connecting to {server_info['ip_address']}...")
            
            # 建立连接 (复用代码逻辑，考虑抽取为公共方法)
            connected = False
            last_error = None
            
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
                except Exception as e:
                    last_error = e

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
                except Exception as e:
                    last_error = e
            
            if not connected:
                raise last_error or Exception("无法连接到服务器")
            
            if log_cb: log_cb("Connected successfully.")

            # 辅助函数
            username = server_info["ssh_username"]
            password = server_info.get("ssh_password")
            def sudo_cmd(cmd):
                if username == 'root':
                    return cmd
                elif password:
                    safe_pass = password.replace("'", "'\\''")
                    return f"echo '{safe_pass}' | sudo -S -p '' {cmd}"
                else:
                    return f"sudo -n {cmd}"
            
            def exec_cmd(cmd):
                # Mask password
                display_cmd = cmd
                if "echo" in cmd and "sudo" in cmd and server_info.get("ssh_password"):
                    display_cmd = cmd.replace(server_info.get("ssh_password"), "******")
                
                if log_cb: log_cb(f"$ {display_cmd}")
                
                stdin, stdout, stderr = ssh_client.exec_command(cmd)
                
                output_buffer = []
                while True:
                    line = stdout.readline()
                    if not line:
                        break
                    line_str = line.strip()
                    if line_str:
                        output_buffer.append(line_str)
                        if log_cb:
                            log_cb(line_str)
                
                exit_status = stdout.channel.recv_exit_status()
                out = "\n".join(output_buffer)
                err = stderr.read().decode().strip()
                
                if err and log_cb:
                    log_cb(f"STDERR: {err}")
                    
                return exit_status, out, err

            # 1. 检查目录是否存在
            if log_cb: log_cb(f"Checking deployment directory: {deploy_path}")
            check_cmd = f"test -d {deploy_path}"
            code, _, _ = exec_cmd(check_cmd)
            if code != 0:
                result["success"] = True
                result["message"] = "部署目录不存在，无需清理"
                if log_cb: log_cb("Directory does not exist. Skipping.")
                return result

            # 2. Docker Compose Down
            if log_cb: log_cb("Stopping containers...")
            # 尝试 V2
            down_cmd = f"cd {deploy_path} && {sudo_cmd('docker compose down -v')}"
            code, out, err = exec_cmd(down_cmd)
            
            if code != 0:
                # 尝试 V1
                if log_cb: log_cb("Retry with docker-compose v1...")
                down_cmd_v1 = f"cd {deploy_path} && {sudo_cmd('docker-compose down -v')}"
                code, out, err = exec_cmd(down_cmd_v1)
                # 即使 down 失败，我们也继续尝试删除文件，或者记录警告

            # 3. 删除目录
            if log_cb: log_cb("Removing deployment directory...")
            rm_cmd = sudo_cmd(f"rm -rf {deploy_path}")
            code, out, err = exec_cmd(rm_cmd)
            if code != 0:
                raise Exception(f"删除部署目录失败: {err}")

            # 4. 清理数据目录 (如果指定)
            if data_paths:
                if log_cb: log_cb(f"Cleaning data paths: {data_paths}")
                cleaned_paths = []
                failed_paths = []
                for path in data_paths:
                    # 简单安全检查
                    if not path.strip() or path.strip() == "/":
                        continue
                        
                    clean_cmd = sudo_cmd(f"rm -rf {path}")
                    code, out, err = exec_cmd(clean_cmd)
                    if code != 0:
                        failed_paths.append(f"{path} ({err})")
                    else:
                        cleaned_paths.append(path)
                
                if cleaned_paths:
                    result["message"] += f" 已清理数据: {', '.join(cleaned_paths)}"
                if failed_paths:
                    result["message"] += f" 清理失败: {', '.join(failed_paths)}"
            
            if log_cb: log_cb("Uninstall completed successfully.")
            result["success"] = True
            
        except Exception as e:
            result["success"] = False
            result["message"] = str(e)
        finally:
            ssh_client.close()
            
        return result

    async def deploy_app(self, instance_id: int):
        """
        执行应用部署任务
        """
        logger.info(f"开始部署应用实例: {instance_id}")
        
        # 清除旧日志
        deployment_logger.clear(f"instance_{instance_id}")
        
        try:
            # 1. 获取应用实例（使用新的 Session 防止并发冲突）
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                instance = await app_instance.get(db, instance_id)
                if not instance:
                    raise Exception("应用实例不存在")
                
                # 更新状态为 installing
                instance.status = AppStatus.installing
                await db.commit()
                
                template = await db.get(AppTemplate, instance.template_id)
                if not template:
                    raise Exception("关联模板不存在")

                # 4. 遍历所有部署目标
                # 为每个部署任务创建独立的 Service 实例和 Session
                deploy_tasks = []
                for deployment in instance.deployments:
                    # 使用闭包或独立函数来处理单个部署，确保 session 独立
                    deploy_tasks.append(self._deploy_to_server_wrapper(deployment.id, template.id, instance.config))
                
                # 5. 并发执行部署
                results = await asyncio.gather(*deploy_tasks, return_exceptions=True)
                
                # 6. 汇总结果 (需要重新获取 instance 因为上面的 session 已经结束)
                # 实际上 _deploy_to_server_wrapper 已经处理了单个 deployment 的状态更新
                # 这里只需要统计整体状态
                
                success_count = 0
                for res in results:
                    if isinstance(res, Exception):
                        logger.error(f"部署失败: {str(res)}")
                    elif res:
                        success_count += 1
                
                # 7. 更新最终状态
                # 重新获取 instance
                instance = await app_instance.get(db, instance_id)
                if success_count == len(instance.deployments):
                    instance.status = AppStatus.running
                elif success_count > 0:
                    instance.status = AppStatus.error # 部分成功
                else:
                    instance.status = AppStatus.error
                    
                await db.commit()
                logger.info(f"应用实例 {instance_id} 部署完成，状态: {instance.status}")

        except Exception as e:
            logger.error(f"应用部署全流程异常: {str(e)}")
            # 尝试更新状态为错误
            try:
                stmt = update(AppInstance).where(AppInstance.id == instance_id).values(status=AppStatus.error)
                await self.db.execute(stmt)
                await self.db.commit()
            except:
                pass

    async def cleanup_removed_nodes(self, removed_nodes_info: List[Dict[str, Any]]):
        """
        后台任务：清理已移除的节点
        removed_nodes_info: List[{server_info: dict, deploy_path: str}]
        """
        logger.info(f"开始清理已移除的 {len(removed_nodes_info)} 个节点")
        tasks = []
        loop = asyncio.get_running_loop()
        
        for info in removed_nodes_info:
            tasks.append(
                loop.run_in_executor(
                    None, 
                    self._ssh_uninstall_task, 
                    info["server_info"], 
                    info["deploy_path"]
                )
            )
            
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"清理节点失败: {res}")
                elif not res.get("success"):
                    logger.error(f"清理节点失败: {res.get('message')}")

    async def initialize_doris_cluster(self, instance_id: int) -> Dict[str, Any]:
        """
        初始化 Doris 集群：自动将 BE 和 Follower 注册到 Master FE (幂等操作)
        """
        # 1. 获取实例及部署详情
        instance = await app_instance.get(self.db, instance_id)
        if not instance:
            raise Exception("实例不存在")
            
        deployments = instance.deployments
        
        # 2. 识别角色
        master_fe = None
        followers = []
        observers = []
        backends = []
        
        for dep in deployments:
            # 获取 IP 地址
            stmt = select(Server).where(Server.id == dep.server_id)
            res = await self.db.execute(stmt)
            server = res.scalar_one_or_none()
            if not server:
                continue
                
            ip = server.ip_address
            # 支持多角色 (逗号分隔)，例如 "fe-master,be"
            roles = [r.strip() for r in dep.role.lower().split(',')] if dep.role else ["default"]
            
            node_info = {"ip": ip, "server": server}
            
            if 'fe-master' in roles:
                master_fe = node_info
            
            if 'fe-follower' in roles:
                followers.append(node_info)
            
            if 'fe-observer' in roles:
                observers.append(node_info)
            
            if 'be' in roles:
                backends.append(node_info)
        
        if not master_fe:
            raise Exception("未找到 Master FE 节点，请检查角色配置 (需包含 'fe-master')")
            
        # 准备 SSH 连接信息
        server_info = {
            "ip_address": master_fe["server"].ip_address,
            "ssh_port": master_fe["server"].ssh_port,
            "ssh_username": master_fe["server"].ssh_username,
            "ssh_password": master_fe["server"].ssh_password,
            "ssh_key_path": getattr(master_fe["server"], "ssh_key_path", None)
        }
        
        loop = asyncio.get_running_loop()
        results = []
        
        # 3. 逐个处理节点
        
        # BEs
        for be in backends:
            # Check: SHOW PROC '/backends'
            # 我们在 python 侧过滤输出，比 shell grep 更安全
            sql_check = f"SHOW PROC '/backends'"
            check_cmd = f"docker run --rm --network host mysql:5.7 mysql -h {master_fe['ip']} -P 9030 -u root -B -N -e \"{sql_check}\""
            check_res = await loop.run_in_executor(None, self._ssh_exec_simple_command, server_info, check_cmd)
            
            exists = False
            if check_res["success"]:
                if be['ip'] in check_res["message"]:
                    exists = True
            
            if exists:
                results.append(f"BE {be['ip']} 已存在")
            else:
                sql_add = f"ALTER SYSTEM ADD BACKEND '{be['ip']}:9050'"
                add_cmd = f"docker run --rm --network host mysql:5.7 mysql -h {master_fe['ip']} -P 9030 -u root -e \"{sql_add}\""
                add_res = await loop.run_in_executor(None, self._ssh_exec_simple_command, server_info, add_cmd)
                if add_res["success"]:
                    results.append(f"BE {be['ip']} 添加成功")
                else:
                    results.append(f"BE {be['ip']} 添加失败: {add_res['message']}")

        # Followers
        for fe in followers:
            sql_check = f"SHOW PROC '/frontends'"
            check_cmd = f"docker run --rm --network host mysql:5.7 mysql -h {master_fe['ip']} -P 9030 -u root -B -N -e \"{sql_check}\""
            check_res = await loop.run_in_executor(None, self._ssh_exec_simple_command, server_info, check_cmd)
            
            exists = False
            if check_res["success"]:
                if fe['ip'] in check_res["message"]:
                    exists = True
            
            if exists:
                results.append(f"Follower {fe['ip']} 已存在")
            else:
                sql_add = f"ALTER SYSTEM ADD FOLLOWER '{fe['ip']}:9010'"
                add_cmd = f"docker run --rm --network host mysql:5.7 mysql -h {master_fe['ip']} -P 9030 -u root -e \"{sql_add}\""
                add_res = await loop.run_in_executor(None, self._ssh_exec_simple_command, server_info, add_cmd)
                if add_res["success"]:
                    results.append(f"Follower {fe['ip']} 添加成功")
                else:
                    results.append(f"Follower {fe['ip']} 添加失败: {add_res['message']}")
                    
        # Observers
        for obs in observers:
            sql_check = f"SHOW PROC '/frontends'"
            check_cmd = f"docker run --rm --network host mysql:5.7 mysql -h {master_fe['ip']} -P 9030 -u root -B -N -e \"{sql_check}\""
            check_res = await loop.run_in_executor(None, self._ssh_exec_simple_command, server_info, check_cmd)
            
            exists = False
            if check_res["success"]:
                if obs['ip'] in check_res["message"]:
                    exists = True
            
            if exists:
                results.append(f"Observer {obs['ip']} 已存在")
            else:
                sql_add = f"ALTER SYSTEM ADD OBSERVER '{obs['ip']}:9010'"
                add_cmd = f"docker run --rm --network host mysql:5.7 mysql -h {master_fe['ip']} -P 9030 -u root -e \"{sql_add}\""
                add_res = await loop.run_in_executor(None, self._ssh_exec_simple_command, server_info, add_cmd)
                if add_res["success"]:
                    results.append(f"Observer {obs['ip']} 添加成功")
                else:
                    results.append(f"Observer {obs['ip']} 添加失败: {add_res['message']}")

        return {"success": True, "message": "; ".join(results)}

    @staticmethod
    def _ssh_exec_simple_command(server_info: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        SSH 执行简单命令
        """
        import paramiko
        
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        result = {"success": False, "message": "", "data": {}}
        
        try:
            # 建立连接 (复用连接逻辑)
            connected = False
            last_error = None
            
            # 优先尝试 Key
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
                except Exception as e:
                    last_error = e

            # 尝试密码
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
                except Exception as e:
                    last_error = e
            
            if not connected:
                raise Exception(f"无法连接到服务器: {last_error}")

            # 执行命令
            stdin, stdout, stderr = ssh_client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            
            out_str = stdout.read().decode().strip()
            err_str = stderr.read().decode().strip()
            
            if exit_status == 0:
                result["success"] = True
                result["message"] = out_str
            else:
                result["success"] = False
                result["message"] = f"Exit Code {exit_status}: {err_str}"
                
        except Exception as e:
            result["success"] = False
            result["message"] = str(e)
        finally:
            ssh_client.close()
            
        return result

    async def _deploy_to_server_wrapper(self, deployment_id: int, template_id: int, config: Dict[str, Any]) -> bool:
        """
        包装函数：为每个部署任务创建独立的数据库会话
        """
        from app.core.database import AsyncSessionLocal
        from app.models.application import AppDeployment, AppTemplate
        
        async with AsyncSessionLocal() as db:
            deployment = await db.get(AppDeployment, deployment_id)
            template = await db.get(AppTemplate, template_id)
            if not deployment or not template:
                return False
            
            # 创建临时的 service 实例，绑定新的 session
            service = ApplicationService(db)
            try:
                result = await service._deploy_to_server(deployment, template, config)
                await db.commit()
                return result
            except Exception:
                await db.commit()
                raise

    async def _deploy_to_server(self, deployment: AppDeployment, template: AppTemplate, config: Dict[str, Any]) -> bool:
        """
        部署到单个服务器 (假定 session 已经由调用方管理)
        """
        try:
            # 必须使用 async with 来获取新的 session
            # 修复：后台任务不能复用 self.db (request scoped)，因为 request 结束后 db 会关闭
            # 必须从 sessionmaker 创建新的 session
            # 这里假设 self.db 已经是 AsyncSession，如果是 request scoped，需要特别处理
            # 更好的方式是在 Service 外部创建 Session 传进来，或者在这里创建新的
            
            # 更新状态为 installing
            deployment.status = "installing"
            deployment.container_id = "Deploying: Preparing resources..."
            # 注意：在并发执行中，不要频繁 commit 同一个 session，容易造成冲突
            # 这里先不 commit，依靠最外层的 commit
            # await self.db.commit() 
            # 实际上由于现在每个 task 都有独立的 session，可以 commit
            await self.db.commit() 

            server_id = deployment.server_id
            logger.info(f"正在部署到服务器 {server_id} ...")
            
            # 实时日志回调 (如果需要)
            # 目前系统没有通用的实时日志推送机制 (除了 script_execution)，暂时只记录 logger
            # TODO: 实现 WebSocket 或 SSE 推送部署日志
            
            # 获取服务器信息
            async with self.db_lock:
                stmt = select(Server).where(Server.id == server_id)
                result = await self.db.execute(stmt)
                server = result.scalar_one_or_none()
            
            if not server:
                raise Exception(f"服务器不存在: {server_id}")

            # 准备上下文
            # 逻辑更新：
            # 1. 获取全局配置 (instance.config.global)
            # 2. 获取该服务器的覆盖配置 (instance.config.overrides.<server_id>)
            # 3. 合并配置，优先级：Override > Global
            
            # 兼容旧数据格式（直接是字典的情况）
            raw_config = config or {}
            
            # 确定要使用的模板内容：优先使用实例级别的自定义模板，否则使用模板定义的默认模板
            template_content = raw_config.get("deploy_template", template.deploy_template)
            
            if "global" in raw_config or "overrides" in raw_config:
                base_config = raw_config.get("global", {})
                # 注意：JSON key 通常是字符串，所以 server_id 要转 str
                server_override = raw_config.get("overrides", {}).get(str(server_id), {})
                context = {**base_config, **server_override}
            else:
                context = raw_config.copy()

            # 确保 cpu_limit 和 mem_limit 存在于 context 中，优先使用 deployment 中的设置
            # 如果 deployment 中有值，覆盖 context 中的值（因为 deployment 字段通常对应 UI 上的显式设置）
            if deployment.cpu_limit:
                context['cpu_limit'] = deployment.cpu_limit
            if deployment.mem_limit:
                context['mem_limit'] = deployment.mem_limit
            
            # 确保 role 和 server_id 存在于 context 中 (供模板逻辑使用)
            context['role'] = deployment.role
            context['server_id'] = deployment.server_id
            context['instance_id'] = deployment.instance_id
            context['current_ip'] = server.ip_address # 注入当前服务器IP
            
            # DolphinScheduler 专属：为了兼容环境变量插值，把全局配置的变量也放入 context 中，方便 Jinja 替换
            if template.name and 'dolphinscheduler' in template.name.lower():
                # 已经通过合并逻辑放进 context 了，不需要额外操作，但要确保 DB_URL 等在 context 里存在
                pass

            # --- 自动构建 fe_servers 列表 & 计算 FE_ID (1-9) ---
            # 仅针对 Doris 应用 (role 包含 fe/be 或者是 doris 模板)
            # 通过模板名称或 role 特征判断
            is_doris = False
            if template.name and 'doris' in template.name.lower():
                is_doris = True
            
            # 获取该实例下的所有 FE 节点，构建 name:ip:port 列表
            if is_doris:
                try:
                    stmt_deps = select(AppDeployment).where(AppDeployment.instance_id == deployment.instance_id)
                    res_deps = await self.db.execute(stmt_deps)
                    all_deps = res_deps.scalars().all()
                    
                    logger.warning(f"DEBUG: Found {len(all_deps)} deployments for instance {deployment.instance_id}")
                    
                    # Filter FE nodes and sort them to ensure stable ID assignment
                    fe_deps = []
                    for dep in all_deps:
                         d_role = dep.role.lower().strip() if dep.role else "unknown"
                         # Support multi-role (e.g. "fe-follower,be")
                         d_roles = [r.strip() for r in d_role.split(',')]
                         if 'fe-master' in d_roles or 'fe-follower' in d_roles or 'fe-observer' in d_roles:
                             fe_deps.append(dep)
                    
                    # Sort: Master first, then by server_id
                    # This ensures:
                    # 1. Master gets ID 1 (fe1)
                    # 2. Others get IDs 2-9 sequentially based on server_id
                    def sort_key(d):
                        r = d.role.lower().strip() if d.role else ""
                        roles = [x.strip() for x in r.split(',')]
                        if 'fe-master' in roles:
                            return (0, d.server_id)
                        return (1, d.server_id)
                    
                    fe_deps.sort(key=sort_key)
                    
                    # Build ID Map: server_id -> int ID (1-9)
                    fe_id_map = {}
                    current_assign_id = 1
                    for dep in fe_deps:
                        fe_id_map[dep.server_id] = current_assign_id
                        current_assign_id += 1
                    
                    # Determine ID for CURRENT deployment
                    my_fe_id = fe_id_map.get(deployment.server_id)
                    if not my_fe_id:
                         # Should not happen if logic is correct
                         logger.warning(f"Current deployment {deployment.server_id} not found in fe_deps list? Fallback to 1.")
                         my_fe_id = 1
                    
                    if my_fe_id > 9:
                        logger.error(f"CRITICAL: FE_ID {my_fe_id} exceeds limit of 9! Doris init script may fail.")
                    
                    context['fe_id_value'] = str(my_fe_id)
                    logger.info(f"Assigned FE_ID={my_fe_id} for server {deployment.server_id}")
    
                    fe_node_list = []
                    for dep in fe_deps:
                        # Robust role check
                        d_role = dep.role.lower().strip() if dep.role else "unknown"
                        
                        # 获取 IP
                        stmt_srv = select(Server).where(Server.id == dep.server_id)
                        res_srv = await self.db.execute(stmt_srv)
                        srv_obj = res_srv.scalar_one_or_none()
                        
                        if srv_obj:
                            # 使用映射的 ID 生成名称: fe1, fe2, ...
                            f_id = fe_id_map.get(dep.server_id)
                            f_name = f"fe{f_id}"
                            fe_node_list.append(f"{f_name}:{srv_obj.ip_address}:9010")
                        else:
                                logger.warning(f"DEBUG: Server {dep.server_id} not found for deployment {dep.id}")
    
                    # 如果找到了节点，生成 fe_servers 字符串
                    if fe_node_list:
                        # 确保 fe1 在最前面
                        fe_node_list.sort(key=lambda x: int(x.split(':')[0].replace('fe','')))
                        context['fe_servers'] = ",".join(fe_node_list)
                        logger.info(f"Generated FE_SERVERS for server {server_id}: {context['fe_servers']}")
                    else:
                        logger.warning(f"No FE nodes found for instance {deployment.instance_id} in database (Filtered list is empty).")
                        
                except Exception as e:
                    logger.error(f"构建 FE_SERVERS 列表失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Fallback context['fe_id_value'] if it wasn't set
                    if 'fe_id_value' not in context:
                         dep_role = deployment.role.lower().strip() if deployment.role else "default"
                         context['fe_id_value'] = "1" if 'fe-master' in dep_role else "2"
    
    
                # Fallback: 如果未能从数据库构建 fe_servers (列表为空或出错)，尝试使用 fe_master_ip
                if 'fe_servers' not in context or not context['fe_servers']:
                    if 'fe_master_ip' in context:
                        context['fe_servers'] = f"fe1:{context['fe_master_ip']}:9010"
                        logger.info(f"Using fallback FE_SERVERS: {context['fe_servers']}")
                    else:
                        logger.error("CRITICAL: fe_servers could not be generated and fe_master_ip is missing!")
                
                # --- Ensure current node is in fe_servers (Critical for Follower startup) ---
                # 即使数据库查询遗漏了其他节点，必须确保：
                # 1. Master 在列表中 (用于 join) - 由上面的 fallback 保证
                # 2. 当前节点在列表中 (用于自检和端口绑定)
                
                logger.info(f"DEBUG: Checking FE_SERVERS for role={deployment.role}, server_id={server.id}")
                
                # 使用 robust role check
                current_role = deployment.role.lower().strip() if deployment.role else "unknown"
                current_roles = [r.strip() for r in current_role.split(',')]
    
                if 'fe-master' in current_roles or 'fe-follower' in current_roles or 'fe-observer' in current_roles:
                    # 计算当前节点名称 - 必须与上面的 fe_node_list 构建逻辑一致
                    # 直接使用已经计算好的 fe_id_value
                    if 'fe_id_value' in context:
                         my_fe_name = f"fe{context['fe_id_value']}"
                    elif 'fe-master' in current_roles:
                        my_fe_name = "fe1"
                    else:
                        # Fallback (Should not reach here if logic above succeeded)
                        my_fe_name = f"fe{server.id}"
                    
                    my_entry = f"{my_fe_name}:{server.ip_address}:9010"
                    
                    current_servers = context.get('fe_servers', '')
                    logger.info(f"DEBUG: Current FE_SERVERS before check: '{current_servers}', My Entry: '{my_entry}'")
                    
                    # 检查当前节点名是否存在于列表中 (简单字符串检查即可)
                    if my_fe_name not in current_servers:
                        logger.warning(f"Current node {my_fe_name} missing in FE_SERVERS. Appending it.")
                        if current_servers:
                            context['fe_servers'] = f"{current_servers},{my_entry}"
                        else:
                            context['fe_servers'] = my_entry
                    
                    logger.info(f"DEBUG: Final FE_SERVERS: {context.get('fe_servers')}")
    
                # 确保 fe_master_ip 存在于 context 中 (供 BE 节点使用)
                if 'fe_master_ip' not in context and 'fe_servers' in context:
                     # 尝试从 fe_servers 解析 master ip (假设第一个是 master)
                     try:
                         parts = context['fe_servers'].split(',')
                         for part in parts:
                             if 'fe1' in part:
                                 # format: fe1:ip:port
                                 context['fe_master_ip'] = part.split(':')[1]
                                 break
                     except:
                         pass

            rendered_content = ""
            # 渲染模板
            if template_content:
                try:
                    jinja_template = Template(template_content)
                    rendered_content = jinja_template.render(**context)
                    
                    # 记录生成的 docker-compose.yml 关键部分用于调试
                    if "services:" not in rendered_content:
                        raise Exception("Template Render Error: 'services:' keyword missing in generated docker-compose.yml")
                    
                    logger.info(f"Generated docker-compose.yml for server {server_id} (Length: {len(rendered_content)}): {rendered_content[:200]}...")
                except Exception as e:
                    logger.error(f"模板渲染失败: {e}")
                    raise Exception(f"模板渲染失败: {str(e)}")
            else:
                raise Exception("未找到部署模板内容")
            
            # 渲染 Pre-Deploy Script (如果存在)
            # 优先使用实例配置中的 pre_deploy_script，如果不存在则使用模板默认配置中的
            pre_deploy_script = context.get("pre_deploy_script")
            if not pre_deploy_script and template.default_config:
                pre_deploy_script = template.default_config.get("pre_deploy_script")
            
            # 检查是否需要注入 Harbor 认证信息
            # 如果配置了 harbor_config_id 或者全局有默认 Harbor
            # 这里简单起见，我们查询系统默认 Harbor 配置
            # TODO: 支持在部署时选择 Harbor 配置
            
            from app.models.application import HarborConfig
            stmt_harbor = select(HarborConfig).where(HarborConfig.is_default == True)
            res_harbor = await self.db.execute(stmt_harbor)
            default_harbor = res_harbor.scalar_one_or_none()
            
            # 检查是否需要注入 Harbor 认证信息
            # 如果配置了 harbor_config_id 或者全局有默认 Harbor
            # 这里简单起见，我们查询系统默认 Harbor 配置
            # TODO: 支持在部署时选择 Harbor 配置
            
            from app.models.application import HarborConfig
            stmt_harbor = select(HarborConfig).where(HarborConfig.is_default == True)
            res_harbor = await self.db.execute(stmt_harbor)
            default_harbor = res_harbor.scalar_one_or_none()
            
            # --- 自动生成或增强 pre_deploy_script ---
            # 如果没有预部署脚本，初始化为空字符串
            if not pre_deploy_script:
                pre_deploy_script = "#!/bin/bash\nset -e\n"
            
            if default_harbor:
                # 1. 处理 Insecure Registry 配置
                # 如果 Harbor 配置了 insecure_registry = True，则自动生成配置脚本
                # 注意：我们只在 pre_deploy_script 中尚未包含相关逻辑时才添加
                if getattr(default_harbor, 'insecure_registry', False):
                     registry_domain = default_harbor.url.replace("http://", "").replace("https://", "")
                     if registry_domain.endswith("/"): registry_domain = registry_domain[:-1]
                     
                     # 检查脚本中是否已有 daemon.json 修改逻辑 (简单检查)
                     if "insecure-registries" not in pre_deploy_script:
                         logger.info(f"Injecting Insecure Registry config for {registry_domain}")
                         insecure_script = f"""
# Auto-injected Insecure Registry Config for {registry_domain}
if [ ! -f "/etc/docker/daemon.json" ]; then echo "{{}}" | sudo tee "/etc/docker/daemon.json" > /dev/null; fi
sudo python3 -c "
import json, os, sys
f_path = '/etc/docker/daemon.json'
reg = '{registry_domain}'
mirrors = ['https://docker.1ms.run', 'https://docker.m.daocloud.io']
changed = False
try:
    if os.path.exists(f_path):
        with open(f_path, 'r') as f:
            c = f.read().strip()
            d = json.loads(c) if c else {{}}
    else: d = {{}}
    
    # Handle Insecure Registries
    # Handle Insecure Registries
    regs = d.get('insecure-registries', [])
    if reg not in regs:
        regs.append(reg)
        d['insecure-registries'] = regs
        changed = True

    # Handle Registry Mirrors
    current_mirrors = d.get('registry-mirrors', [])
    for m in mirrors:
        if m not in current_mirrors:
            current_mirrors.append(m)
            changed = True
    
    if changed:
        d['registry-mirrors'] = current_mirrors
        with open(f_path, 'w') as f: json.dump(d, f, indent=4)
        sys.exit(100)
except Exception as e: print(e); sys.exit(1)
"
if [ $? -eq 100 ]; then
    echo "Reloading Docker..."
    sudo systemctl reload docker || sudo systemctl restart docker
    sleep 3
else
    # Check if registry is actually effective
    if ! docker info 2>/dev/null | grep -q "{registry_domain}"; then
         echo "Registry {registry_domain} not found in docker info, reloading..."
         sudo systemctl reload docker || sudo systemctl restart docker
         sleep 3
    fi
fi
"""
                         pre_deploy_script += insecure_script

                # 2. 处理 Docker Login 和 Pull
                try:
                    # 将 Harbor 信息注入 context
                    context['harbor_url'] = default_harbor.url
                    registry_domain = default_harbor.url.replace("http://", "").replace("https://", "")
                    if registry_domain.endswith("/"): registry_domain = registry_domain[:-1]
                    
                    context['harbor_registry'] = registry_domain
                    context['harbor_username'] = default_harbor.username
                    context['harbor_password'] = default_harbor.password
                    
                    # 如果 pre_deploy_script 是模板，先渲染
                    try:
                        pre_deploy_script = Template(pre_deploy_script).render(**context)
                    except Exception as tpl_err:
                        logger.warning(f"Pre-render pre_deploy_script failed: {tpl_err}")

                    # 检查脚本中是否已经包含了 login 逻辑
                    if "docker login" not in pre_deploy_script and default_harbor.username and default_harbor.password:
                         logger.info(f"Appending Docker Login for {registry_domain} to pre-deploy script")
                         login_cmd = f"\n# Auto-injected Docker Login\necho '{default_harbor.password}' | docker login '{registry_domain}' -u '{default_harbor.username}' --password-stdin\n"
                         pre_deploy_script += login_cmd
                         
                         # 同时尝试从渲染后的 compose 内容中提取镜像，并显式 pull
                         # 这是一个 hack，因为 docker compose 有时读取不到 login 凭证
                         if rendered_content:
                             try:
                                 import yaml
                                 compose_data = yaml.safe_load(rendered_content)
                                 services = compose_data.get('services', {})
                                 for svc_name, svc_conf in services.items():
                                     img = svc_conf.get('image')
                                     # 只要镜像不是空的，都尝试 pull。
                                     # 即使镜像不在 Harbor 域名下，docker login 也许是针对 docker hub 的?
                                     # 这里我们主要针对的是 Private Harbor，但也放宽限制，只要配置了 Harbor，就尝试 pull
                                     # 如果是公共镜像，pull 也会成功。如果是私有镜像且 login 成功，也会成功。
                                     if img:
                                         logger.info(f"Injecting docker pull for {img}")
                                         # Add retry logic for docker pull (3 attempts)
                                         pre_deploy_script += f"echo 'Pulling {img}...' \n"
                                         pre_deploy_script += f"for i in {{1..3}}; do docker pull {img} && break || {{ echo 'Pull failed, retrying in 5s...'; sleep 5; }}; done\n"
                             except Exception as yaml_err:
                                 logger.warning(f"Failed to parse compose file for image pulling: {yaml_err}")
                         
                except Exception as e:
                    logger.warning(f"Failed to inject Harbor credentials into pre_deploy_script: {e}")

            if pre_deploy_script:
                # 再次尝试渲染，以防注入的命令中也有模板变量（虽然不太可能，但为了安全）
                # 注意：如果上面已经渲染过，这里再次渲染通常是幂等的（除非有转义问题）
                # 为了稳妥，我们可以跳过第二次渲染，或者捕获错误
                try:
                    # 只有当包含 {{ }} 时才尝试再次渲染
                    if "{{" in pre_deploy_script:
                        pre_deploy_script = Template(pre_deploy_script).render(**context)
                    logger.info(f"Final pre_deploy_script ready (Length: {len(pre_deploy_script)})")
                except Exception as e:
                    logger.warning(f"pre_deploy_script 二次渲染失败，将使用原始内容: {e}")

            # 准备部署参数
            server_info = {
                "ip_address": server.ip_address,
                "ssh_port": server.ssh_port,
                "ssh_username": server.ssh_username,
                "ssh_password": server.ssh_password, 
                "ssh_key_path": getattr(server, "ssh_key_path", None)
            }
            
            # 部署路径: /opt/acwl-apps/instances/{instance_id}
            deploy_path = f"/opt/acwl-apps/instances/{deployment.instance_id}"

            # 执行 SSH 部署任务
            # 更新状态为 'deploying'
            deployment.status = "deploying"
            deployment.container_id = "Deploying: Connecting..."
            # 同样不 commit
            # await self.db.commit()
            await self.db.commit()
            
            # 定义日志回调
            channel_id = f"instance_{deployment.instance_id}"
            
            # 确保 deployment_logger 有正确的 loop，修复 "DeploymentLogger loop not ready" 问题
            current_loop = asyncio.get_running_loop()
            try:
                # 检查 loop 是否有效 (存在且运行中)
                # 注意：deployment_logger 是单例，.loop 属性应该在 lifespan 中初始化
                # 但如果在某些情况下丢失，我们需要重新设置
                if not getattr(deployment_logger, 'loop', None) or not deployment_logger.loop.is_running():
                    logger.warning(f"DeploymentLogger loop invalid ({getattr(deployment_logger, 'loop', 'None')}), updating to current loop")
                    deployment_logger.set_loop(current_loop)
            except Exception as e:
                logger.warning(f"Failed to check/update DeploymentLogger loop: {e}")

            def log_cb(msg):
                deployment_logger.log_sync(channel_id, msg)
            
            deployment_logger.log_sync(channel_id, f"Starting deployment to server {server_id}...")

            loop = current_loop
            result = await loop.run_in_executor(
                None, 
                self._ssh_deploy_task, 
                server_info, 
                deploy_path, 
                rendered_content,
                template.app_type if template else "docker_compose",
                pre_deploy_script,
                log_cb
            )

            if not result["success"]:
                raise Exception(f"部署执行失败: {result['message']}")

            # 更新部署状态
            deployment.status = "running"
            deployment.container_id = result["data"].get("container_id", "")
            
            # 保存端口信息
            ports_info = {}
            
            # Doris 默认端口 (仅针对 Doris 应用)
            if is_doris:
                # FE 端口
                if "fe" in str(context.get("role", "")):
                    ports_info["FE_HTTP"] = "8030"
                    ports_info["FE_RPC"] = "9020"
                    ports_info["FE_QUERY"] = "9030"
                    ports_info["FE_EDIT"] = "9010"
                
                # BE 端口
                if "be" in str(context.get("role", "")):
                    ports_info["BE_HTTP"] = "8040"
                    ports_info["BE_RPC"] = "9060"
                    ports_info["BE_HEARTBEAT"] = "9050"
                    ports_info["BE_BRPC"] = "8060"

            if "http_port" in context:
                ports_info["HTTP"] = context["http_port"]
            elif "port" in context:
                ports_info["PORT"] = context["port"]
            
            if ports_info:
                deployment.ports = ports_info
            
            # 关键修复：不要在这里使用 self.db.add(deployment)
            # 因为这个 deployment 对象是 attach 到 session 的，直接修改属性即可
            # 等待最外层的 commit() 来提交更改
            self.db.add(deployment) 
            await self.db.commit() 
            
            return True
        except Exception as e:
            logger.error(f"服务器 {deployment.server_id} 部署失败: {str(e)}")
            deployment.status = "error"
            # 记录错误信息到 container_id 字段以便调试
            # 截断错误信息以适应数据库字段限制 (VARCHAR(100))
            # "Error: " 占用 7 字符，预留 93 字符，安全起见截取 85 字符
            error_msg = str(e)
            if len(error_msg) > 85:
                deployment.container_id = f"Error: {error_msg[:40]}...{error_msg[-40:]}"
            else:
                deployment.container_id = f"Error: {error_msg}"
            
            # 同样移除 add，因为在上层捕获后会统一 commit
            self.db.add(deployment)
            await self.db.commit()
            raise e

    @staticmethod
    def _ssh_deploy_task(server_info: Dict[str, Any], deploy_path: str, content: str, app_type: str = "docker_compose", pre_deploy_script: str = None, log_cb=None) -> Dict[str, Any]:
        """
        SSH 部署任务 (同步执行)
        """
        import paramiko
        import time
        import base64
        
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        result = {"success": False, "message": "", "data": {}}
        
        try:
            if log_cb:
                log_cb(f"Connecting to {server_info['ip_address']}...")

            # 建立连接
            connected = False
            last_error = None
            
            # 优先尝试 Key
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
                except Exception as e:
                    last_error = e

            # 尝试密码
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
                except Exception as e:
                    last_error = e
            
            if not connected:
                raise last_error or Exception("无法连接到服务器")
            
            if log_cb:
                log_cb("Connected successfully.")

            # 设置 KeepAlive
            transport = ssh_client.get_transport()
            if transport:
                transport.set_keepalive(30)

            # 辅助函数：执行命令
            def exec_cmd(cmd):
                # Mask password in log
                display_cmd = cmd
                if "echo" in cmd and "sudo" in cmd and server_info.get("ssh_password"):
                    display_cmd = cmd.replace(server_info.get("ssh_password"), "******")
                
                if log_cb:
                    log_cb(f"$ {display_cmd}")

                stdin, stdout, stderr = ssh_client.exec_command(cmd)
                
                output_buffer = []
                while True:
                    line = stdout.readline()
                    if not line:
                        break
                    line_str = line.strip()
                    if line_str:
                        output_buffer.append(line_str)
                        if log_cb:
                            log_cb(line_str)
                
                exit_status = stdout.channel.recv_exit_status()
                out = "\n".join(output_buffer)
                
                err = stderr.read().decode().strip()
                if err:
                    if log_cb:
                        log_cb(f"STDERR: {err}")
                
                return exit_status, out, err

            # 辅助函数：生成 sudo 命令
            username = server_info["ssh_username"]
            password = server_info.get("ssh_password")
            def sudo_cmd(cmd):
                if username == 'root':
                    return cmd
                elif password:
                    safe_pass = password.replace("'", "'\\''")
                    return f"echo '{safe_pass}' | sudo -S -p '' {cmd}"
                else:
                    return f"sudo -n {cmd}"

            # 1. 创建目录
            if log_cb: log_cb(f"Creating directory: {deploy_path}")
            mkdir_cmd = sudo_cmd(f"mkdir -p {deploy_path}")
            code, out, err = exec_cmd(mkdir_cmd)
            if code != 0:
                raise Exception(f"创建目录失败: {err}")

            # 1.5. 执行 Pre-Deploy Script (如果存在)
            if pre_deploy_script:
                logger.info(f"Executing pre_deploy_script on {server_info['ip_address']}...")
                if log_cb: log_cb(f"Executing Pre-Deploy script...")
                
                pre_script_b64 = base64.b64encode(pre_deploy_script.encode()).decode()
                pre_script_target = f"{deploy_path}/pre_deploy.sh"
                
                # 写入到临时文件 (因为目标目录可能需要 sudo 权限)
                temp_pre_script = f"/tmp/pre_deploy_{int(time.time())}.sh"
                write_pre_cmd = f"echo '{pre_script_b64}' | base64 -d > {temp_pre_script}"
                code, out, err = exec_cmd(write_pre_cmd)
                if code != 0:
                     raise Exception(f"写入临时 Pre-Deploy 脚本失败: {err}")
                
                # 移动到目标目录
                mv_pre_cmd = sudo_cmd(f"mv {temp_pre_script} {pre_script_target}")
                code, out, err = exec_cmd(mv_pre_cmd)
                if code != 0:
                     raise Exception(f"移动 Pre-Deploy 脚本失败: {err}")
                
                # 赋予权限并执行
                # 注意：pre_deploy_script 可能包含 systemctl reload docker，这可能导致 ssh 连接中断？
                # 应该没问题，只要不重启 sshd
                # 关键修复：Docker Login 通常是针对当前用户（这里是 root，因为用了 sudo），但 compose up 也是用 sudo
                # 问题在于：docker login 生成的 config.json 是否能被后续的 docker compose 看到？
                # 如果 sudo docker login，配置文件在 /root/.docker/config.json
                # 如果 sudo docker compose，它应该也能读取 /root/.docker/config.json
                # 为了保险，我们强制在脚本中 explicit 输出 login 结果
                exec_pre_cmd = f"chmod +x {pre_script_target} && cd {deploy_path} && {sudo_cmd('./pre_deploy.sh')}"
                code, out, err = exec_cmd(exec_pre_cmd)
                
                # 兼容性处理：只要返回 0 或者日志中包含成功标志，都视为成功
                is_success = False
                if code == 0:
                    is_success = True
                elif "Harbor configuration generated successfully" in out or "Harbor configuration generated successfully" in err:
                    is_success = True
                
                if is_success:
                    logger.info(f"Pre-Deploy 脚本执行完成 (Code {code})。Output: {out}")
                else:
                    raise Exception(f"Pre-Deploy 脚本执行失败 (Code {code}): {err}\nOutput: {out}")
                
                logger.info("Pre-Deploy script executed successfully.")

            # 2. 写入文件
            b64_content = base64.b64encode(content.encode()).decode()
            
            if app_type == "shell_script":
                target_file = f"{deploy_path}/install.sh"
            else:
                target_file = f"{deploy_path}/docker-compose.yml"
                
            temp_file = f"/tmp/deploy_{int(time.time())}.tmp"
            write_cmd = f"echo '{b64_content}' | base64 -d > {temp_file}"
            code, out, err = exec_cmd(write_cmd)
            if code != 0:
                 raise Exception(f"写入临时文件失败: {err}")
            
            mv_cmd = sudo_cmd(f"mv {temp_file} {target_file}")
            code, out, err = exec_cmd(mv_cmd)
            if code != 0:
                 raise Exception(f"移动配置文件失败: {err}")

            # 根据 app_type 执行不同的逻辑
            if app_type == "shell_script":
                # 执行脚本
                logger.info(f"Executing shell script on {server_info['ip_address']}...")
                chmod_cmd = sudo_cmd(f"chmod +x {target_file}")
                exec_cmd(chmod_cmd)
                
                # 执行脚本并捕获输出
                # 注意：对于耗时较长的脚本，这里会阻塞直到完成
                run_script_cmd = f"cd {deploy_path} && {sudo_cmd('./install.sh')}"
                code, out, err = exec_cmd(run_script_cmd)
                
                if code != 0:
                    raise Exception(f"脚本执行失败 (Code {code}): {err}\nOutput: {out}")
                
                logger.info(f"Script execution success on {server_info['ip_address']}")
                result["success"] = True
                result["data"]["container_id"] = "Script Executed"
                
            else:
                # 默认 docker_compose 逻辑
                # 3. 检测 Docker Compose 版本
                compose_cmd = None
                
                # 检查 v2
                check_v2 = sudo_cmd("docker compose version")
                code, out, err = exec_cmd(check_v2)
                if code == 0:
                    compose_cmd = "docker compose"
                else:
                    # 检查 v1
                    check_v1 = sudo_cmd("docker-compose version")
                    code, out, err = exec_cmd(check_v1)
                    if code == 0:
                        compose_cmd = "docker-compose"
                
                if not compose_cmd:
                    raise Exception("未检测到 Docker Compose (v2 或 v1)，请先安装 Docker Compose")

                # 4. 执行 Docker Compose Up
                logger.info(f"Running {compose_cmd} up on {server_info['ip_address']}...")
                up_cmd = f"cd {deploy_path} && {sudo_cmd(f'{compose_cmd} up -d --remove-orphans')}"
                code, out, err = exec_cmd(up_cmd)
                
                if code != 0:
                     raise Exception(f"启动应用失败: {err} (out: {out})")
                
                logger.info(f"Docker compose up success on {server_info['ip_address']}")

                # 5. 获取 Container ID
                # 尝试获取带服务名的格式 (仅限 v2)
                if compose_cmd == "docker compose":
                    ps_cmd = f"cd {deploy_path} && {sudo_cmd(f'{compose_cmd} ps --format \"{{{{.Service}}}}:{{{{.ID}}}}\"')}"
                else:
                    ps_cmd = f"cd {deploy_path} && {sudo_cmd(f'{compose_cmd} ps -q')}"
                    
                code, out, err = exec_cmd(ps_cmd)
                if code != 0:
                     # Fallback for v1 or if format fails
                     ps_cmd = f"cd {deploy_path} && {sudo_cmd(f'{compose_cmd} ps -q')}"
                     code, out, err = exec_cmd(ps_cmd)
                     if code != 0:
                        raise Exception(f"获取容器ID失败: {err}")
                
                lines = out.splitlines()
                formatted_ids = []
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    if ":" in line and compose_cmd == "docker compose":
                        # Format: service:full_id
                        parts = line.split(":")
                        if len(parts) >= 2:
                            svc = parts[0]
                            cid = parts[1][:12] # Short ID
                            # Harbor has many services, so we just keep service name to save space
                            # Or just keep the first few important ones?
                            # Let's try to format it compactly: "svc:id"
                            formatted_ids.append(f"{svc}:{cid}")
                    else:
                        # Just ID
                        formatted_ids.append(line[:12])
                
                # Harbor 有 9 个服务，产生的字符串非常长 (e.g. core:xxx,jobservice:xxx...)
                # 数据库字段可能只有 100 或 255 长度
                # 策略：如果太长，只保留核心服务的 ID，或者截断
                main_container_id = ",".join(formatted_ids) if formatted_ids else "unknown"
                
                # 强制截断以适应数据库字段 (假设是 VARCHAR(255) 或更短)
                # 安全起见，保留前 100 个字符
                if len(main_container_id) > 100:
                    logger.warning(f"Container IDs string too long ({len(main_container_id)}), truncating...")
                    # 尝试优先保留 core, portal, registry
                    priority_svcs = ["core", "portal", "registry"]
                    priority_ids = []
                    other_ids = []
                    
                    for item in formatted_ids:
                        is_priority = False
                        for p in priority_svcs:
                            if item.startswith(p):
                                priority_ids.append(item)
                                is_priority = True
                                break
                        if not is_priority:
                            other_ids.append(item)
                    
                    # 重新组合，优先展示核心服务
                    final_list = priority_ids + other_ids
                    main_container_id = ",".join(final_list)
                    
                    # 再次检查并硬截断
                    if len(main_container_id) > 100:
                         main_container_id = main_container_id[:97] + "..."

                result["success"] = True
                result["data"]["container_id"] = main_container_id

            
        except Exception as e:
            result["success"] = False
            result["message"] = str(e)
        finally:
            ssh_client.close()
            
        return result
