#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志服务模块

提供API使用日志和数据上传记录的业务逻辑处理功能。

Author: System
Date: 2024
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta
import json
import csv
import io
import uuid
import os
from pathlib import Path

from .base import BaseService
from app.models.log import ApiUsageLog, DataUpload
from app.models.api import CustomApi
from app.models.customer import Customer
from app.core.exceptions import (
    ValidationException,
    BusinessException,
    NotFoundException
)
from app.schemas.log import (
    UsageLogQuery,
    DataUploadQuery,
    UsageStatsResponse,
    UploadStatsResponse,
    DailyStatsResponse,
    HourlyStatsResponse,
    TopApiStatsResponse,
    ErrorAnalysisResponse,
    PerformanceAnalysisResponse,
    LogExportRequest
)
from app.schemas.base import PaginationInfo
from app.core.logging import log_api_access


class ApiUsageLogService(BaseService[ApiUsageLog, dict, dict]):
    """
    API使用日志服务
    
    提供API调用日志的记录、查询和分析功能
    """
    
    def __init__(self):
        super().__init__(ApiUsageLog)
    
    def log_api_call(
        self,
        db: Session,
        customer_id: int,
        api_id: int,
        request_method: str,
        request_url: str,
        request_headers: Optional[Dict] = None,
        request_body: Optional[Dict] = None,
        response_status: int = 200,
        response_headers: Optional[Dict] = None,
        response_time: float = 0.0,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict] = None,
        batch_id: Optional[str] = None,
        file_path: Optional[str] = None,
        timestamp: Optional[str] = None,
        nonce: Optional[str] = None,
        encrypted_data: Optional[str] = None,
        iv: Optional[str] = None,
        signature: Optional[str] = None,
        needread: Optional[bool] = None,
        is_encrypted: bool = False
    ):
        """
        记录API调用日志
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_id: API ID
            request_method: 请求方法
            request_url: 请求URL
            request_headers: 请求头
            request_body: 请求体
            response_status: 响应状态码
            response_headers: 响应头
            response_time: 响应时间（毫秒）
            ip_address: IP地址
            user_agent: 用户代理
            error_message: 错误消息
            error_details: 错误详情
            batch_id: 批次ID（可选）
            file_path: 文件存储路径（可选）
            
        Returns:
            创建的日志记录
        """
        # 生成唯一的请求ID
        import time
        request_id = f"req_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        
        print(f"\n🔍 [日志服务] 开始记录API调用日志...")
        print(f"   请求ID: {request_id}")
        print(f"   客户ID: {customer_id}")
        print(f"   API ID: {api_id}")
        print(f"   批次ID: {batch_id}")
        print(f"   文件路径: {file_path}")
        print(f"   响应状态: {response_status}")
        print(f"   处理时间: {response_time}")
        print(f"   IP地址: {ip_address}")
        print(f"   用户代理: {user_agent}")
        print(f"   错误信息: {error_message}")
        print(f"   加密参数: timestamp={timestamp}, nonce={nonce}, is_encrypted={is_encrypted}")
        
        # 准备日志数据，确保与数据库表结构完全匹配
        log_data = {
            "customer_id": customer_id,
            "api_id": api_id,
            "request_id": request_id,
            "client_ip": ip_address,
            "http_method": request_method,
            "request_url": request_url,
            "request_headers": request_headers,  # 直接传递字典，SQLAlchemy会自动处理JSON序列化
            "file_path": file_path,
            "response_status": response_status,
            "response_headers": response_headers,  # 直接传递字典，SQLAlchemy会自动处理JSON序列化
            "processing_time": response_time,
            "error_message": error_message,
            "error_traceback": json.dumps(error_details, ensure_ascii=False) if error_details else None,
            "batch_id": batch_id,
            "data_size": os.path.getsize(file_path) if file_path and os.path.exists(file_path) else None,
            "record_count": len(request_body) if isinstance(request_body, list) else (1 if request_body else None),
            "user_agent": user_agent,
            # 加密相关字段
            "timestamp": int(timestamp) if timestamp and str(timestamp).isdigit() else None,
            "nonce": nonce,
            "encrypted_data": encrypted_data,
            "iv": iv,
            "signature": signature,
            "needread": bool(needread) if needread is not None else False,
            "is_encrypted": bool(is_encrypted)
        }
        
        print(f"📝 [日志服务] 准备保存的日志数据:")
        print(f"   数据大小: {log_data['data_size']} 字节")
        print(f"   记录数量: {log_data['record_count']}")
        print(f"   最终文件路径: {log_data['file_path']}")
        
        try:
            print(f"💾 [日志服务] 开始调用self.create保存日志记录...")
            
            # 输出即将执行的INSERT语句（模拟）
            print(f"📄 [日志服务] 即将执行的INSERT语句:")
            print(f"   INSERT INTO api_usage_logs (")
            print(f"     customer_id, api_id, request_id, http_method, request_url,")
            print(f"     response_status, batch_id, data_size, record_count, file_path,")
            print(f"     client_ip, processing_time, is_encrypted, created_at")
            print(f"   ) VALUES (")
            print(f"     {log_data.get('customer_id')}, {log_data.get('api_id')}, '{log_data.get('request_id')}',")
            print(f"     '{log_data.get('http_method')}', '{log_data.get('request_url')}',")
            print(f"     {log_data.get('response_status')}, '{log_data.get('batch_id')}',")
            print(f"     {log_data.get('data_size')}, {log_data.get('record_count')}, '{log_data.get('file_path')}',")
            print(f"     '{log_data.get('client_ip')}', {log_data.get('processing_time')},")
            print(f"     {log_data.get('is_encrypted')}, '{log_data.get('created_at')}'")
            print(f"   );")
            
            # 创建日志记录
            log = self.create(db, obj_in=log_data)
            print(f"✅ [日志服务] 日志记录创建成功!")
            print(f"   记录ID: {log.id if hasattr(log, 'id') else 'N/A'}")
            print(f"   请求ID: {log.request_id if hasattr(log, 'request_id') else 'N/A'}")
        except Exception as create_error:
            print(f"❌ [日志服务] 创建日志记录失败: {str(create_error)}")
            print(f"   错误类型: {type(create_error).__name__}")
            raise create_error
        
        # 计算是否成功（基于响应状态码）
        is_success_calculated = 200 <= response_status < 300
        
        # 异步更新统计信息（这里简化为同步）
        self._update_api_stats(db, api_id, is_success_calculated)
        self._update_customer_stats(db, customer_id, is_success_calculated)
        
        # Log to Doris
        log_api_access(
            method=request_method,
            url=request_url,
            status_code=response_status,
            response_time=response_time / 1000,  # Convert ms to seconds
            client_ip=ip_address or 'unknown',
            user_agent=user_agent or 'unknown',
            user_id=str(customer_id),
            error_message=error_message
        )
        
        return log
    
    def get_usage_logs(
        self,
        db: Session,
        query_params: UsageLogQuery,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ApiUsageLog], PaginationInfo]:
        """
        获取使用日志列表
        
        Args:
            db: 数据库会话
            query_params: 查询参数
            page: 页码
            page_size: 每页大小
            
        Returns:
            (日志列表, 分页信息)
        """
        query = db.query(ApiUsageLog)
        
        # 客户过滤
        if query_params.customer_id:
            query = query.filter(ApiUsageLog.customer_id == query_params.customer_id)
        
        # API过滤
        if query_params.api_id:
            query = query.filter(ApiUsageLog.api_id == query_params.api_id)
        
        # 状态过滤
        if query_params.is_success is not None:
            if query_params.is_success:
                query = query.filter(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300))
            else:
                query = query.filter(or_(ApiUsageLog.response_status < 200, ApiUsageLog.response_status >= 300))
        
        # 状态码过滤
        if query_params.status_code:
            query = query.filter(ApiUsageLog.response_status == query_params.status_code)
        
        # IP地址过滤
        if query_params.ip_address:
            query = query.filter(ApiUsageLog.client_ip == query_params.ip_address)
        
        # 日期范围过滤
        if query_params.start_date:
            query = query.filter(ApiUsageLog.created_at >= query_params.start_date)
        
        if query_params.end_date:
            query = query.filter(ApiUsageLog.created_at <= query_params.end_date)
        
        # 响应时间过滤
        if query_params.min_response_time is not None:
            query = query.filter(ApiUsageLog.processing_time >= query_params.min_response_time)
        
        if query_params.max_response_time is not None:
            query = query.filter(ApiUsageLog.processing_time <= query_params.max_response_time)
        
        # 获取总数
        total = query.count()
        
        # 排序
        if query_params.order_by:
            if query_params.order_desc:
                query = query.order_by(desc(getattr(ApiUsageLog, query_params.order_by)))
            else:
                query = query.order_by(asc(getattr(ApiUsageLog, query_params.order_by)))
        else:
            query = query.order_by(desc(ApiUsageLog.created_at))
        
        # 分页
        logs = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 创建分页信息
        pagination = PaginationInfo.create(
            page=page,
            size=page_size,
            total=total
        )
        
        return logs, pagination
    
    def get_usage_stats(
        self,
        db: Session,
        *,
        customer_id: Optional[int] = None,
        api_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageStatsResponse:
        """
        获取使用统计信息
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_id: API ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            使用统计信息
        """
        query = db.query(ApiUsageLog)
        
        # 过滤条件
        if customer_id:
            query = query.filter(ApiUsageLog.customer_id == customer_id)
        
        if api_id:
            query = query.filter(ApiUsageLog.api_id == api_id)
        
        if start_date:
            query = query.filter(ApiUsageLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(ApiUsageLog.created_at <= end_date)
        
        # 基础统计
        total_calls = query.count()
        successful_calls = query.filter(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300)).count()
        failed_calls = total_calls - successful_calls
        
        # 平均响应时间
        avg_response_time = query.with_entities(
            func.avg(ApiUsageLog.processing_time)
        ).scalar() or 0
        
        # 最大响应时间
        max_response_time = query.with_entities(
            func.max(ApiUsageLog.processing_time)
        ).scalar() or 0
        
        # 最小响应时间
        min_response_time = query.with_entities(
            func.min(ApiUsageLog.processing_time)
        ).scalar() or 0
        
        return UsageStatsResponse(
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            success_rate=successful_calls / total_calls if total_calls > 0 else 0,
            avg_response_time=float(avg_response_time),
            max_response_time=float(max_response_time),
            min_response_time=float(min_response_time),
            period_start=start_date,
            period_end=end_date
        )
    
    def get_daily_stats(
        self,
        db: Session,
        *,
        customer_id: Optional[int] = None,
        api_id: Optional[int] = None,
        days: int = 30
    ) -> List[DailyStatsResponse]:
        """
        获取每日统计信息
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_id: API ID
            days: 统计天数
            
        Returns:
            每日统计信息列表
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        query = db.query(
            func.date(ApiUsageLog.created_at).label('date'),
            func.count(ApiUsageLog.id).label('total_calls'),
            func.sum(func.case([(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300), 1)], else_=0)).label('successful_calls'),
            func.avg(ApiUsageLog.processing_time).label('avg_response_time')
        ).filter(
            func.date(ApiUsageLog.created_at) >= start_date,
            func.date(ApiUsageLog.created_at) <= end_date
        )
        
        # 过滤条件
        if customer_id:
            query = query.filter(ApiUsageLog.customer_id == customer_id)
        
        if api_id:
            query = query.filter(ApiUsageLog.api_id == api_id)
        
        # 分组和排序
        results = query.group_by(
            func.date(ApiUsageLog.created_at)
        ).order_by(
            func.date(ApiUsageLog.created_at)
        ).all()
        
        # 转换为响应格式
        daily_stats = []
        for result in results:
            failed_calls = result.total_calls - (result.successful_calls or 0)
            daily_stats.append(DailyStatsResponse(
                date=result.date,
                total_calls=result.total_calls,
                successful_calls=result.successful_calls or 0,
                failed_calls=failed_calls,
                success_rate=(
                    (result.successful_calls or 0) / result.total_calls
                    if result.total_calls > 0 else 0
                ),
                avg_response_time=float(result.avg_response_time or 0)
            ))
        
        return daily_stats
    
    def get_hourly_stats(
        self,
        db: Session,
        *,
        customer_id: Optional[int] = None,
        api_id: Optional[int] = None,
        date: Optional[datetime] = None
    ) -> List[HourlyStatsResponse]:
        """
        获取每小时统计信息
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_id: API ID
            date: 统计日期（默认今天）
            
        Returns:
            每小时统计信息列表
        """
        if not date:
            date = datetime.utcnow().date()
        
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        query = db.query(
            func.extract('hour', ApiUsageLog.created_at).label('hour'),
            func.count(ApiUsageLog.id).label('total_calls'),
            func.sum(func.case([(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300), 1)], else_=0)).label('successful_calls'),
            func.avg(ApiUsageLog.processing_time).label('avg_response_time')
        ).filter(
            ApiUsageLog.created_at >= start_datetime,
            ApiUsageLog.created_at < end_datetime
        )
        
        # 过滤条件
        if customer_id:
            query = query.filter(ApiUsageLog.customer_id == customer_id)
        
        if api_id:
            query = query.filter(ApiUsageLog.api_id == api_id)
        
        # 分组和排序
        results = query.group_by(
            func.extract('hour', ApiUsageLog.created_at)
        ).order_by(
            func.extract('hour', ApiUsageLog.created_at)
        ).all()
        
        # 转换为响应格式
        hourly_stats = []
        for result in results:
            failed_calls = result.total_calls - (result.successful_calls or 0)
            hourly_stats.append(HourlyStatsResponse(
                hour=int(result.hour),
                total_calls=result.total_calls,
                successful_calls=result.successful_calls or 0,
                failed_calls=failed_calls,
                success_rate=(
                    (result.successful_calls or 0) / result.total_calls
                    if result.total_calls > 0 else 0
                ),
                avg_response_time=float(result.avg_response_time or 0)
            ))
        
        return hourly_stats
    
    def get_top_apis(
        self,
        db: Session,
        *,
        customer_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[TopApiStatsResponse]:
        """
        获取热门API统计
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制
            
        Returns:
            热门API统计列表
        """
        query = db.query(
            ApiUsageLog.api_id,
            CustomApi.api_name,
            CustomApi.api_code,
            func.count(ApiUsageLog.id).label('total_calls'),
            func.sum(func.case([(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300), 1)], else_=0)).label('successful_calls'),
            func.avg(ApiUsageLog.processing_time).label('avg_response_time')
        ).join(
            CustomApi, ApiUsageLog.api_id == CustomApi.id
        )
        
        # 过滤条件
        if customer_id:
            query = query.filter(ApiUsageLog.customer_id == customer_id)
        
        if start_date:
            query = query.filter(ApiUsageLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(ApiUsageLog.created_at <= end_date)
        
        # 分组、排序和限制
        results = query.group_by(
            ApiUsageLog.api_id, CustomApi.api_name, CustomApi.api_code
        ).order_by(
            desc(func.count(ApiUsageLog.id))
        ).limit(limit).all()
        
        # 转换为响应格式
        top_apis = []
        for result in results:
            failed_calls = result.total_calls - (result.successful_calls or 0)
            top_apis.append(TopApiStatsResponse(
                api_id=result.api_id,
                api_name=result.api_name,
                api_code=result.api_code,
                total_calls=result.total_calls,
                successful_calls=result.successful_calls or 0,
                failed_calls=failed_calls,
                success_rate=(
                    (result.successful_calls or 0) / result.total_calls
                    if result.total_calls > 0 else 0
                ),
                avg_response_time=float(result.avg_response_time or 0)
            ))
        
        return top_apis
    
    def get_error_analysis(
        self,
        db: Session,
        *,
        customer_id: Optional[int] = None,
        api_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ErrorAnalysisResponse]:
        """
        获取错误分析
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_id: API ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            错误分析列表
        """
        query = db.query(
            ApiUsageLog.response_status,
            ApiUsageLog.error_message,
            func.count(ApiUsageLog.id).label('error_count')
        ).filter(
            or_(ApiUsageLog.response_status < 200, ApiUsageLog.response_status >= 300)
        ).group_by()
        
        # 过滤条件
        if customer_id:
            query = query.filter(ApiUsageLog.customer_id == customer_id)
        
        if api_id:
            query = query.filter(ApiUsageLog.api_id == api_id)
        
        if start_date:
            query = query.filter(ApiUsageLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(ApiUsageLog.created_at <= end_date)
        
        # 分组和排序
        results = query.group_by(
            ApiUsageLog.response_status, ApiUsageLog.error_message
        ).order_by(
            desc(func.count(ApiUsageLog.id))
        ).all()
        
        # 转换为响应格式
        error_analysis = []
        for result in results:
            error_analysis.append(ErrorAnalysisResponse(
                status_code=result.response_status,
                error_message=result.error_message or "未知错误",
                error_count=result.error_count
            ))
        
        return error_analysis
    
    def export_logs(
        self,
        db: Session,
        export_request: LogExportRequest
    ) -> str:
        """
        导出日志
        
        Args:
            db: 数据库会话
            export_request: 导出请求
            
        Returns:
            导出文件路径
        """
        # 构建查询
        query = db.query(ApiUsageLog)
        
        # 应用过滤条件
        if export_request.customer_id:
            query = query.filter(ApiUsageLog.customer_id == export_request.customer_id)
        
        if export_request.api_id:
            query = query.filter(ApiUsageLog.api_id == export_request.api_id)
        
        if export_request.start_date:
            query = query.filter(ApiUsageLog.created_at >= export_request.start_date)
        
        if export_request.end_date:
            query = query.filter(ApiUsageLog.created_at <= export_request.end_date)
        
        if export_request.is_success is not None:
            if export_request.is_success:
                query = query.filter(and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300))
            else:
                query = query.filter(or_(ApiUsageLog.response_status < 200, ApiUsageLog.response_status >= 300))
        
        # 排序
        query = query.order_by(ApiUsageLog.created_at.desc())
        
        # 限制数量
        if export_request.limit:
            query = query.limit(export_request.limit)
        
        # 获取数据
        logs = query.all()
        
        # 生成文件
        if export_request.format == "csv":
            return self._export_to_csv(logs, export_request.fields)
        elif export_request.format == "json":
            return self._export_to_json(logs, export_request.fields)
        else:
            raise ValidationException("不支持的导出格式")
    
    def _export_to_csv(self, logs: List[ApiUsageLog], fields: Optional[List[str]] = None) -> str:
        """
        导出为CSV格式
        
        Args:
            logs: 日志列表
            fields: 导出字段
            
        Returns:
            CSV文件路径
        """
        if not fields:
            fields = [
                "id", "customer_id", "api_id", "request_method", "request_url",
                "response_status", "response_time", "is_success", "ip_address",
                "error_message", "created_at"
            ]
        
        # 创建CSV内容
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        
        for log in logs:
            row = {}
            for field in fields:
                value = getattr(log, field, None)
                if isinstance(value, datetime):
                    value = value.isoformat()
                row[field] = value
            writer.writerow(row)
        
        # 保存文件
        filename = f"api_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = Path("exports") / filename
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(output.getvalue())
        
        return str(file_path)
    
    def _export_to_json(self, logs: List[ApiUsageLog], fields: Optional[List[str]] = None) -> str:
        """
        导出为JSON格式
        
        Args:
            logs: 日志列表
            fields: 导出字段
            
        Returns:
            JSON文件路径
        """
        if not fields:
            fields = [
                "id", "customer_id", "api_id", "request_method", "request_url",
                "response_status", "response_time", "is_success", "ip_address",
                "error_message", "created_at"
            ]
        
        # 创建JSON数据
        data = []
        for log in logs:
            row = {}
            for field in fields:
                value = getattr(log, field, None)
                if isinstance(value, datetime):
                    value = value.isoformat()
                row[field] = value
            data.append(row)
        
        # 保存文件
        filename = f"api_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = Path("exports") / filename
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def _update_api_stats(self, db: Session, api_id: int, is_success: bool) -> None:
        """
        更新API统计信息
        
        Args:
            db: 数据库会话
            api_id: API ID
            is_success: 是否成功
        """
        api = db.query(CustomApi).filter(CustomApi.id == api_id).first()
        if api:
            api.total_calls = (api.total_calls or 0) + 1
            api.last_called_at = datetime.utcnow()
            db.commit()
    
    def _update_customer_stats(self, db: Session, customer_id: int, is_success: bool) -> None:
        """
        更新客户统计信息
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            is_success: 是否成功
        """
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.total_api_calls = (customer.total_api_calls or 0) + 1
            customer.last_api_call_at = datetime.utcnow()
            db.commit()


class DataUploadService(BaseService[DataUpload, dict, dict]):
    """
    数据上传服务
    
    提供数据上传记录的管理功能
    """
    
    def __init__(self):
        super().__init__(DataUpload)
    
    def create_upload_record(
        self,
        db: Session,
        *,
        customer_id: int,
        api_id: int,
        original_filename: str,
        file_size: int,
        file_type: str,
        file_path: str,
        upload_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DataUpload:
        """
        创建数据上传记录
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_id: API ID
            filename: 文件名
            file_size: 文件大小
            file_type: 文件类型
            file_path: 文件路径
            upload_ip: 上传IP
            user_agent: 用户代理
            
        Returns:
            创建的上传记录
        """
        upload_data = {
            "customer_id": customer_id,
            "api_id": api_id,
            "filename": filename,
            "file_size": file_size,
            "file_type": file_type,
            "file_path": file_path,
            "upload_ip": upload_ip,
            "user_agent": user_agent,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        upload = self.create(db, obj_in=upload_data)
        
        self.logger.info(f"Created upload record: {filename} for customer: {customer_id}")
        return upload
    
    def update_upload_status(
        self,
        db: Session,
        upload_id: int,
        status: str,
        processed_records: Optional[int] = None,
        validation_errors: Optional[List[str]] = None,
        error_message: Optional[str] = None
    ) -> DataUpload:
        """
        更新上传状态
        
        Args:
            db: 数据库会话
            upload_id: 上传记录ID
            status: 状态
            processed_records: 处理记录数
            validation_errors: 验证错误
            error_message: 错误消息
            
        Returns:
            更新后的上传记录
        """
        upload = self.get_or_404(db, upload_id)
        
        upload.status = status
        if processed_records is not None:
            upload.processed_records = processed_records
        if validation_errors:
            upload.validation_errors = json.dumps(validation_errors)
        if error_message:
            upload.error_message = error_message
        
        if status == "completed":
            upload.completed_at = datetime.utcnow()
        elif status == "failed":
            upload.failed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(upload)
        
        self.logger.info(f"Updated upload status: {upload.id} -> {status}")
        return upload
    
    def get_upload_stats(
        self,
        db: Session,
        *,
        customer_id: Optional[int] = None,
        api_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UploadStatsResponse:
        """
        获取上传统计信息
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_id: API ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            上传统计信息
        """
        query = db.query(DataUpload)
        
        # 过滤条件
        if customer_id:
            query = query.filter(DataUpload.customer_id == customer_id)
        
        if api_id:
            query = query.filter(DataUpload.api_id == api_id)
        
        if start_date:
            query = query.filter(DataUpload.created_at >= start_date)
        
        if end_date:
            query = query.filter(DataUpload.created_at <= end_date)
        
        # 统计信息
        total_uploads = query.count()
        completed_uploads = query.filter(DataUpload.status == "completed").count()
        failed_uploads = query.filter(DataUpload.status == "failed").count()
        pending_uploads = query.filter(DataUpload.status == "pending").count()
        processing_uploads = query.filter(DataUpload.status == "processing").count()
        
        # 文件大小统计
        total_file_size = query.with_entities(
            func.sum(DataUpload.file_size)
        ).scalar() or 0
        
        # 处理记录数统计
        total_processed_records = query.filter(
            DataUpload.processed_records.isnot(None)
        ).with_entities(
            func.sum(DataUpload.processed_records)
        ).scalar() or 0
        
        return UploadStatsResponse(
            total_uploads=total_uploads,
            completed_uploads=completed_uploads,
            failed_uploads=failed_uploads,
            pending_uploads=pending_uploads,
            processing_uploads=processing_uploads,
            success_rate=completed_uploads / total_uploads if total_uploads > 0 else 0,
            total_file_size=total_file_size,
            total_processed_records=total_processed_records,
            period_start=start_date,
            period_end=end_date
        )
    
    def get_uploads(
        self,
        db: Session,
        query_params: DataUploadQuery,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DataUpload], PaginationInfo]:
        """
        获取上传记录列表
        
        Args:
            db: 数据库会话
            query_params: 查询参数
            page: 页码
            page_size: 每页大小
            
        Returns:
            (上传记录列表, 分页信息)
        """
        query = db.query(DataUpload)
        
        # 过滤条件
        if query_params.customer_id:
            query = query.filter(DataUpload.customer_id == query_params.customer_id)
        
        if query_params.api_id:
            query = query.filter(DataUpload.api_id == query_params.api_id)
        
        if query_params.status:
            query = query.filter(DataUpload.status == query_params.status.value)
        
        if query_params.filename:
            query = query.filter(DataUpload.filename.ilike(f"%{query_params.filename}%"))
        
        if query_params.file_type:
            query = query.filter(DataUpload.file_type == query_params.file_type)
        
        if query_params.start_date:
            query = query.filter(DataUpload.created_at >= query_params.start_date)
        
        if query_params.end_date:
            query = query.filter(DataUpload.created_at <= query_params.end_date)
        
        # 获取总数
        total = query.count()
        
        # 排序和分页
        uploads = query.order_by(desc(DataUpload.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # 创建分页信息
        pagination = PaginationInfo.create(
            page=page,
            size=page_size,
            total=total
        )
        
        return uploads, pagination
    
    def cleanup_old_uploads(
        self,
        db: Session,
        days: int = 30,
        status: str = "completed"
    ) -> int:
        """
        清理旧的上传记录
        
        Args:
            db: 数据库会话
            days: 保留天数
            status: 要清理的状态
            
        Returns:
            清理的记录数
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_uploads = db.query(DataUpload).filter(
            DataUpload.created_at <= cutoff_date,
            DataUpload.status == status
        ).all()
        
        cleaned_count = 0
        for upload in old_uploads:
            # 删除文件（如果存在）
            try:
                file_path = Path(upload.file_path)
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                self.logger.warning(f"Failed to delete file {upload.file_path}: {e}")
            
            # 删除记录
            db.delete(upload)
            cleaned_count += 1
        
        db.commit()
        
        self.logger.info(f"Cleaned up {cleaned_count} old upload records")
        return cleaned_count


class LogService:
    """
    日志服务
    
    提供统一的日志管理功能
    """
    
    def __init__(self):
        self.api_usage_log_service = ApiUsageLogService()
        self.data_upload_service = DataUploadService()
        self.logger = self._get_logger()
    
    def _get_logger(self):
        import logging
        return logging.getLogger(self.__class__.__name__)
    
    def log_api_call(self, db: Session, **kwargs):
        """
        记录API调用日志
        
        Args:
            db: 数据库会话
            **kwargs: 日志参数
            
        Returns:
            日志记录
        """
        return self.api_usage_log_service.log_api_call(db, **kwargs)
    
    def get_usage_logs(self, db: Session, query_params, page: int = 1, page_size: int = 20):
        """
        获取使用日志
        
        Args:
            db: 数据库会话
            query_params: 查询参数
            page: 页码
            page_size: 每页大小
            
        Returns:
            日志列表和分页信息
        """
        return self.api_usage_log_service.get_usage_logs(db, query_params, page, page_size)
    
    def get_upload_logs(self, db: Session, query_params, page: int = 1, page_size: int = 20):
        """
        获取上传日志
        
        Args:
            db: 数据库会话
            query_params: 查询参数
            page: 页码
            page_size: 每页大小
            
        Returns:
            上传日志列表和分页信息
        """
        return self.data_upload_service.get_uploads(db, query_params, page, page_size)
    
    def get_api_logs(self, db: Session, api_id: int, page: int = 1, page_size: int = 20):
        """
        获取特定API的调用日志
        
        Args:
            db: 数据库会话
            api_id: API ID
            page: 页码
            page_size: 每页大小
            
        Returns:
            日志列表和分页信息
        """
        # 查询特定API的日志
        query = db.query(ApiUsageLog).filter(ApiUsageLog.api_id == api_id)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        logs = query.order_by(ApiUsageLog.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # 创建分页信息
        from app.schemas.base import PaginationInfo
        pagination = PaginationInfo.create(
            page=page,
            size=page_size,
            total=total
        )
        
        return logs, pagination


# 全局服务实例
api_usage_log_service = ApiUsageLogService()
data_upload_service = DataUploadService()
log_service = LogService()


if __name__ == "__main__":
    print("日志服务定义完成")