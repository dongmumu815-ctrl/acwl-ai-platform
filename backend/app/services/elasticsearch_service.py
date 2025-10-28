from elasticsearch import AsyncElasticsearch
from typing import Dict, Any, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class ElasticsearchService:
    """Elasticsearch服务类"""
    
    def __init__(self):
        """初始化Elasticsearch客户端"""
        # 从配置中获取Elasticsearch连接信息
        es_host = getattr(settings, 'ELASTICSEARCH_HOST', 'localhost')
        es_port = getattr(settings, 'ELASTICSEARCH_PORT', 9200)
        
        self.client = AsyncElasticsearch(
            hosts=[f"http://{es_host}:{es_port}"],
            # 可以根据需要添加更多配置
        )
    
    async def search(self, index_name: str, query_body: Dict[str, Any]) -> Dict[str, Any]:
        """执行Elasticsearch搜索查询
        
        Args:
            index_name: 索引名称
            query_body: 查询体
            
        Returns:
            查询结果
        """
        try:
            # 新版本elasticsearch客户端使用直接参数而不是body
            result = await self.client.search(
                index=index_name,
                query=query_body.get("query", {"match_all": {}}),
                size=query_body.get("size", 10),
                from_=query_body.get("from", 0),
                source=query_body.get("_source"),
                sort=query_body.get("sort"),
                aggs=query_body.get("aggs")
            )
            return result
        except Exception as e:
            logger.error(f"Elasticsearch查询失败: {e}")
            raise
    
    async def close(self):
        """关闭Elasticsearch客户端连接"""
        if self.client:
            await self.client.close()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()