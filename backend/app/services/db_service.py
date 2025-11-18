from multiprocessing.managers import BaseManager 
from typing import Dict, List, Optional, Any, Tuple
import os
import json
import logging
from dotenv import load_dotenv

class PoolManager(BaseManager):
    pass


# 注册 DataService
PoolManager.register('DataService')


class RouterDBService:
    """路由器数据库服务"""
    
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 从环境变量获取配置，如果没有则使用默认值
        host = os.getenv('DB_SERVICE_HOST', '127.0.0.1')
        # 默认端口调整为 50001，以匹配当前部署的 DataService
        port = int(os.getenv('DB_SERVICE_PORT', '50001'))
        auth_key = os.getenv('DB_SERVICE_AUTH_KEY', 'cepiec2024').encode()
        
        print(host, port, auth_key)
        
        self.manager = PoolManager(address=(host, port), authkey=auth_key)
        self.manager.connect()
        self.service = self.manager.DataService()