#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务执行器模块

负责具体任务的执行逻辑，支持多种任务类型
"""

import asyncio
import logging
import os
import sys
import subprocess
import tempfile
import json
from typing import Dict, Any, Optional
from datetime import datetime

from app.schemas.task import TaskType

logger = logging.getLogger(__name__)


class TaskExecutionExecutor:
    """
    任务执行器类
    
    负责具体任务的执行逻辑
    """
    
    def __init__(self, work_dir: str = None, log_dir: str = None):
        self.work_dir = work_dir or tempfile.gettempdir()
        # 默认日志目录
        self.log_dir = log_dir or os.path.join(os.getcwd(), 'logs', 'tasks')
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir, exist_ok=True)
            except Exception as e:
                logger.warning(f"无法创建日志目录 {self.log_dir}: {e}")
                # 回退到临时目录
                self.log_dir = os.path.join(tempfile.gettempdir(), 'acwl_logs')
                os.makedirs(self.log_dir, exist_ok=True)
        
    async def execute_task(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task_info: 任务信息，包含任务类型、内容等
            
        Returns:
            执行结果
        """
        task_type = task_info.get('task_type')
        task_content = task_info.get('task_content', {})
        task_config = task_info.get('task_config', {})
        instance_id = task_info.get('instance_id')
        
        logger.info(f"开始执行任务: {task_info.get('task_name')} (类型: {task_type})")
        
        # 确定日志文件路径
        if instance_id:
            # 确保文件名安全
            safe_id = "".join([c for c in instance_id if c.isalnum() or c in ('-', '_')])
            log_file = os.path.join(self.log_dir, f"{safe_id}.log")
        else:
            log_file = os.path.join(self.log_dir, f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.getpid()}.log")
            
        # 将日志路径放入配置中传递给执行方法
        task_config['log_file'] = log_file
        
        start_time = datetime.utcnow()
        result = {
            'success': False,
            'output': '',
            'error': '',
            'exit_code': -1,
            'start_time': start_time,
            'end_time': None,
            'duration_ms': 0,
            'log_path': log_file
        }
        
        try:
            if task_type == 'python_code':
                execution_result = await self._execute_python(task_content, task_config)
            elif task_type == 'shell_script':
                execution_result = await self._execute_shell(task_content, task_config)
            elif task_type == 'sql_query':
                execution_result = await self._execute_sql(task_content, task_config)
            else:
                # 默认处理或者不支持的类型
                execution_result = {
                    'success': False,
                    'error': f"不支持的任务类型: {task_type}",
                    'exit_code': 1
                }
                
            result.update(execution_result)
            
        except Exception as e:
            logger.error(f"任务执行异常: {e}")
            result['error'] = str(e)
            result['success'] = False
        finally:
            end_time = datetime.utcnow()
            result['end_time'] = end_time
            result['duration_ms'] = int((end_time - start_time).total_seconds() * 1000)
            
        return result
    
    async def _execute_python(self, content: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Python代码任务
        """
        script_content = content.get('script_content')
        if not script_content:
            # 尝试从 code 字段获取
            script_content = content.get('code')
            
        if not script_content:
            return {'success': False, 'error': '未提供Python脚本内容', 'exit_code': 1}
            
        # 准备工作目录
        cwd = config.get('cwd', self.work_dir)
        if not os.path.exists(cwd):
            os.makedirs(cwd, exist_ok=True)
            
        # 准备环境变量
        env = os.environ.copy()
        custom_env = config.get('environment_variables', {})
        if custom_env:
            for k, v in custom_env.items():
                env[str(k)] = str(v)
            
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=self.work_dir) as f:
            f.write(script_content)
            script_path = f.name
            
        log_file = config.get('log_file')
            
        try:
            # 执行脚本
            python_path = config.get('python_path', sys.executable)
            args = config.get('args', [])
            
            cmd = [python_path, script_path] + args
            
            # 打开日志文件
            log_f = None
            if log_file:
                try:
                    log_f = open(log_file, 'w', encoding='utf-8')
                except Exception as e:
                    logger.error(f"无法打开日志文件 {log_file}: {e}")
            
            # 如果无法打开日志文件，使用PIPE
            stdout_dest = log_f if log_f else asyncio.subprocess.PIPE
            stderr_dest = asyncio.subprocess.STDOUT if log_f else asyncio.subprocess.PIPE
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=stdout_dest,
                stderr=stderr_dest,
                cwd=cwd,
                env=env
            )
            
            if log_f:
                await proc.wait()
                log_f.close()
                stdout = b''
                stderr = b''
                
                # 读取部分日志作为输出返回
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        # 读取前10KB
                        stdout = f.read(10000).encode('utf-8')
                except Exception:
                    pass
            else:
                stdout, stderr = await proc.communicate()
            
            return {
                'success': proc.returncode == 0,
                'output': stdout.decode('utf-8', errors='ignore') if stdout else '',
                'error': stderr.decode('utf-8', errors='ignore') if stderr else '',
                'exit_code': proc.returncode,
                'log_path': log_file
            }
            
        finally:
            # 清理临时文件
            if os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except:
                    pass

    async def _execute_shell(self, content: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Shell脚本任务
        """
        script_content = content.get('script_content')
        if not script_content:
             # 尝试从 code 字段获取
            script_content = content.get('code')
            
        if not script_content:
            return {'success': False, 'error': '未提供Shell脚本内容', 'exit_code': 1}
            
        # 准备工作目录
        cwd = config.get('cwd', self.work_dir)
        if not os.path.exists(cwd):
            os.makedirs(cwd, exist_ok=True)
            
        # 准备环境变量
        env = os.environ.copy()
        custom_env = config.get('environment_variables', {})
        if custom_env:
            for k, v in custom_env.items():
                env[str(k)] = str(v)
            
        # 根据操作系统选择后缀
        suffix = '.bat' if os.name == 'nt' else '.sh'
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, dir=self.work_dir) as f:
            f.write(script_content)
            script_path = f.name
            
        log_file = config.get('log_file')
            
        try:
            # 赋予执行权限 (Linux/Mac)
            if os.name != 'nt':
                os.chmod(script_path, 0o755)
            
            # 执行脚本
            cmd = [script_path]
            
            # 打开日志文件
            log_f = None
            if log_file:
                try:
                    log_f = open(log_file, 'w', encoding='utf-8')
                except Exception as e:
                    logger.error(f"无法打开日志文件 {log_file}: {e}")
            
            # 如果无法打开日志文件，使用PIPE
            stdout_dest = log_f if log_f else asyncio.subprocess.PIPE
            stderr_dest = asyncio.subprocess.STDOUT if log_f else asyncio.subprocess.PIPE
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=stdout_dest,
                stderr=stderr_dest,
                cwd=cwd,
                env=env
            )
            
            if log_f:
                await proc.wait()
                log_f.close()
                stdout = b''
                stderr = b''
                
                # 读取部分日志作为输出返回
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        # 读取前10KB
                        stdout = f.read(10000).encode('utf-8')
                except Exception:
                    pass
            else:
                stdout, stderr = await proc.communicate()
            
            return {
                'success': proc.returncode == 0,
                'output': stdout.decode('utf-8', errors='ignore') if stdout else '',
                'error': stderr.decode('utf-8', errors='ignore') if stderr else '',
                'exit_code': proc.returncode,
                'log_path': log_file
            }
            
        finally:
            # 清理临时文件
            if os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except:
                    pass

    async def _execute_sql(self, content: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行SQL查询任务 (通过DB服务)
        """
        sql = content.get('sql')
        if not sql:
            # 尝试从 code 字段获取
            sql = content.get('code')
            
        if not sql:
            return {'success': False, 'error': '未提供SQL内容', 'exit_code': 1}
            
        db_alias = config.get('db_alias', 'default')
        # 如果 config 中没有 db_alias，尝试从 content 获取
        if not db_alias or db_alias == 'default':
            db_alias = content.get('db_alias', 'default')

        try:
            # 延迟导入以避免循环依赖
            from app.services.db_service import RouterDBService
            
            # 实例化数据库服务
            # 注意：这里每次执行都会创建一个新的连接，对于高并发场景可能需要优化
            # 但考虑到这是一个独立进程/任务，且 Manager 连接是轻量级的，暂时可行
            db_service = RouterDBService()
            
            # 在线程池中执行，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: db_service.execute_sql(db_alias, sql)
            )
            
            if not result.get('success'):
                return {
                    'success': False, 
                    'error': result.get('error', 'Unknown error'), 
                    'exit_code': 1
                }
                
            return {
                'success': True,
                'output': json.dumps(result.get('data'), ensure_ascii=False, indent=2),
                'error': '',
                'exit_code': 0
            }
            
        except Exception as e:
            logger.error(f"SQL执行失败: {e}")
            return {'success': False, 'error': str(e), 'exit_code': 1}
