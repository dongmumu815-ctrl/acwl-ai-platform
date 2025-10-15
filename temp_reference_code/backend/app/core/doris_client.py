#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doris数据库客户端模块

提供与Apache Doris数据库的连接和操作功能。
支持批量插入访问日志数据，提供高性能的日志存储方案。

Author: System
Date: 2024
"""

import json
import time
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from queue import Queue, Empty
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

import requests
import pymysql
from loguru import logger

from app.core.config import settings


@dataclass
class AccessLogEntry:
    """
    访问日志条目数据类
    
    定义访问日志的标准结构
    """
    timestamp: str
    method: str
    url: str
    status_code: int
    response_time: float
    client_ip: str
    user_agent: str
    user_id: Optional[str] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None
    referer: Optional[str] = None
    session_id: Optional[str] = None
    api_key: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的日志数据
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """
        转换为JSON格式
        
        Returns:
            str: JSON格式的日志数据
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)


class DorisClient:
    """
    Doris数据库客户端
    
    提供与Doris数据库的连接和操作功能
    支持批量插入和查询操作
    """
    
    def __init__(self):
        """
        初始化Doris客户端
        """
        self.enabled = settings.DORIS_ENABLED
        self.host = settings.DORIS_HOST
        self.http_port = settings.DORIS_HTTP_PORT
        self.query_port = settings.DORIS_QUERY_PORT
        self.user = settings.DORIS_USER
        self.password = settings.DORIS_PASSWORD
        self.database = settings.DORIS_DATABASE
        self.table = settings.DORIS_ACCESS_LOG_TABLE
        self.batch_size = settings.DORIS_BATCH_SIZE
        self.flush_interval = settings.DORIS_FLUSH_INTERVAL
        
        # 批量插入队列
        self.log_queue: Queue = Queue()
        self.batch_buffer: List[AccessLogEntry] = []
        self.last_flush_time = time.time()
        
        # 线程池和后台任务
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.background_task_running = False
        self.shutdown_event = threading.Event()
        
        if self.enabled:
            self._start_background_tasks()
            logger.info(f"Doris客户端已启用 - 主机: {self.host}, 数据库: {self.database}")
        else:
            logger.info("Doris客户端已禁用")
    
    def _start_background_tasks(self):
        """
        启动后台任务
        
        启动批量插入处理线程
        """
        if not self.background_task_running:
            self.background_task_running = True
            self.executor.submit(self._batch_processor)
            logger.info("Doris后台批量处理任务已启动")
    
    def _batch_processor(self):
        """
        批量处理器
        
        后台线程处理批量插入逻辑
        """
        while not self.shutdown_event.is_set():
            try:
                # 处理队列中的日志
                self._process_queue()
                
                # 检查是否需要强制刷新
                current_time = time.time()
                if (current_time - self.last_flush_time >= self.flush_interval and 
                    len(self.batch_buffer) > 0):
                    self._flush_batch()
                
                # 短暂休眠
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"批量处理器错误: {e}")
                time.sleep(5)  # 错误时等待更长时间
    
    def _process_queue(self):
        """
        处理队列中的日志条目
        
        从队列中取出日志并添加到批量缓冲区
        """
        try:
            while len(self.batch_buffer) < self.batch_size:
                try:
                    log_entry = self.log_queue.get(timeout=1)
                    self.batch_buffer.append(log_entry)
                    self.log_queue.task_done()
                except Empty:
                    break
            
            # 如果缓冲区满了，执行批量插入
            if len(self.batch_buffer) >= self.batch_size:
                self._flush_batch()
                
        except Exception as e:
            logger.error(f"处理队列错误: {e}")
    
    def _flush_batch(self):
        """
        刷新批量缓冲区
        
        将缓冲区中的数据批量插入到Doris
        """
        if not self.batch_buffer:
            return
        
        try:
            # 执行批量插入
            success = self._stream_load(self.batch_buffer)
            
            if success:
                logger.info(f"成功插入 {len(self.batch_buffer)} 条访问日志到Doris")
            else:
                logger.error(f"插入 {len(self.batch_buffer)} 条访问日志到Doris失败")
            
            # 清空缓冲区
            self.batch_buffer.clear()
            self.last_flush_time = time.time()
            
        except Exception as e:
            logger.error(f"刷新批量数据错误: {e}")
            # 发生错误时也要清空缓冲区，避免内存泄漏
            self.batch_buffer.clear()
    
    def _stream_load(self, log_entries: List[AccessLogEntry]) -> bool:
        """
        使用Stream Load批量插入数据
        
        Args:
            log_entries: 日志条目列表
        
        Returns:
            bool: 插入是否成功
        """
        try:
            # 生成唯一的label
            import uuid
            label = f"load_{uuid.uuid4().hex}"
            
            # 构建Stream Load URL - 直接访问BE节点
            url = f"{settings.DORIS_BE_HTTP_URL}/api/{self.database}/{self.table}/_stream_load"
            logger.debug(f"Stream Load URL: {url}")
            
            # 准备数据
            data_lines = []
            for entry in log_entries:
                # 转换为TSV格式（制表符分隔）
                values = [
                    entry.timestamp,
                    entry.method,
                    entry.url,
                    str(entry.status_code),
                    str(entry.response_time),
                    entry.client_ip,
                    entry.user_agent or '',
                    entry.user_id or '',
                    str(entry.request_size or 0),
                    str(entry.response_size or 0),
                    entry.referer or '',
                    entry.session_id or '',
                    entry.api_key or '',
                    entry.error_message or ''
                ]
                data_lines.append('\t'.join(values))
            
            data = '\n'.join(data_lines)
            
            # 设置请求头
            headers = {
                'Expect': '100-continue',
                'Content-Type': 'text/plain',
                'format': 'csv',
                'column_separator': '\\t',
                'line_delimiter': '\\n',
                'label': label
            }
            
            # 发送请求 - 尝试使用requests的auth参数
            auth = None
            if self.password:
                auth = (self.user, self.password)
                logger.debug(f"Stream Load认证信息: user={self.user}")
            
            response = requests.put(
                url,
                data=data.encode('utf-8'),
                headers=headers,
                auth=auth,
                timeout=30
            )
            
            # 检查响应
            if response.status_code == 200:
                result = response.json()
                if result.get('Status') == 'Success':
                    return True
                else:
                    logger.error(f"Stream Load失败: {result}")
                    return False
            else:
                logger.error(f"Stream Load HTTP错误: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Stream Load异常: {e}")
            return False
    
    def log_access(self, method: str, url: str, status_code: int,
                  response_time: float, client_ip: str, user_agent: str = None,
                  user_id: str = None, **kwargs):
        """
        记录访问日志
        
        Args:
            method: HTTP方法
            url: 请求URL
            status_code: 响应状态码
            response_time: 响应时间（秒）
            client_ip: 客户端IP
            user_agent: 用户代理
            user_id: 用户ID
            **kwargs: 其他可选参数
        """
        if not self.enabled:
            return
        
        try:
            # 创建日志条目
            log_entry = AccessLogEntry(
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                method=method,
                url=url,
                status_code=status_code,
                response_time=response_time,
                client_ip=client_ip,
                user_agent=user_agent or '',
                user_id=user_id,
                request_size=kwargs.get('request_size'),
                response_size=kwargs.get('response_size'),
                referer=kwargs.get('referer'),
                session_id=kwargs.get('session_id'),
                api_key=kwargs.get('api_key'),
                error_message=kwargs.get('error_message')
            )
            
            # 添加到队列
            self.log_queue.put(log_entry)
            
        except Exception as e:
            logger.error(f"记录访问日志到Doris失败: {e}")
    
    def query_access_logs(self, start_time: str = None, end_time: str = None,
                         method: str = None, status_code: int = None,
                         limit: int = 1000) -> List[Dict[str, Any]]:
        """
        查询访问日志
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            method: HTTP方法
            status_code: 状态码
            limit: 限制条数
        
        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        if not self.enabled:
            return []
        
        try:
            # 构建查询SQL
            sql = f"SELECT * FROM `{self.database}`.`{self.table}` WHERE 1=1"
            params = []
            
            if start_time:
                sql += " AND timestamp >= %s"
                params.append(start_time)
            
            if end_time:
                sql += " AND timestamp <= %s"
                params.append(end_time)
            
            if method:
                sql += " AND method = %s"
                params.append(method)
            
            if status_code:
                sql += " AND status_code = %s"
                params.append(status_code)
            
            sql += f" ORDER BY timestamp DESC LIMIT {limit}"
            
            # 执行查询
            connection = pymysql.connect(
                host=self.host,
                port=self.query_port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(sql, params)
                    results = cursor.fetchall()
                    return results
            finally:
                connection.close()
                
        except Exception as e:
            logger.error(f"查询访问日志失败: {e}")
            return []
    
    def create_table_if_not_exists(self):
        """
        创建访问日志表（如果不存在）
        
        创建Doris中的访问日志表结构
        """
        if not self.enabled:
            return
        
        try:
            # 创建数据库（如果不存在）
            create_db_sql = f"CREATE DATABASE IF NOT EXISTS `{self.database}`"
            
            # 创建表的SQL
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{self.database}`.`{self.table}` (
                `timestamp` DATETIME NOT NULL COMMENT '时间戳',
                `method` VARCHAR(10) NOT NULL COMMENT 'HTTP方法',
                `url` VARCHAR(2048) NOT NULL COMMENT '请求URL',
                `status_code` INT NOT NULL COMMENT '状态码',
                `response_time` DECIMAL(10,3) NOT NULL COMMENT '响应时间',
                `client_ip` VARCHAR(45) NOT NULL COMMENT '客户端IP',
                `user_agent` VARCHAR(1024) COMMENT '用户代理',
                `user_id` VARCHAR(64) COMMENT '用户ID',
                `request_size` BIGINT COMMENT '请求大小',
                `response_size` BIGINT COMMENT '响应大小',
                `referer` VARCHAR(2048) COMMENT '引用页面',
                `session_id` VARCHAR(128) COMMENT '会话ID',
                `api_key` VARCHAR(128) COMMENT 'API密钥',
                `error_message` TEXT COMMENT '错误信息'
            )
            DUPLICATE KEY(`timestamp`, `method`, `url`)
            DISTRIBUTED BY HASH(`timestamp`) BUCKETS 10
            PROPERTIES (
                "replication_allocation" = "tag.location.default: 1",
                "storage_format" = "V2",
                "compression" = "LZ4"
            )
            """
            
            # 执行SQL
            connection = pymysql.connect(
                host=self.host,
                port=self.query_port,
                user=self.user,
                password=self.password,
                charset='utf8mb4'
            )
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute(create_db_sql)
                    cursor.execute(create_table_sql)
                    connection.commit()
                    logger.info(f"Doris表 `{self.database}`.`{self.table}` 创建成功")
            finally:
                connection.close()
                
        except Exception as e:
            logger.error(f"创建Doris表失败: {e}")
    
    def shutdown(self):
        """
        关闭客户端
        
        优雅地关闭后台任务和连接
        """
        if self.enabled and self.background_task_running:
            logger.info("正在关闭Doris客户端...")
            
            # 设置关闭事件
            self.shutdown_event.set()
            
            # 刷新剩余数据
            if self.batch_buffer:
                self._flush_batch()
            
            # 等待队列处理完成
            self.log_queue.join()
            
            # 关闭线程池
            self.executor.shutdown(wait=True)
            
            self.background_task_running = False
            logger.info("Doris客户端已关闭")


