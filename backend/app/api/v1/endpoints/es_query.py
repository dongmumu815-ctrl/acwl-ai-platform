#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elasticsearch查询API接口
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from elasticsearch import AsyncElasticsearch, ConnectionError as ESConnectionError
from elasticsearch.exceptions import AuthenticationException, RequestError

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.datasource import DatasourceService
from app.services.es_query_template import ESQueryTemplateService
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Pydantic模型定义
class ESQueryRequest(BaseModel):
    """ES查询请求模型"""
    datasourceId: int = Field(..., description="数据源ID")
    index: List[str] = Field(..., description="索引名称列表")
    query: Dict[str, Any] = Field(..., description="ES查询DSL")
    size: Optional[int] = Field(100, description="返回结果数量")
    from_: Optional[int] = Field(0, alias="from", description="起始位置")
    sort: Optional[List[Dict[str, Any]]] = Field(None, description="排序条件")
    source: Optional[List[str]] = Field(None, alias="_source", description="返回字段")
    timeout: Optional[str] = Field("30s", description="查询超时时间")
    aggs: Optional[Dict[str, Any]] = Field(None, description="聚合查询")

class ESExportRequest(BaseModel):
    """ES导出请求模型"""
    datasourceId: int = Field(..., description="数据源ID")
    index: List[str] = Field(..., description="索引名称列表")
    query: Dict[str, Any] = Field(..., description="ES查询DSL")
    format: str = Field("csv", description="导出格式")
    size: Optional[int] = Field(10000, description="导出数量")
    source: Optional[List[str]] = Field(None, alias="_source", description="导出字段")

