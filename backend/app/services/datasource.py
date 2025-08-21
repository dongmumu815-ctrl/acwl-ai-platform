#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源服务层
"""

import asyncio
import json
import time
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.datasource import (
    Datasource, DatasourceTestLog, DatasourceUsageStats, 
    DatasourcePermission, DatasourceTemplate,
    DatasourceType, DatasourceStatus, TestResult, PermissionType
)
from app.schemas.datasource import (
    DatasourceCreate, DatasourceUpdate, DatasourceFilter,
    DatasourceTestRequest, DatasourceTestResponse,
    DatasourcePermissionCreate, DatasourcePermissionUpdate
)
from app.core.security import encrypt_datasource_password, decrypt_datasource_password
from app.core.exceptions import ValidationError, NotFoundError, PermissionError


class DatasourceService:
    """数据源服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
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
        try:
            import aiomysql
            
            # 解密密码
            password = decrypt_datasource_password(datasource.password) if datasource.password else None
            
            # 处理连接参数，避免重复的connect_timeout参数
            connection_params = dict(datasource.connection_params or {})
            # 如果connection_params中有connect_timeout，则移除它，使用timeout参数
            connection_params.pop('connect_timeout', None)
            
            conn = await aiomysql.connect(
                host=datasource.host,
                port=datasource.port,
                user=datasource.username,
                password=password,
                db=datasource.database_name,
                connect_timeout=timeout,
                **connection_params
            )
            
            async with conn.cursor() as cursor:
                # 执行测试查询
                query = test_query or "SELECT VERSION() as version, NOW() as current_datetime"
                await cursor.execute(query)
                result = await cursor.fetchone()
                
                # 获取服务器信息
                await cursor.execute("SELECT VERSION() as version")
                version_result = await cursor.fetchone()
                
            conn.close()
            
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
            raise ValidationError(f"MySQL连接失败: {str(e)}")
    
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
        # Elasticsearch连接测试实现
        return {
            "connection_type": "Elasticsearch",
            "message": "Elasticsearch连接测试暂未实现",
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