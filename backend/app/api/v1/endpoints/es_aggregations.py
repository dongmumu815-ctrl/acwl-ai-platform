#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elasticsearch 聚合查询接口
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import AuthenticationException, RequestError, ConnectionError as ESConnectionError

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.datasource import DatasourceService
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ESAggregationsRequest(BaseModel):
    """ES 聚合请求模型"""
    datasourceId: int = Field(..., description="数据源ID")
    indices: List[str] = Field(..., description="索引列表")
    aggregations: Dict[str, Any] = Field(..., description="聚合DSL")
    query: Optional[Dict[str, Any]] = Field(None, description="可选的查询过滤DSL")
    timeout: Optional[str] = Field("30s", description="查询超时时间")


async def _create_es_client(datasource) -> AsyncElasticsearch:
    """创建 ES 客户端（适配 8.x）"""
    if datasource.username and datasource.password:
        return AsyncElasticsearch(
            [{
                'scheme': 'http',
                'host': datasource.host,
                'port': datasource.port
            }],
            basic_auth=(datasource.username, datasource.password),
            verify_certs=False
        )
    else:
        return AsyncElasticsearch(
            [{
                'scheme': 'http',
                'host': datasource.host,
                'port': datasource.port
            }],
            verify_certs=False
        )


@router.post("/aggregations")
async def get_es_aggregations(
    request: ESAggregationsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行 ES 聚合查询
    - 路径: /api/v1/es/aggregations
    """
    try:
        # 获取数据源
        service = DatasourceService(db)
        datasource = await service.get_datasource(request.datasourceId)
        if not datasource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据源 ID {request.datasourceId} 不存在"
            )

        # 创建 ES 客户端
        es_client = await _create_es_client(datasource)

        try:
            body: Dict[str, Any] = {
                "size": 0,
                "aggs": request.aggregations
            }
            # 默认匹配全部，支持传入过滤条件
            body["query"] = request.query or {"match_all": {}}

            # 执行聚合搜索
            response = await es_client.search(
                index=request.indices,
                body=body,
                timeout=request.timeout
            )

            # 组装返回数据（与前端 esQuery.getESAggregations 期望结构一致）
            data = {
                "aggregations": response.get("aggregations", {}),
                "took": response.get("took", 0),
                "hits": {
                    "total": {
                        "value": response.get("hits", {}).get("total", {}).get("value", 0)
                    }
                }
            }

            return {
                "success": True,
                "data": data,
                "message": "聚合查询成功"
            }
        finally:
            await es_client.close()

    except ESConnectionError as e:
        logger.error(f"ES连接失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ES连接失败: {str(e)}"
        )
    except AuthenticationException as e:
        logger.error(f"ES认证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"ES认证失败: {str(e)}"
        )
    except RequestError as e:
        logger.error(f"ES聚合请求错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"聚合请求错误: {str(e)}"
        )
    except Exception as e:
        logger.error(f"ES聚合查询失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聚合查询失败: {str(e)}"
        )