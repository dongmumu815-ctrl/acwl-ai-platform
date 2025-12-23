from typing import Dict, List, Optional, Any
import json
import logging
from multiprocessing.managers import BaseManager

# 获取日志记录器
logger = logging.getLogger(__name__)

class PoolManager(BaseManager):
    """外部数据服务连接管理器"""
    pass


class DataLink:
    """外部数据链接

    
    
    """
 
    
    def __init__(self):
        """初始化翻译服务"""
        self.manager = None
        self.service = None
        
        # 注册DataService
        PoolManager.register('DataService')
    
    def _connect(self) -> None:
        """连接到外部数据服务
        
        尝试连接到运行在本地50000端口的数据服务
        
        Raises:
            ConnectionError: 当连接失败时抛出异常
        """
        try:
            self.manager = PoolManager(address=('127.0.0.1', 50001), authkey=b'cepiec2024')
            self.manager.connect()
            self.service = self.manager.DataService()
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise ConnectionError(f"无法连接到数据服务: {e}")
    
    def get_link_menu_types(self) -> Dict[str, Any]:
        """获取任务类型
        
        从外部数据库获取未翻译的图书标题列表
        
        Args:
            task_id: 任务ID，如果为"0"则获取所有任务的未翻译标题
            
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
                c.id,
                m.link_menu_name,
                t.`name`,
                m.db_name,
                m.table_name 
                FROM
                cpc_task_config c
                LEFT JOIN cpc_task_origin_name_menu m ON c.origin_name_menu_id = m.id
                LEFT JOIN cpc_task_origin_type t ON c.origin_type_id = t.id
            """
            
            logger.debug(f"执行SQL查询: {query}")
            
            result = self.service.execute_sql('task_db', query)
            
            if not result['success']:
                logger.error(f"获取待任务类型失败: {result['error']}")
                return {'success': False, 'error': result['error']}
            
            return {
                'success': True,
                'data': result['data']
            }
        
        except Exception as e:
            logger.error(f"获取待任务类型失败: {e}")
            return {'success': False, 'error': str(e)}

    
    def get_book_result(self,batch_id:str,isbn:str) -> Dict[str, Any]:
        """一般获取图书结果
        
        从外部数据库获取未图书的处理结果
        
        Args:
            batch_id: 批次ID
            isbn: ISBN号码，如果为空则不添加ISBN过滤条件
            
        Returns:
            包含成功状态和数据的字典，格式为：
            {'success': True, 'data': [...]} 或 
            {'success': False, 'error': '错误信息'}
        
        Note:
            由于doris表按create_time分区，查询中添加了create_time条件以利用分区裁剪优化性能
        """
        if not self.service:
            self._connect()
        try:

            # 首先获取任务信息，包括task_id和create_time
            task_info_query="""
                SELECT
                    t.id as task_id,
                    t.create_time 
                    FROM
                    cpc_task_instance t 
                    WHERE
                    t.task_source_code = %s
                    AND t.task_status NOT IN (
                    '12',
                    13)
                    order by t.id desc
                    limit 1
            """
            task_info_result = self.service.execute_sql('task_db', task_info_query, (batch_id,))
            
            if not task_info_result['success'] or not task_info_result['data']:
                logger.error(f"获取任务信息失败: {task_info_result.get('error', '未找到任务')}")
                return {'success': False, 'error': '未找到对应的任务信息'}
            
            task_info = task_info_result['data'][0]
            actual_task_id = task_info['task_id']
            task_create_time = task_info['create_time']

            # 构建基础查询，使用窗口函数去重，按id倒序取最新记录
            # 使用任务的实际create_time作为分区裁剪条件
            query = """
               SELECT 
                isbn,
                final_pass
               FROM (
                   SELECT 
                    COALESCE(b.isbn, b.isbn13, b.pisbn) AS isbn,
                    b.final_pass,
                    ROW_NUMBER() OVER (PARTITION BY COALESCE(b.isbn, b.isbn13, b.pisbn) ORDER BY b.id DESC) as rn
                   FROM
                    cpc_rc_books b 
                   WHERE
                    b.task_id = %s
                    AND b.create_time >= %s
               ) ranked_books
               WHERE rn = 1
            """
            
            # 准备查询参数，使用实际的task_id和create_time
            params = [actual_task_id, task_create_time]
            
            # 如果isbn参数不为空，添加isbn过滤条件到子查询中
            if isbn and isbn.strip():
                # 在子查询的WHERE条件中添加ISBN过滤
                query = query.replace(
                    "WHERE\n                     b.task_id = %s\n                     AND b.create_time >= %s",
                    "WHERE\n                     b.task_id = %s\n                     AND b.create_time >= %s\n                     AND COALESCE(b.isbn, b.isbn13, b.pisbn) = %s"
                )
                params.append(isbn)
            
            logger.debug(f"执行SQL查询: {query}")
            logger.debug(f"查询参数: {params}")
            
            result = self.service.execute_sql('doris-read', query, tuple(params))
            
            if not result['success']:
                logger.error(f"获取图书结果失败: {result['error']}")
                return {'success': False, 'error': result['error']}
            
            return {
                'success': True,
                'data': result['data']
            }
        
        except Exception as e:
            logger.error(f"获取图书结果失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_translated_titles(self, translations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """更新已翻译的图书标题
        
        将翻译后的标题更新到数据库
        
        Args:
            translations: 包含id和翻译后标题的字典列表，格式为：
                         [{'id': 1, 'title_cn_ai': '翻译后的标题'}, ...]
                         
        Returns:
            包含成功状态和结果的字典
        """
        if not self.service:
            self._connect()
        
        try:
            # 构建批量更新SQL
            placeholders = ", ".join(["%s, %s"] * len(translations))
            values = []
            for item in translations:
                values.extend([item['id'], item['title_cn_ai']])
            
            query = f"""
                INSERT INTO cpc_book_registration (id, title_cn_ai)
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE title_cn_ai = VALUES(title_cn_ai)
            """
            
            result = self.service.execute_sql('task_db', query, tuple(values))
            
            if not result['success']:
                logger.error(f"更新翻译标题失败: {result['error']}")
                return {'success': False, 'error': result['error']}
            
            return {
                'success': True,
                'affected_rows': result.get('affected_rows', 0)
            }
            
        except Exception as e:
            logger.error(f"更新翻译标题过程中出错: {e}")
            return {'success': False, 'error': str(e)}