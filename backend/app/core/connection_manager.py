#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接管理器
用于解决aiomysql连接在事件循环关闭后被垃圾回收导致的错误
"""

import asyncio
import atexit
import logging
from typing import Set, Dict, Any

logger = logging.getLogger(__name__)

# 全局连接跟踪器
class ConnectionTracker:
    """跟踪和管理所有数据库连接"""
    
    def __init__(self):
        self.connections: Set[Any] = set()
        self.is_shutting_down = False
        # 注册退出处理函数
        atexit.register(self.cleanup_connections)
    
    def register(self, connection):
        """注册一个连接"""
        if not self.is_shutting_down:
            self.connections.add(connection)
    
    def unregister(self, connection):
        """注销一个连接"""
        if connection in self.connections:
            self.connections.remove(connection)
    
    def cleanup_connections(self):
        """清理所有连接"""
        self.is_shutting_down = True
        
        if not self.connections:
            return
            
        logger.info(f"正在关闭 {len(self.connections)} 个数据库连接...")
        
        # 直接清空连接集合，不尝试关闭它们
        # 因为在程序退出时尝试关闭连接可能会导致事件循环已关闭的错误
        self.connections.clear()
        logger.info("已清空连接跟踪器")

# 创建全局连接跟踪器实例
connection_tracker = ConnectionTracker()

# 猴子补丁aiomysql的Connection类
def patch_aiomysql():
    """为aiomysql添加连接跟踪功能"""
    try:
        import aiomysql
        from functools import wraps
        
        # 保存原始方法
        original_init = aiomysql.Connection.__init__
        original_close = aiomysql.Connection.close
        original_del = aiomysql.Connection.__del__
        
        # 修改__del__方法，防止在事件循环关闭后调用close
        def patched_del(self):
            try:
                # 只在连接跟踪器未关闭时尝试调用原始__del__
                if not connection_tracker.is_shutting_down:
                    original_del(self)
            except Exception as e:
                # 忽略事件循环关闭错误
                if "Event loop is closed" not in str(e):
                    logger.error(f"连接析构时出错: {e}")
        
        # 修改__init__方法，注册连接
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            connection_tracker.register(self)
        
        # 修改close方法，注销连接
        @wraps(original_close)
        async def patched_close(self, *args, **kwargs):
            connection_tracker.unregister(self)
            return await original_close(self, *args, **kwargs)
        
        # 应用补丁
        aiomysql.Connection.__init__ = patched_init
        aiomysql.Connection.close = patched_close
        aiomysql.Connection.__del__ = patched_del
        
        logger.info("已为aiomysql应用连接跟踪补丁")
    except ImportError:
        logger.warning("无法导入aiomysql，跳过补丁应用")
    except Exception as e:
        logger.error(f"应用aiomysql补丁时出错: {e}")