class ESTemplateRequest(BaseModel):
    """ES查询模板请求模型"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    datasourceId: int = Field(..., description="数据源ID")
    indices: List[str] = Field(..., description="索引列表")
    query: Dict[str, Any] = Field(..., description="查询DSL")
    tags: Optional[List[str]] = Field([], description="标签")

class ESExplainRequest(BaseModel):
    """ES查询解释请求模型"""
    index: str = Field(..., description="索引名称")
    query: Dict[str, Any] = Field(..., description="查询DSL")

@router.post("/query")
async def execute_es_query(
    request: ESQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行ES查询
    """
    try:
        # 获取数据源信息
        service = DatasourceService(db)
        datasource = await service.get_datasource(request.datasourceId)
        
        if not datasource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据源 ID {request.datasourceId} 不存在"
            )
        
        # 创建ES客户端
        es_client = await _create_es_client(datasource)
        
        try:
            # 构建查询参数
            search_params = {
                "index": request.index,
                "body": {
                    "query": request.query,
                    "size": request.size,
                    "from": request.from_
                }
            }
            
            # 添加可选参数
            if request.sort:
                search_params["body"]["sort"] = request.sort
            
            if request.source:
                search_params["body"]["_source"] = request.source
            
            if request.aggs:
                search_params["body"]["aggs"] = request.aggs
            
            if request.timeout:
                search_params["timeout"] = request.timeout
            
            # 执行查询
            response = await es_client.search(**search_params)
            
            # 构建统计信息
            stats = {
                "totalHits": response["hits"]["total"]["value"],
                "took": response["took"],
                "maxScore": response["hits"].get("max_score", 0),
                "shardsInfo": {
                    "total": response["_shards"]["total"],
                    "successful": response["_shards"]["successful"],
                    "failed": response["_shards"]["failed"]
                }
            }
            
            return {
                "success": True,
                "data": response,
                "stats": stats,
                "message": f"查询完成，共找到 {stats['totalHits']} 条记录"
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
        logger.error(f"ES查询请求错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"查询请求错误: {str(e)}"
        )
    except Exception as e:
        logger.error(f"ES查询执行失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询执行失败: {str(e)}"
        )

@router.post("/export")
async def export_es_query_result(
    request: ESExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出ES查询结果
    """
    try:
        # 获取数据源信息
        service = DatasourceService(db)
        datasource = await service.get_datasource(request.datasourceId)
        
        if not datasource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据源 ID {request.datasourceId} 不存在"
            )
        
        # 创建ES客户端
        es_client = await _create_es_client(datasource)
        
        try:
            # 构建查询参数
            search_params = {
                "index": request.index,
                "body": {
                    "query": request.query,
                    "size": request.size
                }
            }
            
            if request.source:
                search_params["body"]["_source"] = request.source
            
            # 执行查询
            response = await es_client.search(**search_params)
            
            # 生成导出数据
            if request.format.lower() == "csv":
                return _generate_csv_response(response)
            elif request.format.lower() == "json":
                return _generate_json_response(response)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"不支持的导出格式: {request.format}"
                )
                
        finally:
            await es_client.close()
            
    except Exception as e:
        logger.error(f"ES查询结果导出失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )

@router.post("/templates")
async def save_es_query_template(
    request: ESTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    保存ES查询模板
    """
    try:
        # 创建ES查询模板服务
        template_service = ESQueryTemplateService(db)
        
        # 创建查询模板
        template = await template_service.create_template(
            name=request.name,
            description=request.description,
            datasource_id=request.datasourceId,
            indices=request.indices,
            query=request.query,
            tags=request.tags,
            is_template=getattr(request, 'isTemplate', True),  # 默认为模板
            created_by=current_user.id
        )
        
        return {
            "success": True,
            "data": {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "isTemplate": template.is_template
            },
            "message": "查询模板保存成功"
        }
        
    except ValueError as e:
        logger.error(f"保存ES查询模板参数错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"保存ES查询模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存模板失败: {str(e)}"
        )

@router.get("/templates")
async def get_es_query_templates(
    datasource_id: int = Query(..., description="数据源ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取ES查询模板列表
    """
    try:
        # 创建ES查询模板服务
        template_service = ESQueryTemplateService(db)
        
        # 获取用户的查询模板列表
        templates = await template_service.get_templates(
            datasource_id=datasource_id,
            created_by=current_user.id
        )
        
        # 转换为前端需要的格式
        template_list = []
        for template in templates:
            template_list.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "datasourceId": template.datasource_id,
                "indices": template.indices,
                "query": template.query,
                "tags": template.tags,
                "isTemplate": template.is_template,
                "createdAt": template.created_at.isoformat() if template.created_at else None,
                "updatedAt": template.updated_at.isoformat() if template.updated_at else None
            })
        
        return {
            "success": True,
            "data": template_list,
            "message": "获取模板列表成功"
        }
        
    except Exception as e:
        logger.error(f"获取ES查询模板列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板列表失败: {str(e)}"
        )

@router.get("/fields/{datasource_id}")
async def get_es_field_mapping(
    datasource_id: int,
    indices: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Elasticsearch字段映射
    """
    try:
        # 获取数据源信息
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据源 ID {datasource_id} 不存在"
            )
        
        # 解析索引列表
        index_list = [idx.strip() for idx in indices.split(',') if idx.strip()]
        
        if not index_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="索引名称不能为空"
            )
        
        # 创建ES客户端
        es_client = await _create_es_client(datasource)
        
        try:
            # 获取字段映射
            mapping_response = await es_client.indices.get_mapping(index=index_list)
            
            fields = []
            for index_name, index_data in mapping_response.items():
                if 'mappings' in index_data and 'properties' in index_data['mappings']:
                    properties = index_data['mappings']['properties']
                    for field_name, field_info in properties.items():
                        fields.append({
                            'name': field_name,
                            'type': field_info.get('type', 'unknown'),
                            'index': index_name
                        })
            
            return {
                "success": True,
                "data": {
                    "fields": fields,
                    "total": len(fields)
                },
                "message": "获取字段映射成功"
            }
            
        finally:
            await es_client.close()
            
    except Exception as e:
        logger.error(f"获取ES字段映射失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取字段映射失败: {str(e)}"
        )

@router.delete("/templates/{template_id}")
async def delete_es_query_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除ES查询模板
    """
    try:
        # 创建ES查询模板服务
        template_service = ESQueryTemplateService(db)
        
        # 删除查询模板
        success = await template_service.delete_template(
            template_id=template_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="查询模板不存在或无权限删除"
            )
        
        return {
            "success": True,
            "message": "查询模板删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除ES查询模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除模板失败: {str(e)}"
        )

async def _create_es_client(datasource) -> AsyncElasticsearch:
    """
    创建ES客户端
    """
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

def _generate_csv_response(es_response: Dict[str, Any]) -> StreamingResponse:
    """
    生成CSV格式的响应
    """
    import io
    import csv
    
    def generate_csv():
        output = io.StringIO()
        
        hits = es_response["hits"]["hits"]
        if not hits:
            return
        
        # 获取所有字段名
        all_fields = set()
        for hit in hits:
            if "_source" in hit:
                all_fields.update(hit["_source"].keys())
        
        # 写入CSV头部
        writer = csv.DictWriter(output, fieldnames=list(all_fields))
        writer.writeheader()
        
        # 写入数据行
        for hit in hits:
            if "_source" in hit:
                writer.writerow(hit["_source"])
        
        output.seek(0)
        for line in output:
            yield line
    
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=es_query_result.csv"}
    )

def _generate_json_response(es_response: Dict[str, Any]) -> StreamingResponse:
    """
    生成JSON格式的响应
    """
    def generate_json():
        hits = es_response["hits"]["hits"]
        data = [hit["_source"] for hit in hits if "_source" in hit]
        yield json.dumps(data, ensure_ascii=False, indent=2)
    
    return StreamingResponse(
        generate_json(),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=es_query_result.json"}
    )