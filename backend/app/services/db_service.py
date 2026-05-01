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
        auth_key = os.getenv('DB_SERVICE_AUTH_KEY', 'change-me-in-production').encode()
        
        print(host, port, auth_key)
        
        self.manager = PoolManager(address=(host, port), authkey=auth_key)
        self.manager.connect()
        self.service = self.manager.DataService()

    def execute_sql(self, db_alias: str, query: str) -> Dict[str, Any]:
        """执行SQL查询"""
        try:
            return self.service.execute_sql(db_alias, query)
        except Exception as e:
            logging.error(f"执行SQL失败: {e}")
            return {'success': False, 'error': str(e)}

    def execute_batch_sql(self, db_alias: str, query: str, params_list: List[Any]) -> Dict[str, Any]:
        """批量执行SQL (支持事务提交)"""
        try:
            return self.service.execute_batch_sql(db_alias, query, params_list)
        except Exception as e:
            logging.error(f"批量执行SQL失败: {e}")
            return {'success': False, 'error': str(e)}


class LinkTaskService:
    """任务链接服务"""
    
    def __init__(self):
        self.manager = None
        self.service = None
        
    def _connect(self) -> None:
        """连接到外部数据服务
        
        尝试连接到运行在本地50000端口的数据服务
        
        Raises:
            ConnectionError: 当连接失败时抛出异常
        """
        try:
            # 使用用户指定的端口 50000
            self.manager = PoolManager(address=('127.0.0.1', 50001), authkey=b'change-me-in-production')
            self.manager.connect()
            self.service = self.manager.DataService()
        except Exception as e:
            logging.error(f"数据库连接失败: {e}")
            raise ConnectionError(f"无法连接到数据服务: {e}")
    
    def get_link_menu_types(self) -> Dict[str, Any]:
        """获取任务类型
        
        从外部数据库获取未翻译的图书标题列表
        
        Returns:
            包含成功状态和数据的字典，格式为：
            {'success': True, 'data': [...]} 或 
            {'success': False, 'error': '错误信息'}
        """
        if not self.service:
            self._connect()
        try:
            query = """
               SELECT
                CAST(c.id AS CHAR) AS id,
                m.link_menu_name,
                t.`name`,
                m.db_name,
                m.table_name 
                FROM
                cpc_task_config c
                LEFT JOIN cpc_task_origin_name_menu m ON c.origin_name_menu_id = m.id
                LEFT JOIN cpc_task_origin_type t ON c.origin_type_id = t.id
            """
            
            logging.debug(f"执行SQL查询: {query}")
            
            result = self.service.execute_sql('task_db', query)
            
            if not result['success']:
                logging.error(f"获取待任务类型失败: {result['error']}")
                return {'success': False, 'error': result['error']}
            
            return {
                'success': True,
                'data': result['data']
            }
        
        except Exception as e:
            logging.error(f"获取待任务类型失败: {e}")
            return {'success': False, 'error': str(e)}


class SysDictService:
    def __init__(self):
        self.manager = None
        self.service = None
    
    def _connect(self) -> None:
        try:
            self.manager = PoolManager(address=('127.0.0.1', 50001), authkey=b'change-me-in-production')
            self.manager.connect()
            self.service = self.manager.DataService()
        except Exception as e:
            logging.error(f"数据库连接失败: {e}")
            raise ConnectionError(f"无法连接到数据服务: {e}")
    
    def get_dict_by_type(self, dict_type: str) -> Dict[str, Any]:
        if not self.service:
            self._connect()
        try:
            safe_type = (dict_type or "").replace("'", "''")
            query = f"""
               SELECT dict_label, dict_value
               FROM sys_dict_data
               WHERE dict_type = '{safe_type}'
            """
            result = self.service.execute_sql('cloud_db', query)
            if not result['success']:
                logging.error(f"获取字典失败: {result['error']}")
                return {'success': False, 'error': result['error']}
            data = {}
            rows = result.get('data') or []
            for row in rows:
                try:
                    if isinstance(row, dict):
                        k = str(row.get('dict_label'))
                        v = str(row.get('dict_value'))
                    else:
                        k = str(row[0])
                        v = str(row[1])
                    if k:
                        data[k] = v
                except Exception:
                    continue
            return {'success': True, 'data': data}
        except Exception as e:
            logging.error(f"获取字典失败: {e}")
            return {'success': False, 'error': str(e)}
