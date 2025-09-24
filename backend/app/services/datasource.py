#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源服务层
"""

import asyncio
import json
import logging
import time
import re
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError, AuthenticationException

from app.models.datasource import (
    Datasource, DatasourceTestLog, DatasourceUsageStats, 
    DatasourcePermission, DatasourceTemplate,
    DatasourceType, DatasourceStatus, TestResult, PermissionType
)
from app.models.data_resource import DataResource
from app.schemas.datasource import (
    DatasourceCreate, DatasourceUpdate, DatasourceFilter,
    DatasourceTestRequest, DatasourceTestResponse,
    DatasourcePermissionCreate, DatasourcePermissionUpdate
)
from app.core.security import encrypt_datasource_password, decrypt_datasource_password
from app.core.exceptions import ValidationError, NotFoundError, PermissionError
from app.core.mysql_pool import mysql_pool_manager


class DatasourceService:
    """数据源服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def create_datasource(self, datasource_data: DatasourceCreate, created_by: int) -> Datasource:
        """创建数据源"""
        # 检查名称是否重复
        existing = await self.db.execute(
            select(Datasource).where(Datasource.name == datasource_data.name)
        )
        if existing.scalar_one_or_none():
            raise ValidationError(f"数据源名称 '{datasource_data.name}' 已存在")
        
        # 加密密码
        encrypted_password = None
        if datasource_data.password:
            encrypted_password = encrypt_datasource_password(datasource_data.password)
        
        # 创建数据源
        datasource = Datasource(
            name=datasource_data.name,
            description=datasource_data.description,
            datasource_type=datasource_data.datasource_type,
            host=datasource_data.host,
            port=datasource_data.port,
            database_name=datasource_data.database_name,
            username=datasource_data.username,
            password=encrypted_password,
            connection_params=datasource_data.connection_params or {},
            pool_config=datasource_data.pool_config or {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600
            },
            is_enabled=datasource_data.is_enabled,
            status=DatasourceStatus.INACTIVE,
            created_by=created_by
        )
        
        self.db.add(datasource)
        await self.db.commit()
        await self.db.refresh(datasource)
        
        return datasource
    
    async def get_datasource(self, datasource_id: int) -> Optional[Datasource]:
        """获取数据源"""
        result = await self.db.execute(
            select(Datasource).where(Datasource.id == datasource_id)
        )
        return result.scalar_one_or_none()
    
    async def get_datasources(
        self, 
        filters: Optional[DatasourceFilter] = None,
        page: int = 1,
        size: int = 20,
        user_id: Optional[int] = None
    ) -> Tuple[List[Datasource], int]:
        """获取数据源列表"""
        query = select(Datasource)
        
        # 应用筛选条件
        if filters:
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        Datasource.name.ilike(search_term),
                        Datasource.description.ilike(search_term),
                        Datasource.host.ilike(search_term)
                    )
                )
            
            if filters.datasource_type:
                query = query.where(Datasource.datasource_type == filters.datasource_type)
            
            if filters.status:
                query = query.where(Datasource.status == filters.status)
            
            if filters.is_enabled is not None:
                query = query.where(Datasource.is_enabled == filters.is_enabled)
            
            if filters.created_by:
                query = query.where(Datasource.created_by == filters.created_by)
        
        # 如果指定了用户ID，只返回该用户有权限的数据源
        if user_id:
            # 这里可以添加权限检查逻辑
            pass
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.order_by(desc(Datasource.created_at))
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        datasources = result.scalars().all()
        
        return list(datasources), total
    
    async def update_datasource(
        self, 
        datasource_id: int, 
        datasource_data: DatasourceUpdate,
        updated_by: int
    ) -> Optional[Datasource]:
        """更新数据源"""
        datasource = await self.get_datasource(datasource_id)
        if not datasource:
            raise NotFoundError(f"数据源 ID {datasource_id} 不存在")
        
        # 检查名称是否重复（排除自己）
        if datasource_data.name and datasource_data.name != datasource.name:
            existing = await self.db.execute(
                select(Datasource).where(
                    and_(
                        Datasource.name == datasource_data.name,
                        Datasource.id != datasource_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValidationError(f"数据源名称 '{datasource_data.name}' 已存在")
        
        # 更新字段
        update_data = datasource_data.dict(exclude_unset=True)
        
        # 处理密码加密
        if 'password' in update_data and update_data['password']:
            update_data['password'] = encrypt_datasource_password(update_data['password'])
        
        for field, value in update_data.items():
            setattr(datasource, field, value)
        
        datasource.updated_by = updated_by
        
        await self.db.commit()
        await self.db.refresh(datasource)
        
        return datasource
    
    async def delete_datasource(self, datasource_id: int) -> bool:
        """删除数据源"""
        datasource = await self.get_datasource(datasource_id)
        if not datasource:
            raise NotFoundError(f"数据源 ID {datasource_id} 不存在")
        
        # 检查是否有关联的权限记录
        permissions_result = await self.db.execute(
            select(DatasourcePermission).where(DatasourcePermission.datasource_id == datasource_id)
        )
        if permissions_result.scalars().first():
            raise ValidationError("无法删除数据源，存在关联的权限记录")
        
        await self.db.delete(datasource)
        await self.db.commit()
        
        return True
    
    async def test_connection(
        self, 
        datasource_id: int, 
        test_request: DatasourceTestRequest,
        tested_by: Optional[int] = None
    ) -> DatasourceTestResponse:
        """测试数据源连接"""
        datasource = await self.get_datasource(datasource_id)
        if not datasource:
            raise NotFoundError(f"数据源 ID {datasource_id} 不存在")
        
        start_time = time.time()
        test_time = datetime.utcnow()
        
        try:
            # 根据数据源类型进行连接测试
            connection_info = await self._test_datasource_connection(
                datasource, test_request.timeout, test_request.test_query
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            # 检查连接信息中是否包含错误
            if "error" in connection_info:
                # 更新数据源状态为错误
                datasource.status = DatasourceStatus.ERROR
                datasource.last_test_time = test_time
                datasource.last_test_result = connection_info.get("message", "连接失败")
                
                # 记录失败的测试日志
                test_log = DatasourceTestLog(
                    datasource_id=datasource_id,
                    test_time=test_time,
                    test_result=TestResult.FAILED,
                    response_time=response_time,
                    error_message=connection_info.get("message", "连接失败"),
                    test_details=connection_info,
                    tested_by=tested_by
                )
                self.db.add(test_log)
                
                await self.db.commit()
                
                return DatasourceTestResponse(
                    success=False,
                    response_time=response_time,
                    message=connection_info.get("message", "连接测试失败"),
                    error_details=connection_info.get("message", "未知错误"),
                    test_time=test_time,
                    connection_info=connection_info
                )
            
            # 连接成功的情况
            # 更新数据源状态
            datasource.status = DatasourceStatus.ACTIVE
            datasource.last_test_time = test_time
            datasource.last_test_result = "连接成功"
            
            # 记录测试日志
            test_log = DatasourceTestLog(
                datasource_id=datasource_id,
                test_time=test_time,
                test_result=TestResult.SUCCESS,
                response_time=response_time,
                test_details=connection_info,
                tested_by=tested_by
            )
            self.db.add(test_log)
            
            await self.db.commit()
            
            return DatasourceTestResponse(
                success=True,
                response_time=response_time,
                message="连接测试成功",
                test_time=test_time,
                connection_info=connection_info
            )
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            error_message = str(e)
            
            # 更新数据源状态
            datasource.status = DatasourceStatus.ERROR
            datasource.last_test_time = test_time
            datasource.last_test_result = f"连接失败: {error_message}"
            
            # 记录测试日志
            test_log = DatasourceTestLog(
                datasource_id=datasource_id,
                test_time=test_time,
                test_result=TestResult.FAILED,
                response_time=response_time,
                error_message=error_message,
                test_details={"error": error_message},
                tested_by=tested_by
            )
            self.db.add(test_log)
            
            await self.db.commit()
            
            return DatasourceTestResponse(
                success=False,
                response_time=response_time,
                message=f"连接测试失败: {error_message}",
                error_details=error_message,
                test_time=test_time
            )
    
    async def test_temp_connection(
        self, 
        datasource_data: DatasourceCreate,
        test_request: DatasourceTestRequest,
        tested_by: Optional[int] = None
    ) -> DatasourceTestResponse:
        """临时测试数据源连接（不保存数据源）"""
        start_time = time.time()
        test_time = datetime.utcnow()
        
        try:
            # 创建临时数据源对象用于测试
            temp_datasource = Datasource(
                name=datasource_data.name,
                datasource_type=datasource_data.datasource_type,
                host=datasource_data.host,
                port=datasource_data.port,
                database_name=datasource_data.database_name,
                username=datasource_data.username,
                password=datasource_data.password,  # 临时使用明文密码
                description=datasource_data.description,
                connection_params=datasource_data.connection_params or {},
                pool_config=datasource_data.pool_config or {},
                is_enabled=True,
                status=DatasourceStatus.INACTIVE
            )
            
            # 根据数据源类型进行连接测试
            connection_info = await self._test_datasource_connection(
                temp_datasource, test_request.timeout, test_request.test_query
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            # 检查连接信息中是否包含错误
            if "error" in connection_info:
                return DatasourceTestResponse(
                    success=False,
                    response_time=response_time,
                    message=connection_info.get("message", "连接测试失败"),
                    error_details=connection_info.get("message", "未知错误"),
                    test_time=test_time,
                    connection_info=connection_info
                )
            
            return DatasourceTestResponse(
                success=True,
                response_time=response_time,
                message="连接测试成功",
                test_time=test_time,
                connection_info=connection_info
            )
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            error_message = str(e)
            
            return DatasourceTestResponse(
                success=False,
                response_time=response_time,
                message=f"连接测试失败: {error_message}",
                error_details=error_message,
                test_time=test_time
            )
    
    async def _test_datasource_connection(
        self, 
        datasource: Datasource, 
        timeout: int,
        test_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """测试数据源连接的具体实现"""
        connection_info = {
            "datasource_type": datasource.datasource_type.value,
            "host": datasource.host,
            "port": datasource.port,
            "database": datasource.database_name
        }
        
        if datasource.datasource_type == DatasourceType.MYSQL:
            return await self._test_mysql_connection(datasource, timeout, test_query)
        elif datasource.datasource_type == DatasourceType.DORIS:
            return await self._test_doris_connection(datasource, timeout, test_query)
        elif datasource.datasource_type == DatasourceType.ORACLE:
            return await self._test_oracle_connection(datasource, timeout, test_query)
        elif datasource.datasource_type == DatasourceType.POSTGRESQL:
            return await self._test_postgresql_connection(datasource, timeout, test_query)
        elif datasource.datasource_type == DatasourceType.SQLSERVER:
            return await self._test_sqlserver_connection(datasource, timeout, test_query)
        elif datasource.datasource_type == DatasourceType.CLICKHOUSE:
            return await self._test_clickhouse_connection(datasource, timeout, test_query)
        elif datasource.datasource_type == DatasourceType.MONGODB:
            return await self._test_mongodb_connection(datasource, timeout, test_query)
        elif datasource.datasource_type == DatasourceType.REDIS:
            return await self._test_redis_connection(datasource, timeout, test_query)
        elif datasource.datasource_type == DatasourceType.ELASTICSEARCH:
            return await self._test_elasticsearch_connection(datasource, timeout, test_query)
        else:
            raise ValidationError(f"不支持的数据源类型: {datasource.datasource_type}")
    
    async def _test_mysql_connection(self, datasource: Datasource, timeout: int, test_query: Optional[str]) -> Dict[str, Any]:
        """测试MySQL连接"""
        import aiomysql
        
        connection = None
        try:
            # 解密密码
            password = decrypt_datasource_password(datasource.password) if datasource.password else None
            
            # 处理连接参数，避免重复的connect_timeout参数
            connection_params = dict(datasource.connection_params or {})
            # 如果connection_params中有connect_timeout，则移除它，使用timeout参数
            connection_params.pop('connect_timeout', None)
            
            # 添加更多连接参数以优化连接管理
            connection_params.update({
                'read_timeout': timeout,
                'write_timeout': timeout,
                'autocommit': True,
                'charset': 'utf8mb4'
            })
            
            connection = await aiomysql.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password=password,
                db=datasource.database_name,
                connect_timeout=timeout,
                **connection_params
            )
            
            async with connection.cursor() as cursor:
                # 执行测试查询
                query = test_query or "SELECT VERSION() as version, NOW() as current_datetime"
                await cursor.execute(query)
                result = await cursor.fetchone()
                
                # 获取服务器信息
                await cursor.execute("SELECT VERSION() as version")
                version_result = await cursor.fetchone()
            
            # 处理查询结果，确保JSON可序列化
            serializable_result = None
            if result:
                serializable_result = []
                for item in result:
                    if isinstance(item, datetime):
                        serializable_result.append(item.isoformat())
                    elif isinstance(item, date):
                        serializable_result.append(item.isoformat())
                    else:
                        serializable_result.append(str(item))
            
            return {
                "connection_type": "MySQL",
                "server_version": version_result[0] if version_result else "Unknown",
                "test_query_result": serializable_result,
                "connection_params": datasource.connection_params
            }
            
        except ImportError:
            raise ValidationError("MySQL驱动未安装，请安装 aiomysql")
        except Exception as e:
            self.logger.error(f"MySQL连接测试失败: {str(e)}")
            raise ValidationError(f"MySQL连接失败: {str(e)}")
        finally:
            # 确保连接正确关闭
            if connection:
                try:
                    connection.close()
                except Exception as e:
                    self.logger.warning(f"关闭MySQL测试连接失败: {str(e)}")
    
    async def _test_doris_connection(self, datasource: Datasource, timeout: int, test_query: Optional[str]) -> Dict[str, Any]:
        """测试Doris连接"""
        # Doris通常使用MySQL协议，可以复用MySQL连接逻辑
        return await self._test_mysql_connection(datasource, timeout, test_query)
    
    async def _test_oracle_connection(self, datasource: Datasource, timeout: int, test_query: Optional[str]) -> Dict[str, Any]:
        """测试Oracle连接"""
        try:
            import cx_Oracle_async
            
            # 构建连接字符串
            dsn = f"{datasource.host}:{datasource.port}/{datasource.database_name}"
            
            conn = await cx_Oracle_async.connect(
                user=datasource.username,
                password="test_password",  # 实际应该解密
                dsn=dsn,
                **datasource.connection_params
            )
            
            cursor = conn.cursor()
            
            # 执行测试查询
            query = test_query or "SELECT * FROM DUAL"
            await cursor.execute(query)
            result = await cursor.fetchone()
            
            # 获取版本信息
            await cursor.execute("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1")
            version_result = await cursor.fetchone()
            
            await cursor.close()
            await conn.close()
            
            return {
                "connection_type": "Oracle",
                "server_version": version_result[0] if version_result else "Unknown",
                "test_query_result": result,
                "connection_params": datasource.connection_params
            }
            
        except ImportError:
            raise ValidationError("Oracle驱动未安装，请安装 cx_Oracle_async")
        except Exception as e:
            raise ValidationError(f"Oracle连接失败: {str(e)}")
    
    async def _test_postgresql_connection(self, datasource: Datasource, timeout: int, test_query: Optional[str]) -> Dict[str, Any]:
        """测试PostgreSQL连接"""
        try:
            import asyncpg
            
            conn = await asyncpg.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password="test_password",  # 实际应该解密
                database=datasource.database_name,
                command_timeout=timeout,
                **datasource.connection_params
            )
            
            # 执行测试查询
            query = test_query or "SELECT version(), now()"
            result = await conn.fetchrow(query)
            
            await conn.close()
            
            return {
                "connection_type": "PostgreSQL",
                "server_version": result[0] if result else "Unknown",
                "test_query_result": dict(result) if result else None,
                "connection_params": datasource.connection_params
            }
            
        except ImportError:
            raise ValidationError("PostgreSQL驱动未安装，请安装 asyncpg")
        except Exception as e:
            raise ValidationError(f"PostgreSQL连接失败: {str(e)}")
    
    async def _test_sqlserver_connection(self, datasource: Datasource, timeout: int, test_query: Optional[str]) -> Dict[str, Any]:
        """测试SQL Server连接"""
        # SQL Server连接测试实现
        return {
            "connection_type": "SQL Server",
            "message": "SQL Server连接测试暂未实现",
            "connection_params": datasource.connection_params
        }
    
    async def _test_clickhouse_connection(self, datasource: Datasource, timeout: int, test_query: Optional[str]) -> Dict[str, Any]:
        """测试ClickHouse连接"""
        # ClickHouse连接测试实现
        return {
            "connection_type": "ClickHouse",
            "message": "ClickHouse连接测试暂未实现",
            "connection_params": datasource.connection_params
        }
    
    async def _test_mongodb_connection(self, datasource: Datasource, timeout: int, test_query: Optional[str]) -> Dict[str, Any]:
        """测试MongoDB连接"""
        # MongoDB连接测试实现
        return {
            "connection_type": "MongoDB",
            "message": "MongoDB连接测试暂未实现",
            "connection_params": datasource.connection_params
        }
    
    async def _test_redis_connection(self, datasource: Datasource, timeout: int, test_query: Optional[str]) -> Dict[str, Any]:
        """测试Redis连接"""
        # Redis连接测试实现
        return {
            "connection_type": "Redis",
            "message": "Redis连接测试暂未实现",
            "connection_params": datasource.connection_params
        }
    
    async def _test_elasticsearch_connection(self, datasource: Datasource, timeout: int, test_query: Optional[str]) -> Dict[str, Any]:
        """测试Elasticsearch连接"""
        try:
            # 创建Elasticsearch客户端 - 适配elasticsearch 8.x版本
            if datasource.username and datasource.password:
                es_client = AsyncElasticsearch(
                    [{
                        'scheme': 'http',
                        'host': datasource.host,
                        'port': datasource.port
                    }],
                    basic_auth=(datasource.username, datasource.password),
                    request_timeout=timeout,
                    max_retries=datasource.connection_params.get('max_retries', 3),
                    retry_on_timeout=True,
                    verify_certs=False
                )
            else:
                es_client = AsyncElasticsearch(
                    [{
                        'scheme': 'http',
                        'host': datasource.host,
                        'port': datasource.port
                    }],
                    request_timeout=timeout,
                    max_retries=datasource.connection_params.get('max_retries', 3),
                    retry_on_timeout=True,
                    verify_certs=False
                )
            
            try:
                # 测试连接 - 获取集群信息
                cluster_info = await es_client.info()
                
                # 获取集群健康状态
                health = await es_client.cluster.health()
                
                # 如果提供了测试查询，执行查询
                query_result = None
                if test_query:
                    try:
                        # 解析测试查询（假设是JSON格式的查询）
                        query_body = json.loads(test_query) if isinstance(test_query, str) else test_query
                        # 执行搜索查询（在所有索引上）
                        query_result = await es_client.search(
                            index="_all",
                            body=query_body,
                            size=1  # 只返回1条记录用于测试
                        )
                    except Exception as query_error:
                        query_result = {"error": f"查询执行失败: {str(query_error)}"}
                
                return {
                    "connection_type": "Elasticsearch",
                    "message": "连接成功",
                    "cluster_info": {
                        "name": cluster_info.get('cluster_name', 'unknown'),
                        "version": cluster_info.get('version', {}).get('number', 'unknown'),
                        "status": health.get('status', 'unknown'),
                        "number_of_nodes": health.get('number_of_nodes', 0),
                        "number_of_data_nodes": health.get('number_of_data_nodes', 0)
                    },
                    "test_query_result": query_result,
                    "connection_params": datasource.connection_params
                }
                
            finally:
                # 关闭客户端连接
                await es_client.close()
                
        except ESConnectionError as e:
            return {
                "connection_type": "Elasticsearch",
                "message": f"连接失败: {str(e)}",
                "error": "CONNECTION_ERROR",
                "connection_params": datasource.connection_params
            }
        except AuthenticationException as e:
            return {
                "connection_type": "Elasticsearch",
                "message": f"认证失败: {str(e)}",
                "error": "AUTHENTICATION_ERROR",
                "connection_params": datasource.connection_params
            }
        except json.JSONDecodeError as e:
            return {
                "connection_type": "Elasticsearch",
                "message": f"测试查询JSON格式错误: {str(e)}",
                "error": "QUERY_FORMAT_ERROR",
                "connection_params": datasource.connection_params
            }
        except Exception as e:
            return {
                "connection_type": "Elasticsearch",
                "message": f"连接测试失败: {str(e)}",
                "error": "UNKNOWN_ERROR",
                "connection_params": datasource.connection_params
            }
    
    async def enable_datasource(self, datasource_id: int) -> bool:
        """启用数据源"""
        datasource = await self.get_datasource(datasource_id)
        if not datasource:
            raise NotFoundError(f"数据源 ID {datasource_id} 不存在")
        
        datasource.is_enabled = True
        await self.db.commit()
        return True
    
    async def disable_datasource(self, datasource_id: int) -> bool:
        """停用数据源"""
        datasource = await self.get_datasource(datasource_id)
        if not datasource:
            raise NotFoundError(f"数据源 ID {datasource_id} 不存在")
        
        datasource.is_enabled = False
        await self.db.commit()
        return True
    
    async def get_datasource_stats(self) -> Dict[str, Any]:
        """获取数据源统计信息"""
        # 总数统计
        total_result = await self.db.execute(select(func.count(Datasource.id)))
        total_count = total_result.scalar()
        
        # 激活数量
        active_result = await self.db.execute(
            select(func.count(Datasource.id)).where(Datasource.status == DatasourceStatus.ACTIVE)
        )
        active_count = active_result.scalar()
        
        # 未激活数量
        inactive_result = await self.db.execute(
            select(func.count(Datasource.id)).where(Datasource.status == DatasourceStatus.INACTIVE)
        )
        inactive_count = inactive_result.scalar()
        
        # 错误数量
        error_result = await self.db.execute(
            select(func.count(Datasource.id)).where(Datasource.status == DatasourceStatus.ERROR)
        )
        error_count = error_result.scalar()
        
        # 类型分布
        type_result = await self.db.execute(
            select(Datasource.datasource_type, func.count(Datasource.id))
            .group_by(Datasource.datasource_type)
        )
        type_distribution = {row[0].value: row[1] for row in type_result.fetchall()}
        
        # 最近测试成功率（最近7天）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_tests_result = await self.db.execute(
            select(DatasourceTestLog.test_result, func.count(DatasourceTestLog.id))
            .where(DatasourceTestLog.test_time >= seven_days_ago)
            .group_by(DatasourceTestLog.test_result)
        )
        
        test_stats = {row[0]: row[1] for row in recent_tests_result.fetchall()}
        total_tests = sum(test_stats.values())
        success_rate = (test_stats.get(TestResult.SUCCESS, 0) / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_count": total_count,
            "active_count": active_count,
            "inactive_count": inactive_count,
            "error_count": error_count,
            "type_distribution": type_distribution,
            "recent_test_success_rate": round(success_rate, 2)
        }
    
    async def get_test_logs(
        self, 
        datasource_id: Optional[int] = None,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[DatasourceTestLog], int]:
        """获取测试日志"""
        query = select(DatasourceTestLog)
        
        if datasource_id:
            query = query.where(DatasourceTestLog.datasource_id == datasource_id)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.order_by(desc(DatasourceTestLog.test_time))
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return list(logs), total
    
    async def get_templates(self, datasource_type: Optional[DatasourceType] = None) -> List[DatasourceTemplate]:
        """获取数据源模板"""
        query = select(DatasourceTemplate)
        
        if datasource_type:
            query = query.where(DatasourceTemplate.datasource_type == datasource_type)
        
        query = query.order_by(DatasourceTemplate.name)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_datasource_schemas(self, datasource_id: int) -> List[Dict[str, Any]]:
        """获取数据源的Schema列表"""
        datasource = await self.get_datasource(datasource_id)
        if not datasource:
            raise NotFoundError(f"数据源 ID {datasource_id} 不存在")
        
        try:
            if datasource.datasource_type == DatasourceType.MYSQL:
                return await self._get_mysql_schemas(datasource)
            elif datasource.datasource_type == DatasourceType.DORIS:
                return await self._get_doris_schemas(datasource)
            elif datasource.datasource_type == DatasourceType.POSTGRESQL:
                return await self._get_postgresql_schemas(datasource)
            elif datasource.datasource_type == DatasourceType.ORACLE:
                return await self._get_oracle_schemas(datasource)
            elif datasource.datasource_type == DatasourceType.SQLSERVER:
                return await self._get_sqlserver_schemas(datasource)
            elif datasource.datasource_type == DatasourceType.ELASTICSEARCH:
                # ES没有Schema概念，返回空列表
                return []
            else:
                return []
        except Exception as e:
            raise ValidationError(f"获取Schema列表失败: {str(e)}")
    
    async def _get_mysql_schemas(self, datasource: Datasource) -> List[Dict[str, Any]]:
        """获取MySQL数据库列表"""
        try:
            # 使用连接池管理器获取连接
            async with mysql_pool_manager.get_connection(datasource) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute("SHOW DATABASES")
                    databases = await cursor.fetchall()
                    
                    schemas = []
                    for db in databases:
                        db_name = db[0]
                        # 过滤系统数据库
                        if db_name not in ['information_schema', 'performance_schema', 'mysql', 'sys']:
                            schemas.append({"name": db_name})
                    
                    return schemas
                
        except Exception as e:
            self.logger.error(f"获取MySQL数据库列表失败: {str(e)}")
            raise ValidationError(f"连接MySQL失败: {str(e)}")
    
    async def _get_doris_schemas(self, datasource: Datasource) -> List[Dict[str, Any]]:
        """获取Doris数据库列表"""
        # Doris使用MySQL协议，可以复用MySQL的逻辑
        return await self._get_mysql_schemas(datasource)
    
    async def _get_postgresql_schemas(self, datasource: Datasource) -> List[Dict[str, Any]]:
        """获取PostgreSQL Schema列表"""
        import asyncpg
        
        try:
            # 解密密码
            password = decrypt_datasource_password(datasource.password) if datasource.password else None
            
            # 建立连接
            connection = await asyncpg.connect(
                host=datasource.host,
                port=datasource.port or 5432,
                user=datasource.username,
                password=password,
                database=datasource.database_name or 'postgres',
                command_timeout=10
            )
            
            try:
                # 查询所有Schema
                query = """
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    ORDER BY schema_name
                """
                rows = await connection.fetch(query)
                
                schemas = []
                for row in rows:
                    schemas.append({"name": row['schema_name']})
                
                return schemas
                
            finally:
                await connection.close()
                
        except Exception as e:
            raise ValidationError(f"连接PostgreSQL失败: {str(e)}")
    
    async def _get_oracle_schemas(self, datasource: Datasource) -> List[Dict[str, Any]]:
        """获取Oracle Schema列表"""
        # Oracle的Schema概念与用户相关，这里返回模拟数据
        return [
            {"name": "HR"},
            {"name": "SCOTT"},
            {"name": "SYS"},
            {"name": "SYSTEM"}
        ]
    
    async def _get_sqlserver_schemas(self, datasource: Datasource) -> List[Dict[str, Any]]:
        """获取SQL Server Schema列表"""
        # SQL Server的Schema，这里返回模拟数据
        return [
            {"name": "dbo"},
            {"name": "guest"},
            {"name": "INFORMATION_SCHEMA"},
            {"name": "sys"}
        ]
    
    async def get_datasource_tables_by_schema(self, datasource_id: int, schema_name: str) -> List[Dict[str, str]]:
        """
        获取指定数据源指定Schema下的表和视图列表
        
        Args:
            datasource_id: 数据源ID
            schema_name: Schema名称
            
        Returns:
            List[Dict[str, str]]: 表和视图列表，每个元素包含name和type字段
        """
        try:
            # 获取数据源信息
            datasource = await self.get_datasource(datasource_id)
            if not datasource:
                raise Exception(f"数据源 {datasource_id} 不存在")
            
            datasource_type = datasource.datasource_type
            
            # 根据数据源类型调用相应的方法
            if datasource_type == DatasourceType.MYSQL:
                return await self._get_mysql_tables_by_schema(datasource, schema_name)
            elif datasource_type == DatasourceType.DORIS:
                return await self._get_doris_tables_by_schema(datasource, schema_name)
            elif datasource_type == DatasourceType.POSTGRESQL:
                return await self._get_postgresql_tables_by_schema(datasource, schema_name)
            elif datasource_type == DatasourceType.ORACLE:
                return await self._get_oracle_tables_by_schema(datasource, schema_name)
            elif datasource_type == DatasourceType.SQLSERVER:
                return await self._get_sqlserver_tables_by_schema(datasource, schema_name)
            elif datasource_type == DatasourceType.ELASTICSEARCH:
                # ES没有Schema概念，直接返回索引列表
                return await self._get_elasticsearch_indices(datasource)
            else:
                raise Exception(f"不支持的数据源类型: {datasource_type}")
                
        except Exception as e:
            raise ValidationError(f"获取表列表失败: {str(e)}")
    
    async def _get_mysql_tables_by_schema(self, datasource, schema_name: str) -> List[Dict[str, str]]:
        """
        获取MySQL指定Schema下的表和视图列表
        """
        try:
            # 使用连接池管理器获取连接
            async with mysql_pool_manager.get_connection(datasource) as connection:
                async with connection.cursor() as cursor:
                    # 切换到指定数据库
                    await cursor.execute(f"USE `{schema_name}`")
                    
                    # 获取表列表
                    await cursor.execute("""
                        SELECT TABLE_NAME, TABLE_TYPE 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = %s
                        ORDER BY TABLE_NAME
                    """, (schema_name,))
                    
                    results = await cursor.fetchall()
                    tables = []
                    
                    for row in results:
                        table_name, table_type = row
                        # 将MySQL的TABLE_TYPE转换为统一格式
                        if table_type == 'BASE TABLE':
                            type_name = 'table'
                        elif table_type == 'VIEW':
                            type_name = 'view'
                        else:
                            type_name = 'table'  # 默认为table
                            
                        tables.append({
                            "name": table_name,
                            "type": type_name
                        })
                    
                    return tables
            
        except Exception as e:
            self.logger.error(f"获取MySQL Schema {schema_name} 下的表列表失败: {str(e)}")
            raise Exception(f"获取MySQL表列表失败: {str(e)}")
    
    async def _get_doris_tables_by_schema(self, datasource, schema_name: str) -> List[Dict[str, str]]:
        """
        获取Doris指定Schema下的表和视图列表
        """
        try:
            import aiomysql
            
            # 解密密码
            decrypted_password = decrypt_datasource_password(datasource.password)
            
            connection = await aiomysql.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password=decrypted_password,
                db=schema_name,
                autocommit=True
            )
            
            cursor = await connection.cursor()
            
            # Doris使用类似MySQL的语法
            await cursor.execute("""
                SELECT TABLE_NAME, TABLE_TYPE 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
            """, (schema_name,))
            
            results = await cursor.fetchall()
            tables = []
            
            for row in results:
                table_name, table_type = row
                if table_type == 'BASE TABLE':
                    type_name = 'table'
                elif table_type == 'VIEW':
                    type_name = 'view'
                else:
                    type_name = 'table'
                    
                tables.append({
                    "name": table_name,
                    "type": type_name
                })
            
            await cursor.close()
            connection.close()
            
            return tables
            
        except Exception as e:
            self.logger.error(f"获取Doris Schema {schema_name} 下的表列表失败: {str(e)}")
            raise Exception(f"获取Doris表列表失败: {str(e)}")
    
    async def _get_postgresql_tables_by_schema(self, datasource, schema_name: str) -> List[Dict[str, str]]:
        """
        获取PostgreSQL指定Schema下的表和视图列表
        """
        try:
            import asyncpg
            
            # 解密密码
            decrypted_password = decrypt_datasource_password(datasource.password)
            
            connection = await asyncpg.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password=decrypted_password,
                database=datasource.database
            )
            
            # 获取表和视图列表
            query = """
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = $1
                ORDER BY table_name
            """
            
            results = await connection.fetch(query, schema_name)
            tables = []
            
            for row in results:
                table_name = row['table_name']
                table_type = row['table_type']
                
                if table_type == 'BASE TABLE':
                    type_name = 'table'
                elif table_type == 'VIEW':
                    type_name = 'view'
                else:
                    type_name = 'table'
                    
                tables.append({
                    "name": table_name,
                    "type": type_name
                })
            
            await connection.close()
            
            return tables
            
        except Exception as e:
            self.logger.error(f"获取PostgreSQL Schema {schema_name} 下的表列表失败: {str(e)}")
            raise Exception(f"获取PostgreSQL表列表失败: {str(e)}")
    
    async def _get_oracle_tables_by_schema(self, datasource, schema_name: str) -> List[Dict[str, str]]:
        """
        获取Oracle指定Schema下的表和视图列表
        """
        try:
            import cx_Oracle
            
            # Oracle连接字符串
            dsn = cx_Oracle.makedsn(datasource.host, datasource.port, service_name=datasource.database)
            connection = cx_Oracle.connect(datasource.username, datasource.password, dsn)
            
            cursor = connection.cursor()
            
            # 获取表列表
            cursor.execute("""
                SELECT table_name, 'table' as table_type 
                FROM all_tables 
                WHERE owner = :schema_name
                UNION ALL
                SELECT view_name as table_name, 'view' as table_type 
                FROM all_views 
                WHERE owner = :schema_name
                ORDER BY table_name
            """, schema_name=schema_name.upper())
            
            results = cursor.fetchall()
            tables = []
            
            for row in results:
                table_name, table_type = row
                tables.append({
                    "name": table_name,
                    "type": table_type
                })
            
            cursor.close()
            connection.close()
            
            return tables
            
        except Exception as e:
            self.logger.error(f"获取Oracle Schema {schema_name} 下的表列表失败: {str(e)}")
            raise Exception(f"获取Oracle表列表失败: {str(e)}")
    
    async def _get_sqlserver_tables_by_schema(self, datasource, schema_name: str) -> List[Dict[str, str]]:
        """
        获取SQL Server指定Schema下的表和视图列表
        """
        try:
            import pyodbc
            
            # SQL Server连接字符串
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={datasource.host},{datasource.port};DATABASE={datasource.database};UID={datasource.username};PWD={datasource.password}"
            connection = pyodbc.connect(conn_str)
            
            cursor = connection.cursor()
            
            # 获取表和视图列表
            cursor.execute("""
                SELECT TABLE_NAME, TABLE_TYPE 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = ?
                ORDER BY TABLE_NAME
            """, schema_name)
            
            results = cursor.fetchall()
            tables = []
            
            for row in results:
                table_name, table_type = row
                if table_type == 'BASE TABLE':
                    type_name = 'table'
                elif table_type == 'VIEW':
                    type_name = 'view'
                else:
                    type_name = 'table'
                    
                tables.append({
                    "name": table_name,
                    "type": type_name
                })
            
            cursor.close()
            connection.close()
            
            return tables
            
        except Exception as e:
            self.logger.error(f"获取SQL Server Schema {schema_name} 下的表列表失败: {str(e)}")
            raise Exception(f"获取SQL Server表列表失败: {str(e)}")
    
    async def _get_elasticsearch_indices(self, datasource) -> List[Dict[str, str]]:
        """
        获取Elasticsearch索引列表
        """
        try:
            from elasticsearch import AsyncElasticsearch
            
            # 设置超时时间（秒）
            timeout = datasource.connection_params.get('timeout', 30) if datasource.connection_params else 30
            
            # 创建ES客户端 - 适配elasticsearch 8.x版本
            if datasource.username and datasource.password:
                es = AsyncElasticsearch(
                    [{
                        'scheme': 'http',
                        'host': datasource.host,
                        'port': datasource.port
                    }],
                    basic_auth=(datasource.username, datasource.password),
                    request_timeout=timeout,
                    max_retries=datasource.connection_params.get('max_retries', 3) if datasource.connection_params else 3,
                    retry_on_timeout=True,
                    verify_certs=False
                )
            else:
                es = AsyncElasticsearch(
                    [{
                        'scheme': 'http',
                        'host': datasource.host,
                        'port': datasource.port
                    }],
                    request_timeout=timeout,
                    max_retries=datasource.connection_params.get('max_retries', 3) if datasource.connection_params else 3,
                    retry_on_timeout=True,
                    verify_certs=False
                )
            
            try:
                # 获取所有索引
                indices = await es.cat.indices(format='json')
                
                tables = []
                for index in indices:
                    # 过滤掉系统索引（以.开头的）
                    index_name = index['index']
                    if not index_name.startswith('.'):
                        tables.append({
                            "name": index_name,
                            "type": "index"  # ES中都是索引
                        })
                
                return tables
                
            finally:
                # 确保关闭客户端连接
                await es.close()
            
        except ESConnectionError as e:
            self.logger.error(f"Elasticsearch连接失败: {str(e)}")
            raise Exception(f"获取Elasticsearch索引列表失败: Connection timed out")
        except Exception as e:
            self.logger.error(f"获取Elasticsearch索引列表失败: {str(e)}")
            raise Exception(f"获取Elasticsearch索引列表失败: {str(e)}")
    
    async def get_elasticsearch_field_mapping(self, datasource_id: int, indices: List[str]) -> List[Dict[str, Any]]:
        """
        获取Elasticsearch字段映射
        """
        try:
            datasource = await self.get_datasource(datasource_id)
            if not datasource:
                raise Exception(f"数据源 ID {datasource_id} 不存在")
            
            return await self._get_elasticsearch_field_mapping(datasource, indices)
            
        except Exception as e:
            self.logger.error(f"获取ES字段映射失败: {str(e)}")
            raise Exception(f"获取ES字段映射失败: {str(e)}")
    
    async def _get_elasticsearch_field_mapping(self, datasource, indices: List[str]) -> List[Dict[str, Any]]:
        """
        获取Elasticsearch字段映射实现
        """
        try:
            from elasticsearch import AsyncElasticsearch
            
            # 创建ES客户端
            if datasource.username and datasource.password:
                es = AsyncElasticsearch(
                    [{
                        'scheme': 'http',
                        'host': datasource.host,
                        'port': datasource.port
                    }],
                    basic_auth=(datasource.username, datasource.password),
                    verify_certs=False
                )
            else:
                es = AsyncElasticsearch(
                    [{
                        'scheme': 'http',
                        'host': datasource.host,
                        'port': datasource.port
                    }],
                    verify_certs=False
                )
            
            fields = []
            
            # 获取每个索引的映射
            for index in indices:
                try:
                    # 获取索引映射
                    mapping_response = await es.indices.get_mapping(index=index)
                    
                    for index_name, index_mapping in mapping_response.items():
                        if 'mappings' in index_mapping and 'properties' in index_mapping['mappings']:
                            properties = index_mapping['mappings']['properties']
                            
                            # 递归解析字段
                            index_fields = self._parse_es_properties(properties, index_name)
                            fields.extend(index_fields)
                            
                except Exception as e:
                    self.logger.warning(f"获取索引 {index} 映射失败: {str(e)}")
                    continue
            
            await es.close()
            
            # 去重并排序
            unique_fields = {}
            for field in fields:
                field_key = f"{field['name']}_{field['type']}"
                if field_key not in unique_fields:
                    unique_fields[field_key] = field
            
            return sorted(list(unique_fields.values()), key=lambda x: x['name'])
            
        except Exception as e:
            self.logger.error(f"获取Elasticsearch字段映射失败: {str(e)}")
            raise Exception(f"获取Elasticsearch字段映射失败: {str(e)}")
    
    def _parse_es_properties(self, properties: Dict[str, Any], index_name: str, parent_path: str = "") -> List[Dict[str, Any]]:
        """
        递归解析ES字段属性
        """
        fields = []
        
        for field_name, field_config in properties.items():
            field_path = f"{parent_path}.{field_name}" if parent_path else field_name
            
            field_info = {
                "name": field_path,
                "type": field_config.get('type', 'object'),
                "index": index_name
            }
            
            # 添加可选属性
            if 'analyzer' in field_config:
                field_info['analyzer'] = field_config['analyzer']
            
            if 'search_analyzer' in field_config:
                field_info['searchAnalyzer'] = field_config['search_analyzer']
            
            if 'format' in field_config:
                field_info['format'] = field_config['format']
            
            if 'index' in field_config:
                field_info['indexable'] = field_config['index']
            
            fields.append(field_info)
            
            # 如果有嵌套属性，递归解析
            if 'properties' in field_config:
                nested_fields = self._parse_es_properties(
                    field_config['properties'], 
                    index_name, 
                    field_path
                )
                fields.extend(nested_fields)
        
        return fields

    async def get_datasource_table_fields(self, datasource_id: int, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        获取指定数据源指定Schema下指定表的字段列表
        
        Args:
            datasource_id: 数据源ID
            schema_name: Schema名称
            table_name: 表名称
            
        Returns:
            字段列表，每个字段包含名称、类型等信息
        """
        datasource = await self.get_datasource(datasource_id)
        if not datasource:
            raise NotFoundError(f"数据源 ID {datasource_id} 不存在")
        
        if datasource.datasource_type == DatasourceType.MYSQL:
            return await self._get_mysql_table_fields(datasource, schema_name, table_name)
        elif datasource.datasource_type == DatasourceType.POSTGRESQL:
            return await self._get_postgresql_table_fields(datasource, schema_name, table_name)
        elif datasource.datasource_type == DatasourceType.ORACLE:
            return await self._get_oracle_table_fields(datasource, schema_name, table_name)
        elif datasource.datasource_type == DatasourceType.SQLSERVER:
            return await self._get_sqlserver_table_fields(datasource, schema_name, table_name)
        elif datasource.datasource_type == DatasourceType.DORIS:
            return await self._get_doris_table_fields(datasource, schema_name, table_name)
        else:
            raise ValidationError(f"不支持的数据源类型: {datasource.datasource_type}")
    
    async def _get_mysql_table_fields(self, datasource: Datasource, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        获取MySQL表字段信息
        """
        import aiomysql
        
        try:
            # 解密密码
            password = decrypt_datasource_password(datasource.password) if datasource.password else None
            
            # 建立连接
            connection = await aiomysql.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password=password,
                db=schema_name,
                charset='utf8mb4'
            )
            
            try:
                cursor = await connection.cursor(aiomysql.DictCursor)
                
                # 查询表字段信息
                query = """
                    SELECT 
                        COLUMN_NAME as name,
                        DATA_TYPE as type,
                        IS_NULLABLE as nullable,
                        COLUMN_DEFAULT as default_value,
                        COLUMN_COMMENT as comment,
                        CHARACTER_MAXIMUM_LENGTH as max_length,
                        NUMERIC_PRECISION as `precision`,
                        NUMERIC_SCALE as scale
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """
                
                await cursor.execute(query, (schema_name, table_name))
                rows = await cursor.fetchall()
                
                fields = []
                for row in rows:
                    field_info = {
                        "name": row['name'],
                        "type": row['type'],
                        "nullable": row['nullable'] == 'YES',
                        "comment": row['comment'] or ""
                    }
                    
                    if row['default_value'] is not None:
                        field_info['default_value'] = row['default_value']
                    
                    if row['max_length'] is not None:
                        field_info['max_length'] = row['max_length']
                    
                    if row['precision'] is not None:
                        field_info['precision'] = row['precision']
                    
                    if row['scale'] is not None:
                        field_info['scale'] = row['scale']
                    
                    fields.append(field_info)
                
                return fields
                
            finally:
                await cursor.close()
                connection.close()
                
        except Exception as e:
            self.logger.error(f"获取MySQL表字段失败: {str(e)}")
            raise Exception(f"获取MySQL表字段失败: {str(e)}")
    
    async def _get_postgresql_table_fields(self, datasource: Datasource, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        获取PostgreSQL表字段信息
        """
        import asyncpg
        
        try:
            # 解密密码
            password = decrypt_datasource_password(datasource.password) if datasource.password else None
            
            # 建立连接
            connection = await asyncpg.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password=password,
                database=datasource.database_name
            )
            
            try:
                # 查询表字段信息
                query = """
                    SELECT 
                        column_name as name,
                        data_type as type,
                        is_nullable,
                        column_default as default_value,
                        character_maximum_length as max_length,
                        numeric_precision as precision,
                        numeric_scale as scale
                    FROM information_schema.columns 
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                """
                
                rows = await connection.fetch(query, schema_name, table_name)
                
                fields = []
                for row in rows:
                    field_info = {
                        "name": row['name'],
                        "type": row['type'],
                        "nullable": row['is_nullable'] == 'YES',
                        "comment": ""
                    }
                    
                    if row['default_value'] is not None:
                        field_info['default_value'] = row['default_value']
                    
                    if row['max_length'] is not None:
                        field_info['max_length'] = row['max_length']
                    
                    if row['precision'] is not None:
                        field_info['precision'] = row['precision']
                    
                    if row['scale'] is not None:
                        field_info['scale'] = row['scale']
                    
                    fields.append(field_info)
                
                return fields
                
            finally:
                await connection.close()
                
        except Exception as e:
            self.logger.error(f"获取PostgreSQL表字段失败: {str(e)}")
            raise Exception(f"获取PostgreSQL表字段失败: {str(e)}")
    
    async def _get_oracle_table_fields(self, datasource: Datasource, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        获取Oracle表字段信息
        """
        # Oracle字段查询实现
        return []
    
    async def _get_sqlserver_table_fields(self, datasource: Datasource, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        获取SQL Server表字段信息
        """
        # SQL Server字段查询实现
        return []
    
    async def _get_doris_table_fields(self, datasource: Datasource, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        获取Doris表字段信息
        
        Args:
            datasource: Doris数据源对象
            schema_name: 数据库名称
            table_name: 表名称
            
        Returns:
            字段列表，每个字段包含名称、类型、是否可空、默认值、注释等信息
        """
        import aiomysql
        
        try:
            # 解密密码
            password = decrypt_datasource_password(datasource.password) if datasource.password else None
            
            # 建立连接 - Doris使用MySQL协议
            connection = await aiomysql.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password=password,
                db=schema_name,
                charset='utf8mb4'
            )
            
            try:
                cursor = await connection.cursor(aiomysql.DictCursor)
                
                # 查询表字段信息 - 使用INFORMATION_SCHEMA
                query = """
                    SELECT 
                        COLUMN_NAME as name,
                        DATA_TYPE as type,
                        IS_NULLABLE as nullable,
                        COLUMN_DEFAULT as default_value,
                        COLUMN_COMMENT as comment,
                        CHARACTER_MAXIMUM_LENGTH as max_length,
                        NUMERIC_PRECISION as `precision`,
                        NUMERIC_SCALE as scale,
                        COLUMN_TYPE as full_type
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """
                
                await cursor.execute(query, (schema_name, table_name))
                rows = await cursor.fetchall()
                
                fields = []
                for row in rows:
                    field_info = {
                        "name": row['name'],
                        "type": row['type'],
                        "full_type": row['full_type'] or row['type'],  # 完整类型信息，包含长度等
                        "nullable": row['nullable'] == 'YES',
                        "comment": row['comment'] or ""
                    }
                    
                    # 添加默认值（如果存在）
                    if row['default_value'] is not None:
                        field_info['default_value'] = row['default_value']
                    
                    # 添加字符类型的最大长度
                    if row['max_length'] is not None:
                        field_info['max_length'] = row['max_length']
                    
                    # 添加数值类型的精度
                    if row['precision'] is not None:
                        field_info['precision'] = row['precision']
                    
                    # 添加数值类型的小数位数
                    if row['scale'] is not None:
                        field_info['scale'] = row['scale']
                    
                    fields.append(field_info)
                
                return fields
                
            finally:
                await cursor.close()
                connection.close()
                
        except Exception as e:
            self.logger.error(f"获取Doris表字段失败 - Schema: {schema_name}, Table: {table_name}, 错误: {str(e)}")
            raise Exception(f"获取Doris表字段失败: {str(e)}")
    
    async def execute_query(
        self,
        datasource: Datasource,
        query: str,
        limit: int = 100,
        timeout: int = 30,
        offset: int = 0,
        enable_pagination: bool = False
    ) -> Dict[str, Any]:
        """
        执行数据源查询
        
        Args:
            datasource: 数据源对象
            query: SQL查询语句
            limit: 结果限制
            timeout: 超时时间（秒）
            offset: 偏移量（用于分页）
            enable_pagination: 是否启用真正的分页（计算总数）
            
        Returns:
            查询结果字典，包含columns、data、row_count、total_count等字段
        """
        try:
            if datasource.datasource_type == DatasourceType.MYSQL:
                return await self._execute_mysql_query(datasource, query, limit, timeout, offset, enable_pagination)
            elif datasource.datasource_type == DatasourceType.POSTGRESQL:
                return await self._execute_postgresql_query(datasource, query, limit, timeout, offset, enable_pagination)
            elif datasource.datasource_type == DatasourceType.DORIS:
                return await self._execute_doris_query(datasource, query, limit, timeout, offset, enable_pagination)
            elif datasource.datasource_type == DatasourceType.ORACLE:
                return await self._execute_oracle_query(datasource, query, limit, timeout, offset, enable_pagination)
            elif datasource.datasource_type == DatasourceType.SQLSERVER:
                return await self._execute_sqlserver_query(datasource, query, limit, timeout, offset, enable_pagination)
            elif datasource.datasource_type == DatasourceType.CLICKHOUSE:
                return await self._execute_clickhouse_query(datasource, query, limit, timeout, offset, enable_pagination)
            else:
                raise ValidationError(f"不支持的数据源类型: {datasource.datasource_type}")
        except Exception as e:
            self.logger.error(f"执行查询失败 - 数据源: {datasource.name}, 错误: {str(e)}")
            raise
    
    async def _execute_mysql_query(
        self,
        datasource: Datasource,
        query: str,
        limit: int,
        timeout: int,
        offset: int = 0,
        enable_pagination: bool = False
    ) -> Dict[str, Any]:
        """
        执行MySQL查询
        
        Args:
            datasource: 数据源对象
            query: SQL查询语句
            limit: 结果限制
            timeout: 超时时间（秒）
            offset: 偏移量（用于分页）
            enable_pagination: 是否启用真正的分页（计算总数）
        """
        try:
            import aiomysql
        except ImportError:
            raise ValidationError("MySQL驱动未安装，请安装 aiomysql")
        
        connection = None
        try:
            # 解密密码
            password = decrypt_datasource_password(datasource.password) if datasource.password else None
            
            # 建立连接参数
            connection_params = {
                'host': datasource.host,
                'port': datasource.port or 3306,
                'user': datasource.username,
                'password': password,
                'connect_timeout': timeout
            }
            
            # 只有当数据库名称存在时才添加db参数
            if datasource.database_name:
                connection_params['db'] = datasource.database_name
            
            # 合并额外的连接参数，但避免重复的connect_timeout
            extra_params = datasource.connection_params.copy() if datasource.connection_params else {}
            if 'connect_timeout' in extra_params:
                del extra_params['connect_timeout']
            connection_params.update(extra_params)
            
            # 建立连接
            connection = await aiomysql.connect(**connection_params)
            
            # 动态选择数据库：优先使用数据资源表中的database_name，其次使用数据源配置的database_name
            target_database = datasource.database_name  # 默认使用数据源配置的数据库
            
            # 从SQL中提取表名，查找是否有特定的数据库配置
            table_names = self._extract_table_names_from_sql(query)
            if table_names:
                # 对于查询中的第一个表，尝试从数据资源表中获取其数据库名称
                first_table = table_names[0]
                resource_database = await self._get_database_name_for_table(datasource.id, first_table)
                if resource_database:
                    target_database = resource_database
                    logging.info(f"表 {first_table} 使用数据资源配置的数据库: {target_database}")
                else:
                    logging.info(f"表 {first_table} 使用数据源默认数据库: {target_database}")
            
            # 如果连接时没有指定数据库，但有目标数据库名称，则使用USE语句
            if target_database:
                async with connection.cursor() as cursor:
                    await cursor.execute(f"USE `{target_database}`")
            
            total_count = 0
            
            # 如果启用分页，先执行COUNT查询获取总数
            if enable_pagination:
                count_query = self._create_count_query(query)
                async with connection.cursor() as cursor:
                    await cursor.execute(count_query)
                    count_result = await cursor.fetchone()
                    total_count = count_result[0] if count_result else 0
            
            # 执行分页查询
            paginated_query = self._add_pagination_to_query(query, limit, offset)
            
            async with connection.cursor() as cursor:
                await cursor.execute(paginated_query)
                
                # 获取列名
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # 获取数据
                rows = await cursor.fetchall()
                
                # 转换数据为可序列化格式
                data = []
                for row in rows:
                    converted_row = []
                    for value in row:
                        if isinstance(value, (datetime, date)):
                            converted_row.append(value.isoformat())
                        elif value is None:
                            converted_row.append(None)
                        else:
                            converted_row.append(str(value))
                    data.append(converted_row)
                
                result = {
                    'columns': columns,
                    'data': data,
                    'row_count': len(data)
                }
                
                # 如果启用分页，添加总数信息
                if enable_pagination:
                    result['total_count'] = total_count
                else:
                    result['total_count'] = len(data)
                
                return result
                
        except Exception as e:
            self.logger.error(f"MySQL查询执行失败: {str(e)}")
            raise ValidationError(f"MySQL查询执行失败: {str(e)}")
        finally:
            if connection:
                try:
                    connection.close()
                except Exception as e:
                    self.logger.warning(f"关闭MySQL连接失败: {str(e)}")
    
    async def _execute_postgresql_query(
        self,
        datasource: Datasource,
        query: str,
        limit: int,
        timeout: int
    ) -> Dict[str, Any]:
        """
        执行PostgreSQL查询
        """
        # PostgreSQL查询实现
        raise ValidationError("PostgreSQL查询功能暂未实现")
    
    async def _execute_doris_query(
        self,
        datasource: Datasource,
        query: str,
        limit: int,
        timeout: int,
        offset: int = 0,
        enable_pagination: bool = False
    ) -> Dict[str, Any]:
        """
        执行Doris查询
        
        Args:
            datasource: Doris数据源对象
            query: SQL查询语句
            limit: 结果限制
            timeout: 超时时间（秒）
            offset: 偏移量（用于分页）
            enable_pagination: 是否启用真正的分页（计算总数）
            
        Returns:
            查询结果字典，包含columns、data、row_count、total_count等字段
        """
        import aiomysql
        
        connection = None
        try:
            # 解密密码
            password = decrypt_datasource_password(datasource.password) if datasource.password else None
            
            # 建立连接 - Doris使用MySQL协议
            connection = await aiomysql.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password=password,
                db=datasource.database_name,
                charset='utf8mb4',
                connect_timeout=timeout
            )
            
            # 从查询中提取表名，用于确定目标数据库
            table_names = self._extract_table_names_from_sql(query)
            target_database = datasource.database_name
            
            # 如果查询中包含表名，尝试从数据资源表中获取对应的数据库名称
            if table_names:
                # 对于查询中的第一个表，尝试从数据资源表中获取其数据库名称
                first_table = table_names[0]
                resource_database = await self._get_database_name_for_table(datasource.id, first_table)
                if resource_database:
                    target_database = resource_database
                    logging.info(f"表 {first_table} 使用数据资源配置的数据库: {target_database}")
                else:
                    logging.info(f"表 {first_table} 使用数据源默认数据库: {target_database}")
            
            # 如果连接时没有指定数据库，但有目标数据库名称，则使用USE语句
            if target_database:
                async with connection.cursor() as cursor:
                    await cursor.execute(f"USE `{target_database}`")
            
            total_count = None
            
            # 如果启用分页，先执行COUNT查询获取总数
            if enable_pagination:
                count_query = self._create_count_query(query)
                async with connection.cursor() as cursor:
                    await cursor.execute(count_query)
                    count_result = await cursor.fetchone()
                    total_count = count_result[0] if count_result else 0
            
            # 执行分页查询
            paginated_query = self._add_pagination_to_query(query, limit, offset)
            
            async with connection.cursor() as cursor:
                await cursor.execute(paginated_query)
                
                # 获取列名
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # 获取数据
                rows = await cursor.fetchall()
                
                # 转换数据为可序列化格式
                data = []
                for row in rows:
                    converted_row = []
                    for value in row:
                        if isinstance(value, (datetime, date)):
                            converted_row.append(value.isoformat())
                        elif value is None:
                            converted_row.append(None)
                        else:
                            converted_row.append(str(value))
                    data.append(converted_row)
                
                result = {
                    'columns': columns,
                    'data': data,
                    'row_count': len(data)
                }
                
                # 如果启用分页，添加总数信息
                if enable_pagination:
                    result['total_count'] = total_count
                
                return result
                
        except Exception as e:
            self.logger.error(f"Doris查询执行失败: {str(e)}")
            raise ValidationError(f"Doris查询执行失败: {str(e)}")
        finally:
            if connection:
                try:
                    connection.close()
                except Exception as e:
                    self.logger.warning(f"关闭Doris连接失败: {str(e)}")
    
    async def _execute_oracle_query(
        self,
        datasource: Datasource,
        query: str,
        limit: int,
        timeout: int
    ) -> Dict[str, Any]:
        """
        执行Oracle查询
        """
        # Oracle查询实现
        raise ValidationError("Oracle查询功能暂未实现")
    
    async def _execute_sqlserver_query(
        self,
        datasource: Datasource,
        query: str,
        limit: int,
        timeout: int
    ) -> Dict[str, Any]:
        """
        执行SQL Server查询
        """
        # SQL Server查询实现
        raise ValidationError("SQL Server查询功能暂未实现")
    
    async def _execute_clickhouse_query(
        self,
        datasource: Datasource,
        query: str,
        limit: int,
        timeout: int
    ) -> Dict[str, Any]:
        """
        执行ClickHouse查询
        """
        # ClickHouse查询实现
        raise ValidationError("ClickHouse查询功能暂未实现")
    
    def _add_limit_to_query(self, query: str, limit: int) -> str:
        """
        为查询添加LIMIT子句（向后兼容方法）
        """
        query = query.strip()
        query_upper = query.upper()
        
        # 如果已经有LIMIT子句，则不添加
        if 'LIMIT' in query_upper:
            return query
        
        # 添加LIMIT子句
        return f"{query} LIMIT {limit}"
    
    def _create_count_query(self, query: str) -> str:
        """
        创建COUNT查询以获取总记录数
        
        Args:
            query: 原始SQL查询
            
        Returns:
            COUNT查询语句
        """
        query = query.strip()
        
        # 移除末尾的分号
        if query.endswith(';'):
            query = query[:-1]
        
        # 将原查询包装为子查询来计算总数
        count_query = f"SELECT COUNT(*) FROM ({query}) AS count_subquery"
        
        return count_query
    
    def _add_pagination_to_query(self, query: str, limit: int, offset: int) -> str:
        """
        为查询添加分页子句（LIMIT和OFFSET）
        
        Args:
            query: 原始SQL查询
            limit: 限制条数
            offset: 偏移量
            
        Returns:
            带分页的SQL查询
        """
        query = query.strip()
        query_upper = query.upper()
        
        # 移除末尾的分号
        if query.endswith(';'):
            query = query[:-1]
        
        # 如果已经有LIMIT子句，先移除它
        if 'LIMIT' in query_upper:
            # 简单的LIMIT移除逻辑，可能需要更复杂的解析
            import re
            query = re.sub(r'\s+LIMIT\s+\d+(\s+OFFSET\s+\d+)?', '', query, flags=re.IGNORECASE)
        
        # 添加新的LIMIT和OFFSET子句
        if offset > 0:
            return f"{query} LIMIT {limit} OFFSET {offset}"
        else:
            return f"{query} LIMIT {limit}"
    
    def _extract_table_names_from_sql(self, sql: str) -> List[str]:
        """
        从SQL查询中提取表名
        """
        # 移除注释和多余空格
        sql = re.sub(r'--.*?\n', ' ', sql)
        sql = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        # 匹配FROM和JOIN后的表名
        pattern = r'(?:FROM|JOIN)\s+`?([a-zA-Z_][a-zA-Z0-9_]*)`?'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        
        return list(set(matches))  # 去重
    
    async def _get_database_name_for_table(self, datasource_id: int, table_name: str) -> Optional[str]:
        """
        根据表名从数据资源表中查找对应的数据库名称
        """
        try:
            # 查询数据资源表中是否有该表的记录
            stmt = select(DataResource.database_name).where(
                and_(
                    DataResource.datasource_id == datasource_id,
                    DataResource.table_name == table_name
                )
            )
            result = await self.db.execute(stmt)
            database_name = result.scalar_one_or_none()
            return database_name
        except Exception as e:
            logging.warning(f"查询表 {table_name} 的数据库名称失败: {e}")
            return None