# 全局Doris客户端实例
doris_client = DorisClient()


def get_doris_client() -> DorisClient:
    """
    获取Doris客户端实例
    
    Returns:
        DorisClient: Doris客户端实例
    """
    return doris_client


# 便捷函数
def log_api_access_to_doris(method: str, url: str, status_code: int,
                           response_time: float, client_ip: str,
                           user_agent: str = None, user_id: str = None,
                           **kwargs):
    """
    记录API访问日志到Doris
    
    便捷函数，直接调用全局客户端实例
    
    Args:
        method: HTTP方法
        url: 请求URL
        status_code: 响应状态码
        response_time: 响应时间（秒）
        client_ip: 客户端IP
        user_agent: 用户代理
        user_id: 用户ID
        **kwargs: 其他可选参数
    """
    doris_client.log_access(
        method=method,
        url=url,
        status_code=status_code,
        response_time=response_time,
        client_ip=client_ip,
        user_agent=user_agent,
        user_id=user_id,
        **kwargs
    )


if __name__ == "__main__":
    # 测试Doris客户端
    import time
    
    # 创建测试客户端
    test_client = DorisClient()
    
    if test_client.enabled:
        # 创建表
        test_client.create_table_if_not_exists()
        
        # 测试插入数据
        for i in range(10):
            test_client.log_access(
                method="GET",
                url=f"/api/test/{i}",
                status_code=200,
                response_time=0.123 + i * 0.01,
                client_ip="192.168.1.100",
                user_agent="Test Agent",
                user_id=f"user_{i}"
            )
        
        # 等待批量处理
        time.sleep(5)
        
        # 查询数据
        results = test_client.query_access_logs(limit=5)
        print(f"查询到 {len(results)} 条记录")
        for result in results:
            print(result)
        
        # 关闭客户端
        test_client.shutdown()
    else:
        print("Doris客户端未启用")