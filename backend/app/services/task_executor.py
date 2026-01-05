#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务执行器模块

负责具体任务的执行逻辑，支持多种任务类型
"""

import asyncio
import logging
import os
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
    
    def __init__(self, work_dir: str = None):
        self.work_dir = work_dir or tempfile.gettempdir()
        
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
        
        logger.info(f"开始执行任务: {task_info.get('task_name')} (类型: {task_type})")
        
        start_time = datetime.utcnow()
        result = {
            'success': False,
            'output': '',
            'error': '',
            'exit_code': -1,
            'start_time': start_time,
            'end_time': None,
            'duration_ms': 0
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
            return {'success': False, 'error': '未提供Python脚本内容', 'exit_code': 1}
            
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=self.work_dir) as f:
            f.write(script_content)
            script_path = f.name
            
        try:
            # 执行脚本
            python_path = config.get('python_path', 'python3')
            args = config.get('args', [])
            
            cmd = [python_path, script_path] + args
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.work_dir
            )
            
            stdout, stderr = await proc.communicate()
            
            return {
                'success': proc.returncode == 0,
                'output': stdout.decode(),
                'error': stderr.decode(),
                'exit_code': proc.returncode
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
            return {'success': False, 'error': '未提供Shell脚本内容', 'exit_code': 1}
            
        # 根据操作系统选择后缀
        suffix = '.bat' if os.name == 'nt' else '.sh'
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, dir=self.work_dir) as f:
            f.write(script_content)
            script_path = f.name
            
        try:
            # 赋予执行权限 (Linux/Mac)
            if os.name != 'nt':
                os.chmod(script_path, 0o755)
            
            # 执行脚本
            cmd = [script_path]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.work_dir
            )
            
            stdout, stderr = await proc.communicate()
            
            return {
                'success': proc.returncode == 0,
                'output': stdout.decode(),
                'error': stderr.decode(),
                'exit_code': proc.returncode
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
        # 这里只是模拟SQL执行，实际应该调用数据服务的API
        # 由于executor_service.py主要关注执行逻辑，这里可以预留接口
        return {
            'success': False,
            'error': 'SQL任务执行需要在Worker中集成数据服务客户端',
            'exit_code': 1
        }
