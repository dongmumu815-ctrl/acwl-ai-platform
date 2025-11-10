#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API管理服务模块

提供自定义API和API字段的业务逻辑处理功能。

Author: System
Date: 2024
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
import json
import re
import time
from urllib.parse import quote

from .base import BaseService
from app.core.config import settings

# Redis客户端配置
try:
    import redis
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
except ImportError:
    redis_client = None
from app.models.api import CustomApi, ApiField
from app.models.customer import Customer
from app.core.exceptions import (
    ValidationException,
    ConflictException,
    NotFoundException,
    AuthorizationException
)
from app.core.business_codes import BusinessException, BusinessCode, BusinessResponse
from app.schemas.api import (
    CustomApiCreate,
    CustomApiUpdate,
    ApiFieldCreate,
    ApiFieldUpdate,
    HttpMethodEnum,
    ResponseFormatEnum,
    FieldTypeEnum
)
from app.schemas.base import PaginationInfo
from app.services.log import log_service


class CustomApiService(BaseService[CustomApi, CustomApiCreate, CustomApiUpdate]):
    """
    自定义API服务
    
    提供自定义API管理的业务逻辑处理
    """
    
    def __init__(self):
        super().__init__(CustomApi)
    
    def create_api(
        self,
        db: Session,
        api_data: CustomApiCreate,
        customer_id: int,
        created_by: Optional[int] = None
    ) -> CustomApi:
        """
        创建自定义API
        
        Args:
            db: 数据库会话
            api_data: API创建数据
            customer_id: 客户ID
            created_by: 创建者ID
            
        Returns:
            创建的API对象
            
        Raises:
            ConflictException: API代码已存在
            AuthorizationException: 客户无权限创建API
        """
        # 检查客户是否存在且有权限
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise NotFoundException(f"客户 {customer_id} 不存在")
        
        if not customer.can_create_api:
            raise AuthorizationException("客户无权限创建API")
        
        # 检查API代码是否已存在（同一客户下）
        if self.exists(db, filters={
            "customer_id": customer_id,
            "api_code": api_data.api_code
        }):
            raise ConflictException(f"API代码 '{api_data.api_code}' 已存在")
        
        # 验证API代码格式
        if not self._is_valid_api_code(api_data.api_code):
            raise ValidationException("API代码格式不正确，只能包含字母、数字、下划线和连字符")
        
        # 准备创建数据
        create_data = api_data.dict()
        create_data.update({
            "customer_id": customer_id,
            "api_url": f"/api/v1/custom/{customer.app_id}/{api_data.api_code}"
        })
        
        # 创建API
        api = self.create(db, obj_in=create_data)
        
        # 更新客户的API计数
        customer.total_apis = (customer.total_apis or 0) + 1
        db.commit()
        db.refresh(api)
        
        self.logger.info(f"Created API: {api.api_code} for customer: {customer_id}")
        return api
    
    def copy_api(
        self,
        db: Session,
        source_api_id: int,
        target_customer_id: int,
        new_api_code: str,
        new_api_name: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> CustomApi:
        """
        复制API到指定客户
        
        Args:
            db: 数据库会话
            source_api_id: 源API ID
            target_customer_id: 目标客户ID
            new_api_code: 新的API代码
            new_api_name: 新的API名称（可选，默认使用源API名称）
            created_by: 创建者ID
            
        Returns:
            复制的API对象
            
        Raises:
            NotFoundException: 源API或目标客户不存在
            ConflictException: 新API代码已存在
            AuthorizationException: 目标客户无权限创建API
        """
        # 获取源API
        source_api = self.get_or_404(db, source_api_id)
        
        # 检查目标客户是否存在且有权限
        target_customer = db.query(Customer).filter(Customer.id == target_customer_id).first()
        if not target_customer:
            raise NotFoundException(f"目标客户 {target_customer_id} 不存在")
        
        if not target_customer.can_create_api:
            raise AuthorizationException("目标客户无权限创建API")
        
        # 检查新API代码是否已存在（目标客户下）
        if self.exists(db, filters={
            "customer_id": target_customer_id,
            "api_code": new_api_code
        }):
            raise ConflictException(f"API代码 '{new_api_code}' 在目标客户下已存在")
        
        # 验证新API代码格式
        if not self._is_valid_api_code(new_api_code):
            raise ValidationException("API代码格式不正确，只能包含字母、数字、下划线和连字符")
        
        # 准备复制数据
        copy_data = {
            "customer_id": target_customer_id,
            "api_name": new_api_name or f"{source_api.api_name} (复制)",
            "api_code": new_api_code,
            "api_description": source_api.api_description,
            "api_url": f"/api/v1/custom/{target_customer.app_id}/{new_api_code}",
            "http_method": source_api.http_method,
            "status": source_api.status,
            "rate_limit": source_api.rate_limit,
            "require_authentication": source_api.require_authentication,
            "response_format": source_api.response_format
        }
        
        # 创建新API
        new_api = self.create(db, obj_in=copy_data)
        
        # 复制API字段
        source_fields = db.query(ApiField).filter(ApiField.api_id == source_api_id).order_by(ApiField.sort_order).all()
        for source_field in source_fields:
            field_data = {
                "api_id": new_api.id,
                "field_name": source_field.field_name,
                "field_label": source_field.field_label,
                "field_type": source_field.field_type,
                "is_required": source_field.is_required,
                "default_value": source_field.default_value,
                "max_length": source_field.max_length,
                "min_length": source_field.min_length,
                "max_value": source_field.max_value,
                "min_value": source_field.min_value,
                "allowed_values": source_field.allowed_values,
                "validation_regex": source_field.validation_regex,
                "validation_message": source_field.validation_message,
                "sort_order": source_field.sort_order
            }
            
            new_field = ApiField(**field_data)
            db.add(new_field)
        
        # 更新目标客户的API计数
        target_customer.total_apis = (target_customer.total_apis or 0) + 1
        
        db.commit()
        db.refresh(new_api)
        
        self.logger.info(f"Copied API: {source_api.api_code} -> {new_api.api_code} for customer: {target_customer_id}")
        return new_api
    
    def update_api(
        self,
        db: Session,
        api_id: int,
        api_data: CustomApiUpdate,
        customer_id: Optional[int] = None,
        updated_by: Optional[int] = None
    ) -> CustomApi:
        """
        更新自定义API
        
        Args:
            db: 数据库会话
            api_id: API ID
            api_data: 更新数据
            customer_id: 客户ID（用于权限检查）
            updated_by: 更新者ID
            
        Returns:
            更新后的API对象
            
        Raises:
            NotFoundException: API不存在
            AuthorizationException: 无权限更新
            ConflictException: API代码冲突
        """
        api = self.get_or_404(db, api_id)
        
        # 权限检查
        if customer_id and api.customer_id != customer_id:
            raise AuthorizationException("无权限更新此API")
        
        # 处理客户ID更改
        target_customer_id = api_data.customer_id if api_data.customer_id is not None else api.customer_id
        
        # 如果要更改客户ID，验证目标客户是否存在
        if api_data.customer_id and api_data.customer_id != api.customer_id:
            from app.models.customer import Customer
            target_customer = db.query(Customer).filter(Customer.id == api_data.customer_id).first()
            if not target_customer:
                raise NotFoundException(f"目标客户 {api_data.customer_id} 不存在")
        
        # 检查API代码是否冲突（在目标客户下）
        if api_data.api_code and api_data.api_code != api.api_code:
            if self.exists(db, filters={
                "customer_id": target_customer_id,
                "api_code": api_data.api_code,
                "id": {"ne": api_id}
            }):
                raise ConflictException(f"API代码 '{api_data.api_code}' 在目标客户下已存在")
        
        # 更新数据
        update_data = api_data.dict(exclude_unset=True)
        
        # 如果更新了api_code或customer_id，需要重新生成api_url
        if 'api_code' in update_data or 'customer_id' in update_data:
            # 获取目标客户的app_id
            if 'customer_id' in update_data:
                from app.models.customer import Customer
                target_customer = db.query(Customer).filter(Customer.id == target_customer_id).first()
                app_id = target_customer.app_id
            else:
                app_id = api.customer.app_id
            
            api_code = update_data.get('api_code', api.api_code)
            update_data['api_url'] = f"/api/v1/custom/{app_id}/{api_code}"
        
        updated_api = self.update(db, db_obj=api, obj_in=update_data)
        
        # 清除API配置缓存
        from app.api.v1.router import invalidate_api_config_cache
        invalidate_api_config_cache(api.api_code)
        
        self.logger.info(f"Updated API: {api.api_code} (ID: {api.id})")
        return updated_api
    
    def activate_api(self, db: Session, api_id: int, customer_id: Optional[int] = None) -> CustomApi:
        """
        激活API
        
        Args:
            db: 数据库会话
            api_id: API ID
            customer_id: 客户ID（用于权限检查）
            
        Returns:
            更新后的API对象
        """
        api = self.get_or_404(db, api_id)
        
        # 权限检查
        if customer_id and api.customer_id != customer_id:
            raise AuthorizationException("无权限激活此API")
        
        api.status = True
        if hasattr(api, 'activated_at'):
            api.activated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(api)
        
        # 清除API配置缓存
        from app.api.v1.router import invalidate_api_config_cache
        invalidate_api_config_cache(api.api_code)
        
        self.logger.info(f"Activated API: {api.api_code} (ID: {api.id})")
        return api
    
    def deactivate_api(self, db: Session, api_id: int, customer_id: Optional[int] = None) -> CustomApi:
        """
        停用API
        
        Args:
            db: 数据库会话
            api_id: API ID
            customer_id: 客户ID（用于权限检查）
            
        Returns:
            更新后的API对象
        """
        api = self.get_or_404(db, api_id)
        
        # 权限检查
        if customer_id and api.customer_id != customer_id:
            raise AuthorizationException("无权限停用此API")
        
        api.status = False
        if hasattr(api, 'deactivated_at'):
            api.deactivated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(api)
        
        # 清除API配置缓存
        from app.api.v1.router import invalidate_api_config_cache
        invalidate_api_config_cache(api.api_code)
        
        self.logger.info(f"Deactivated API: {api.api_code} (ID: {api.id})")
        return api
    
    def get_customer_apis(
        self,
        db: Session,
        customer_id: int,
        *,
        is_active: Optional[bool] = None,
        http_method: Optional[HttpMethodEnum] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[CustomApi], PaginationInfo]:
        """
        获取客户的API列表
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            is_active: 是否激活
            http_method: HTTP方法
            page: 页码
            page_size: 每页大小
            
        Returns:
            (API列表, 分页信息)
        """
        filters = {"customer_id": customer_id}
        
        if is_active is not None:
            filters["is_active"] = is_active
        
        if http_method:
            filters["http_method"] = http_method.value
        
        return self.get_paginated(
            db,
            page=page,
            page_size=page_size,
            filters=filters,
            order_by="created_at",
            order_desc=True
        )
    
    def search_apis(
        self,
        db: Session,
        *,
        keyword: Optional[str] = None,
        customer_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        http_method: Optional[HttpMethodEnum] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[CustomApi], PaginationInfo]:
        """
        搜索API
        
        Args:
            db: 数据库会话
            keyword: 关键词（API名称、代码、描述）
            customer_id: 客户ID
            is_active: 是否激活
            http_method: HTTP方法
            created_after: 创建时间之后
            created_before: 创建时间之前
            page: 页码
            page_size: 每页大小
            
        Returns:
            (API列表, 分页信息)
        """
        query = db.query(CustomApi)
        
        # 关键词搜索
        if keyword:
            search_filter = or_(
                CustomApi.api_name.ilike(f"%{keyword}%"),
                CustomApi.api_code.ilike(f"%{keyword}%"),
                CustomApi.description.ilike(f"%{keyword}%")
            )
            query = query.filter(search_filter)
        
        # 客户过滤
        if customer_id:
            query = query.filter(CustomApi.customer_id == customer_id)
        
        # 状态过滤
        if is_active is not None:
            query = query.filter(CustomApi.status == is_active)
        
        if http_method:
            query = query.filter(CustomApi.http_method == http_method.value)
        
        # 日期过滤
        if created_after:
            query = query.filter(CustomApi.created_at >= created_after)
        
        if created_before:
            query = query.filter(CustomApi.created_at <= created_before)
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        apis = query.order_by(CustomApi.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # 创建分页信息
        pagination = PaginationInfo.create(
            page=page,
            size=page_size,
            total=total
        )
        
        return apis, pagination
    
    def get_api_by_code(
        self,
        db: Session,
        customer_id: int,
        api_code: str
    ) -> Optional[CustomApi]:
        """
        根据客户ID和API代码获取API
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            api_code: API代码
            
        Returns:
            API对象或None
        """
        return db.query(CustomApi).filter(
            CustomApi.customer_id == customer_id,
            CustomApi.api_code == api_code
        ).first()
    
    def increment_call_count(
        self,
        db: Session,
        api_id: int,
        success: bool = True
    ) -> None:
        """
        增加API调用计数
        
        Args:
            db: 数据库会话
            api_id: API ID
            success: 是否成功调用
        """
        api = db.query(CustomApi).filter(CustomApi.id == api_id).first()
        if api:
            api.total_calls = (api.total_calls or 0) + 1
            api.last_called_at = datetime.utcnow()
            db.commit()
    
    def get_api_stats(
        self,
        db: Session,
        api_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取API统计信息
        
        Args:
            db: 数据库会话
            api_id: API ID
            days: 统计天数
            
        Returns:
            统计信息
        """
        api = self.get_or_404(db, api_id)
        
        # 计算日期范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 从日志表计算成功和失败次数
        from .log import ApiUsageLog
        from sqlalchemy import and_
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 查询指定时间段内的调用统计
        total_calls_in_period = db.query(ApiUsageLog).filter(
            and_(
                ApiUsageLog.api_id == api.id,
                ApiUsageLog.created_at >= start_date
            )
        ).count()
        
        successful_calls_in_period = db.query(ApiUsageLog).filter(
            and_(
                ApiUsageLog.api_id == api.id,
                ApiUsageLog.created_at >= start_date,
                ApiUsageLog.response_status >= 200,
                ApiUsageLog.response_status < 300
            )
        ).count()
        
        failed_calls_in_period = total_calls_in_period - successful_calls_in_period
        
        # 基础统计
        stats = {
            "api_id": api.id,
            "api_name": api.api_name,
            "api_code": api.api_code,
            "total_calls": api.total_calls or 0,
            "successful_calls": successful_calls_in_period,
            "failed_calls": failed_calls_in_period,
            "success_rate": (
                successful_calls_in_period / total_calls_in_period
                if total_calls_in_period > 0
                else 0
            ),
            "last_called_at": api.last_called_at,
            "is_active": api.status,
            "rate_limit": api.rate_limit,
            "period_days": days
        }
        
        # 这里可以添加更详细的统计查询（从日志表）
        # 例如：每日调用量、错误分析、响应时间等
        
        return stats
    
    def delete_api(
        self,
        db: Session,
        api_id: int,
        customer_id: Optional[int] = None
    ) -> None:
        """
        删除API
        
        Args:
            db: 数据库会话
            api_id: API ID
            customer_id: 客户ID（用于权限检查）
            
        Raises:
            NotFoundException: API不存在
            AuthorizationException: 无权限删除
        """
        api = self.get_or_404(db, api_id)
        
        # 权限检查
        if customer_id and api.customer_id != customer_id:
            raise AuthorizationException("无权限删除此API")
        
        # 删除API
        self.delete(db, id=api_id)
        
        # 清除相关字段缓存
        api_field_service._invalidate_cache(api_id)
        
        # 清除API配置缓存
        from app.api.v1.router import invalidate_api_config_cache
        invalidate_api_config_cache(api.api_code)
        
        # 更新客户的API计数
        customer = db.query(Customer).filter(Customer.id == api.customer_id).first()
        if customer:
            customer.total_apis = max(0, (customer.total_apis or 1) - 1)
            db.commit()
        
        self.logger.info(f"Deleted API: {api.api_code} (ID: {api.id})")
    
    def toggle_api_status(
        self,
        db: Session,
        api_id: int,
        customer_id: Optional[int] = None
    ) -> CustomApi:
        """
        切换API状态
        
        Args:
            db: 数据库会话
            api_id: API ID
            customer_id: 客户ID（用于权限检查）
            
        Returns:
            更新后的API对象
            
        Raises:
            NotFoundException: API不存在
            AuthorizationException: 无权限操作
        """
        api = self.get_or_404(db, api_id)
        
        # 权限检查
        if customer_id and api.customer_id != customer_id:
            raise AuthorizationException("无权限操作此API")
        
        # 切换状态：status字段 1-开放，0-停用
        api.status = not api.status
        
        # 更新时间戳字段（如果存在）
        if hasattr(api, 'activated_at') and hasattr(api, 'deactivated_at'):
            if api.status:
                api.activated_at = datetime.utcnow()
            else:
                api.deactivated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(api)
        
        # 清除API配置缓存
        from app.api.v1.router import invalidate_api_config_cache
        invalidate_api_config_cache(api.api_code)
        
        status_text = "激活" if api.status else "停用"
        self.logger.info(f"{status_text} API: {api.api_code} (ID: {api.id})")
        return api
    
    def check_rate_limit(
        self,
        db: Session,
        api_id: int,
        time_window: int = 3600  # 1小时
    ) -> Tuple[bool, int, int]:
        """
        检查API频率限制
        
        Args:
            db: 数据库会话
            api_id: API ID
            time_window: 时间窗口（秒）
            
        Returns:
            (是否允许调用, 当前调用次数, 限制次数)
        """
        api = self.get_or_404(db, api_id)
        
        if not api.rate_limit:
            return True, 0, 0
        
        # 计算时间窗口
        window_start = datetime.utcnow() - timedelta(seconds=time_window)
        
        # 这里需要查询日志表来获取实际的调用次数
        # 暂时使用简化逻辑
        current_calls = 0  # 从日志表查询
        
        allowed = current_calls < api.rate_limit
        return allowed, current_calls, api.rate_limit
    
    def _is_valid_api_code(self, api_code: str) -> bool:
        """
        验证API代码格式
        
        Args:
            api_code: API代码
            
        Returns:
            是否有效
        """
        # API代码规则：3-50个字符，只能包含字母、数字、下划线和连字符
        pattern = r'^[a-zA-Z][a-zA-Z0-9_-]{2,49}$'
        return bool(re.match(pattern, api_code))
    
    def log_api_call(
        self,
        db: Session,
        api_config: CustomApi,
        ip_address: Optional[str],
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        is_success: bool,
        batch_id: Optional[str] = None,
        file_path: Optional[str] = None,
        timestamp: Optional[str] = None,
        nonce: Optional[str] = None,
        encrypted_data: Optional[str] = None,
        iv: Optional[str] = None,
        signature: Optional[str] = None,
        needread: Optional[bool] = None,
        is_encrypted: bool = False
    ) -> None:
        """
        记录API调用日志
        
        Args:
            db: 数据库会话
            api_config: API配置对象
            ip_address: 客户端IP地址
            request_data: 请求数据
            response_data: 响应数据
            is_success: 是否成功
            batch_id: 批次ID（可选）
            file_path: 文件存储路径（可选）
            timestamp: 时间戳（加密请求）
            nonce: 随机数（加密请求）
            encrypted_data: 加密数据（加密请求）
            iv: 初始化向量（加密请求）
            signature: 数据签名（加密请求）
            needread: 是否需要读取（加密请求）
            is_encrypted: 是否为加密请求
        """
        try:
            # 获取API信息
            api = api_config
            if not api:
                print(f"⚠️ [API服务] API配置为空，跳过日志记录")
                return
            
            print(f"🔄 [API服务] 开始记录API调用日志...")
            print(f"   API名称: {api.api_name if hasattr(api, 'api_name') else 'Unknown API'}")
            print(f"   API代码: {api.api_code if hasattr(api, 'api_code') else 'N/A'}")
            print(f"   客户ID: {api.customer_id if hasattr(api, 'customer_id') else 'N/A'}")
            print(f"   API ID: {api.id if hasattr(api, 'id') else 'N/A'}")
            print(f"   批次ID: {batch_id}")
            print(f"   文件路径: {file_path}")
            print(f"   是否成功: {is_success}")
            
            # 记录API调用信息到日志
            self.logger.debug(f"Processing API call for: {api.api_name if hasattr(api, 'api_name') else 'Unknown API'}")
            
            print(f"📞 [API服务] 调用log_service.log_api_call...")
            # 调用日志服务记录日志（包含batch_id和加密参数）
            log_service.log_api_call(
                db,
                customer_id=api.customer_id,
                api_id=api.id,
                request_method=api.http_method,
                request_url=f"/api/v1/{api.api_code}",
                request_headers=None,
                request_body=request_data,
                response_status=200 if is_success else 500,
                response_headers=None,
                response_time=0.0,  # 这里可以传入实际的响应时间
                ip_address=ip_address,
                user_agent=None,
                error_message=None if is_success else "API调用失败",
                error_details=None if is_success else response_data,
                batch_id=batch_id,  # 添加批次ID
                file_path=file_path,  # 添加文件路径
                timestamp=timestamp,
                nonce=nonce,
                encrypted_data=encrypted_data,
                iv=iv,
                signature=signature,
                needread=needread,
                is_encrypted=is_encrypted
            )
            print(f"✅ [API服务] log_service.log_api_call调用成功!")
        except Exception as e:
             print(f"❌ [API服务] 记录API调用日志失败: {str(e)}")
             print(f"   错误类型: {type(e).__name__}")
             import traceback
             print(f"   错误堆栈: {traceback.format_exc()}")
             self.logger.error(f"Failed to log API call: {e}")

    def validate_business_rules(self, db: Session, obj_data: Dict[str, Any]) -> None:
        """
        验证API业务规则
        
        Args:
            db: 数据库会话
            obj_data: 对象数据
            
        Raises:
            BusinessException: 业务规则验证失败
        """
        # 检查API代码格式
        api_code = obj_data.get("api_code")
        if api_code and not self._is_valid_api_code(api_code):
            raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "API代码格式不正确")
        
        # 检查频率限制
        rate_limit = obj_data.get("rate_limit")
        if rate_limit and (rate_limit < 1 or rate_limit > 10000):
            raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "频率限制必须在1-10000之间")
        
        # 检查响应格式
        response_format = obj_data.get("response_format")
        if response_format and response_format not in [fmt.value for fmt in ResponseFormatEnum]:
            raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "不支持的响应格式")
    
    def get_with_fields(self, db: Session, api_id: int) -> Optional[CustomApi]:
        """
        获取API详细信息（包含字段定义）
        
        Args:
            db: 数据库会话
            api_id: API ID
            
        Returns:
            API对象（包含字段信息）
        """
        api = db.query(CustomApi).filter(CustomApi.id == api_id).first()
        if api:
            # 预加载字段信息
            api.fields = db.query(ApiField).filter(
                ApiField.api_id == api_id
            ).order_by(ApiField.sort_order).all()
        return api
    
    def generate_documentation(self, db: Session, api: CustomApi, format: str = "markdown") -> str:
        """
        生成API文档
        
        Args:
            db: 数据库会话
            api: API对象
            format: 文档格式（markdown/html/json）
            
        Returns:
            生成的文档内容
        """

        if format == "markdown":
            return self._generate_markdown_documentation(api)
        elif format == "html":
            return self._generate_html_documentation(api)
        elif format == "json":
            return self._generate_json_documentation(api)
        else:
            raise ValueError(f"不支持的文档格式: {format}")
    
    def _generate_markdown_documentation(self, api: CustomApi) -> str:
        """
        生成Markdown格式的API文档
        
        Args:
            api: API对象
            
        Returns:
            Markdown文档内容
        """
        doc = []
        print("goooooooooooooooooooooooooooood1")
        # 文档标题和徽章
        doc.append(f"# 📋 {api.api_name} API文档")
        doc.append("")
        
        # 状态徽章
        status_badge = "🟢 启用" if api.status else "🔴 禁用"
        method_emoji = {
            "GET": "🔍",
            "POST": "📝", 
            "PUT": "✏️",
            "DELETE": "🗑️",
            "PATCH": "🔧"
        }.get(api.http_method, "📡")
        
        doc.append(f"**状态**: {status_badge} | **方法**: {method_emoji} `{api.http_method}` | **认证**: {'🔐 需要' if api.require_authentication else '🔓 无需'}")
        doc.append("")
        
        # 目录
        doc.append("## 📑 目录")
        doc.append("")
        doc.append("- [📋 基本信息](#基本信息)")
        if self._is_data_upload_api(api):
            doc.append("- [🔐 数据加密说明](#数据加密说明)")
        doc.append("- [📤 请求示例](#请求示例)")
        if hasattr(api, 'fields') and api.fields:
            doc.append("- [📝 字段说明](#字段说明)")
        doc.append("- [📥 响应示例](#响应示例)")
        doc.append("- [⚠️ 错误码说明](#错误码说明)")
        doc.append("- [🔧 SDK示例](#SDK示例)")
        doc.append("  - [Python示例](#python示例)")
        doc.append("  - [Java示例](#java示例)")
        doc.append("")
        doc.append("---")
        doc.append("")
        
        # 基本信息
        doc.append("## 📋 基本信息")
        doc.append("")
        doc.append("| 属性 | 值 |")
        doc.append("|------|-------|")
        doc.append(f"| **API名称** | `{api.api_name}` |")
        doc.append(f"| **API代码** | `{api.api_code}` |")
        doc.append(f"| **HTTP方法** | `{api.http_method}` |")
        doc.append(f"| **API URL** | `{api.api_url}` |")
        doc.append(f"| **完整路径** | `/api/v1/{{batch_id}}/{api.api_code}` |")
        doc.append(f"| **状态** | {status_badge} |")
        if api.api_description:
            doc.append(f"| **描述** | {api.api_description} |")
        if api.rate_limit:
            doc.append(f"| **频率限制** | ⏱️ {api.rate_limit} 次/分钟 |")
        doc.append(f"| **需要认证** | {'🔐 是' if api.require_authentication else '🔓 否'} |")
        doc.append("")
        print("goooooooooooooooooooooooooooood11")
        # 检查是否为数据上传接口，添加加密说明
        if self._is_data_upload_api(api):
            print("goooooooooooooooooooooooooooood22")
            doc.extend(self._generate_encryption_section())
            doc.append("")
        
        # 请求示例
        doc.append("## 📤 请求示例")
        doc.append("")
        # 使用正确的API路径格式
        correct_api_path = f"/api/v1/{{batch_id}}/{api.api_code}"
        doc.append("> **接口地址**")
        doc.append(f"> `{api.http_method} {correct_api_path}`")
        doc.append("")
        doc.append("### HTTP 请求头")
        doc.append("")
        doc.append("```http")
        doc.append(f"{api.http_method} {correct_api_path} HTTP/1.1")
        doc.append("Host: your-domain.com")
        doc.append("Content-Type: application/json")
        if api.require_authentication:
            doc.append("Authorization: Bearer <your_access_token>")
        doc.append("```")
        doc.append("")
        
        # 生成请求体示例
        if hasattr(api, 'fields') and api.fields:
            doc.append("### 请求体示例")
            doc.append("")
            
            # 普通请求示例
            doc.append("#### 普通请求")
            doc.append("")
            example_data = {}
            for field in api.fields:
                example_data[field.field_name] = self._get_field_example_value(field)
            
            import json
            doc.append("```json")
            doc.append(json.dumps(example_data, indent=2, ensure_ascii=False))
            doc.append("```")
            doc.append("")
            
            # 如果是数据上传API，添加加密请求示例
            if self._is_data_upload_api(api):
                doc.append("#### 加密请求")
                doc.append("")
                doc.append("> **说明**: 业务数据需要先加密，然后放入`data`字段中")
                doc.append("")
                doc.append("**原始业务数据**:")
                doc.append("```json")
                doc.append(json.dumps(example_data, indent=2, ensure_ascii=False))
                doc.append("```")
                doc.append("")
                doc.append("**加密后的请求体**:")
                encrypted_example = {
                    "timestamp": "1640995200000",
                    "nonce": "abc123def456",
                    "data": "base64_encoded_encrypted_business_data_here",
                    "iv": "base64_encoded_iv_here",
                    "signature": "hmac_sha256_signature_here",
                    "needread": False
                }
                doc.append("```json")
                doc.append(json.dumps(encrypted_example, indent=2, ensure_ascii=False))
                doc.append("```")
                doc.append("")
                doc.append("> **注意**: `data`字段包含的是加密后的业务数据，不是原始的业务字段")
                doc.append("")
        doc.append("")
        
        # 字段说明
        if hasattr(api, 'fields') and api.fields:
            doc.append("## 📝 字段说明")
            doc.append("")
            
            # 普通请求字段说明
            doc.append("### 普通请求字段")
            doc.append("")
            doc.append("| 字段名 | 标签 | 类型 | 必填 | 描述 | 验证规则 |")
            doc.append("|:-------|:-----|:-----|:-----|:-----|:---------|")
            
            for field in api.fields:
                required_icon = "✅" if field.is_required else "❌"
                required_text = "是" if field.is_required else "否"
                description = getattr(field, 'description', None) or "-"
                validation_rules = self._get_field_validation_rules(field)
                
                doc.append(f"| `{field.field_name}` | {field.field_label} | `{field.field_type}` | {required_icon} {required_text} | {description} | {validation_rules} |")
            
            doc.append("")
            
            # 如果是数据上传API，添加加密请求字段说明
            if self._is_data_upload_api(api):
                doc.append("### 加密请求字段")
                doc.append("")
                doc.append("> **说明**: 当使用加密传输时，需要使用以下字段结构")
                doc.append("")
                doc.append("| 字段名 | 类型 | 必填 | 描述 | 示例值 |")
                doc.append("|:-------|:-----|:-----|:-----|:--------|")
                doc.append("| `timestamp` | `string` | ✅ 是 | 请求时间戳（毫秒） | \"1640995200000\" |")
                doc.append("| `nonce` | `string` | ✅ 是 | 随机数，用于防重放攻击 | \"abc123def456\" |")
                doc.append("| `data` | `string` | ✅ 是 | Base64编码的加密业务数据 | \"base64_encrypted_data\" |")
                doc.append("| `iv` | `string` | ✅ 是 | Base64编码的初始化向量 | \"base64_iv_data\" |")
                doc.append("| `signature` | `string` | ✅ 是 | HMAC-SHA256签名 | \"hmac_signature\" |")
                doc.append("| `needread` | `boolean` | ❌ 否 | 是否需要读取确认 | `false` |")
                doc.append("")
                doc.append("> **注意**: `data`字段包含的是加密后的原始业务数据，而不是上述普通请求字段")
                doc.append("")
        
        # 响应示例
        doc.append("## 📥 响应示例")
        doc.append("")
        
        doc.append("### ✅ 成功响应")
        doc.append("")
        doc.append("> **HTTP状态码**: `200 OK`")
        doc.append("")
        doc.append("```json")
        doc.append("{")
        doc.append('  "success": true,')
        doc.append('  "message": "处理成功",')
        doc.append('  "data": {')
        doc.append('    "id": 12345,')
        doc.append('    "status": "processed",')
        doc.append('    "timestamp": "2024-01-01T12:00:00Z"')
        doc.append('  }')
        doc.append("}")
        doc.append("```")
        doc.append("")
        
        doc.append("### ❌ 错误响应")
        doc.append("")
        doc.append("> **HTTP状态码**: `400 Bad Request`")
        doc.append("")
        doc.append("```json")
        doc.append("{")
        doc.append('  "success": false,')
        doc.append('  "message": "验证失败",')
        doc.append('  "errors": [')
        doc.append('    "字段 username 不能为空"')
        doc.append('  ]')
        doc.append("}")
        doc.append("```")
        doc.append("")
        
        # 错误码说明
        doc.append("## ⚠️ 错误码说明")
        doc.append("")
        doc.append("| 状态码 | 状态 | 说明 |")
        doc.append("|:-------|:-----|:-----|")
        doc.append("| `200` | ✅ 成功 | 请求处理成功 |")
        doc.append("| `400` | ❌ 错误 | 请求参数错误或格式不正确 |")
        doc.append("| `401` | 🔐 认证 | 未提供有效的认证信息 |")
        doc.append("| `403` | 🚫 权限 | 没有访问权限 |")
        doc.append("| `404` | 🔍 未找到 | 请求的资源不存在 |")
        doc.append("| `429` | ⏱️ 限流 | 请求频率超过限制 |")
        doc.append("| `500` | 💥 服务器 | 服务器内部错误 |")
        doc.append("")
        
        # SDK示例
        doc.append("## 🔧 SDK示例")
        doc.append("")
        
        # Python示例
        doc.append("### Python 示例")
        doc.append("")
        doc.append("```python")
        doc.append("import requests")
        doc.append("import json")
        doc.append("")
        doc.append("# API配置")
        doc.append(f'url = "https://your-domain.com/api/v1/{{batch_id}}/{api.api_code}"')
        doc.append("headers = {")
        doc.append('    "Content-Type": "application/json",')
        if api.require_authentication:
            doc.append('    "Authorization": "Bearer your_access_token"')
        doc.append("}")
        doc.append("")
        
        if hasattr(api, 'fields') and api.fields:
            doc.append("# 请求数据")
            doc.append("data = {")
            field_lines = []
            for field in api.fields:
                example_value = self._get_field_example_value(field)
                if isinstance(example_value, str):
                    field_lines.append(f'    "{field.field_name}": "{example_value}"')
                else:
                    field_lines.append(f'    "{field.field_name}": {json.dumps(example_value)}')
            
            # 添加字段，最后一个字段不加逗号
            for i, line in enumerate(field_lines):
                if i < len(field_lines) - 1:
                    doc.append(line + ",")
                else:
                    doc.append(line)
            doc.append("}")
            doc.append("")
            
            # 如果是数据上传API，添加加密请求示例
            if self._is_data_upload_api(api):
                doc.append("# 加密请求数据（当需要加密传输时）")
                doc.append("import time")
                doc.append("import os")
                doc.append("encrypted_data = {")
                doc.append('    "timestamp": str(int(time.time() * 1000)),')
                doc.append('    "nonce": os.urandom(8).hex(),')
                doc.append('    "data": "base64_encoded_encrypted_data_here",  # 加密后的业务数据')
                doc.append('    "iv": "base64_encoded_iv_here",  # 初始化向量')
                doc.append('    "signature": "hmac_sha256_signature_here",  # HMAC签名')
                doc.append('    "needread": False  # 是否需要读取确认')
                doc.append("}")
                doc.append("")
        
        doc.append("# 发送请求")
        if api.http_method.upper() == "GET":
            doc.append("response = requests.get(url, headers=headers)")
        else:
            if hasattr(api, 'fields') and api.fields and self._is_data_upload_api(api):
                doc.append("# 普通请求")
                doc.append("response = requests.post(url, headers=headers, json=data)")
                doc.append("")
                doc.append("# 或者加密请求（当需要加密传输时）")
                doc.append("# response = requests.post(url, headers=headers, json=encrypted_data)")
            else:
                doc.append("response = requests.post(url, headers=headers, json=data)")
        doc.append("")
        doc.append("# 处理响应")
        doc.append("if response.status_code == 200:")
        doc.append("    result = response.json()")
        doc.append("    print(f'成功: {result}')")
        doc.append("else:")
        doc.append("    print(f'错误: {response.status_code} - {response.text}')")
        doc.append("```")
        doc.append("")
        
        # Java示例
        doc.append("### Java 示例")
        doc.append("")
        doc.append("```java")
        doc.append("import java.net.http.HttpClient;")
        doc.append("import java.net.http.HttpRequest;")
        doc.append("import java.net.http.HttpResponse;")
        doc.append("import java.net.URI;")
        doc.append("import java.time.Duration;")
        doc.append("import com.fasterxml.jackson.databind.ObjectMapper;")
        doc.append("import java.util.HashMap;")
        doc.append("import java.util.Map;")
        doc.append("")
        doc.append("public class ApiClient {")
        doc.append("    public static void main(String[] args) throws Exception {")
        doc.append("        // API配置")
        doc.append(f'        String url = "https://your-domain.com/api/v1/{{batch_id}}/{api.api_code}";')
        doc.append("        ")
        
        if hasattr(api, 'fields') and api.fields:
            doc.append("        // 请求数据")
            doc.append("        Map<String, Object> data = new HashMap<>();")
            for field in api.fields:
                example_value = self._get_field_example_value(field)
                if isinstance(example_value, str):
                    doc.append(f'        data.put("{field.field_name}", "{example_value}");')
                elif isinstance(example_value, bool):
                    doc.append(f'        data.put("{field.field_name}", {str(example_value).lower()});')
                else:
                    doc.append(f'        data.put("{field.field_name}", {example_value});')
            doc.append("        ")
            
            # 如果是数据上传API，添加加密请求示例
            if self._is_data_upload_api(api):
                doc.append("        // 加密请求数据（当需要加密传输时）")
                doc.append("        Map<String, Object> encryptedData = new HashMap<>();")
                doc.append("        encryptedData.put(\"timestamp\", String.valueOf(System.currentTimeMillis()));")
                doc.append("        encryptedData.put(\"nonce\", generateNonce());")
                doc.append("        encryptedData.put(\"data\", \"base64_encoded_encrypted_data_here\");")
                doc.append("        encryptedData.put(\"iv\", \"base64_encoded_iv_here\");")
                doc.append("        encryptedData.put(\"signature\", \"hmac_sha256_signature_here\");")
                doc.append("        encryptedData.put(\"needread\", false);")
                doc.append("        ")
        
        doc.append("        // 创建HTTP客户端")
        doc.append("        HttpClient client = HttpClient.newBuilder()")
        doc.append("            .connectTimeout(Duration.ofSeconds(10))")
        doc.append("            .build();")
        doc.append("        ")
        doc.append("        // 构建请求")
        doc.append("        ObjectMapper mapper = new ObjectMapper();")
        if hasattr(api, 'fields') and api.fields:
            doc.append("        String jsonData = mapper.writeValueAsString(data);")
        else:
            doc.append("        String jsonData = \"{}\";")
        doc.append("        ")
        doc.append("        HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()")
        doc.append("            .uri(URI.create(url))")
        doc.append("            .header(\"Content-Type\", \"application/json\")")
        if api.require_authentication:
            doc.append("            .header(\"Authorization\", \"Bearer your_access_token\")")
        
        if api.http_method.upper() == "GET":
            doc.append("            .GET();")
        else:
            doc.append("            .POST(HttpRequest.BodyPublishers.ofString(jsonData));")
        doc.append("        ")
        doc.append("        HttpRequest request = requestBuilder.build();")
        doc.append("        ")
        doc.append("        // 发送请求")
        doc.append("        HttpResponse<String> response = client.send(request,")
        doc.append("            HttpResponse.BodyHandlers.ofString());")
        doc.append("        ")
        doc.append("        // 处理响应")
        doc.append("        if (response.statusCode() == 200) {")
        doc.append("            System.out.println(\"成功: \" + response.body());")
        doc.append("        } else {")
        doc.append("            System.err.println(\"错误: \" + response.statusCode() + \" - \" + response.body());")
        doc.append("        }")
        doc.append("    }")
        
        if hasattr(api, 'fields') and api.fields and self._is_data_upload_api(api):
            doc.append("    ")
            doc.append("    private static String generateNonce() {")
            doc.append("        return java.util.UUID.randomUUID().toString().replace(\"-\", \"\").substring(0, 16);")
            doc.append("    }")
        
        doc.append("}")
        doc.append("```")
        doc.append("")
        
        # 页脚
        doc.append("---")
        doc.append("")
        doc.append("📝 *本文档由系统自动生成，如有疑问请联系技术支持*")
        doc.append("")
        
        return "\n".join(doc)
    
    def _generate_json_documentation(self, api: CustomApi) -> str:
        """
        生成符合OpenAPI 3.0+标准的JSON格式API文档
        
        Args:
            api: API对象
            
        Returns:
            OpenAPI 3.0+ JSON文档内容
        """
        import json
        
        # 构建OpenAPI 3.0+规范的文档结构
        openapi_doc = {
            "openapi": "3.0.3",
            "info": {
                "title": f"{api.api_name} API",
                "description": api.api_description or f"API接口: {api.api_name}",
                "version": "1.0.0",
                "contact": {
                    "name": "API支持",
                    "email": "support@example.com"
                }
            },
            "servers": [
                {
                    "url": "https://your-domain.com/api/v1",
                    "description": "生产环境"
                },
                {
                    "url": "http://localhost:8000/api/v1",
                    "description": "开发环境"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {}
            }
        }
        
        # 如果需要认证，添加安全方案
        if api.require_authentication:
            openapi_doc["components"]["securitySchemes"] = {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT Bearer Token认证"
                }
            }
        
        # 构建路径信息
        path_key = f"/{{{"batch_id"}}}/{api.api_code}"
        method_key = api.http_method.lower()
        
        # 构建请求体schema
        request_schema = None
        if hasattr(api, 'fields') and api.fields:
            properties = {}
            required_fields = []
            
            for field in api.fields:
                field_schema = self._build_field_schema(field)
                properties[field.field_name] = field_schema
                
                if field.is_required:
                    required_fields.append(field.field_name)
            
            request_schema = {
                "type": "object",
                "properties": properties,
                "required": required_fields if required_fields else []
            }
            
            # 添加到components/schemas
            openapi_doc["components"]["schemas"][f"{api.api_code}Request"] = request_schema
            
            # 如果是数据上传API，添加加密请求schema
            if self._is_data_upload_api(api):
                encrypted_schema = {
                    "type": "object",
                    "properties": {
                        "timestamp": {
                            "type": "string",
                            "description": "请求时间戳（毫秒）",
                            "example": "1640995200000"
                        },
                        "nonce": {
                            "type": "string",
                            "description": "随机数，用于防重放攻击",
                            "example": "abc123def456"
                        },
                        "data": {
                            "type": "string",
                            "description": "Base64编码的加密业务数据",
                            "example": "base64_encoded_encrypted_data_here"
                        },
                        "iv": {
                            "type": "string",
                            "description": "Base64编码的初始化向量",
                            "example": "base64_encoded_iv_here"
                        },
                        "signature": {
                            "type": "string",
                            "description": "HMAC-SHA256签名",
                            "example": "hmac_sha256_signature_here"
                        },
                        "needread": {
                            "type": "boolean",
                            "description": "是否需要读取确认",
                            "example": False,
                            "default": False
                        }
                    },
                    "required": ["timestamp", "nonce", "data", "iv", "signature"]
                }
                openapi_doc["components"]["schemas"][f"{api.api_code}EncryptedRequest"] = encrypted_schema
        
        # 构建响应schema
        success_response_schema = {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "请求是否成功",
                    "example": True
                },
                "message": {
                    "type": "string",
                    "description": "响应消息",
                    "example": "处理成功"
                },
                "data": {
                    "type": "object",
                    "description": "响应数据",
                    "example": {
                        "id": 12345,
                        "status": "processed",
                        "timestamp": "2024-01-01T12:00:00Z"
                    }
                }
            }
        }
        
        error_response_schema = {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "请求是否成功",
                    "example": False
                },
                "message": {
                    "type": "string",
                    "description": "错误消息",
                    "example": "验证失败"
                },
                "errors": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "错误详情列表",
                    "example": ["字段 username 不能为空"]
                }
            }
        }
        
        openapi_doc["components"]["schemas"]["SuccessResponse"] = success_response_schema
        openapi_doc["components"]["schemas"]["ErrorResponse"] = error_response_schema
        
        # 构建路径操作
        operation = {
            "summary": api.api_name,
            "description": api.api_description or f"执行{api.api_name}操作",
            "operationId": f"{method_key}_{api.api_code}",
            "parameters": [
                {
                    "name": "batch_id",
                    "in": "path",
                    "required": True,
                    "description": "批次ID",
                    "schema": {
                        "type": "string",
                        "example": "batch_123"
                    }
                }
            ],
            "responses": {
                "200": {
                    "description": "请求成功",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/SuccessResponse"
                            }
                        }
                    }
                },
                "400": {
                    "description": "请求参数错误",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                },
                "401": {
                    "description": "未授权",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                },
                "403": {
                    "description": "禁止访问",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                },
                "404": {
                    "description": "资源未找到",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                },
                "429": {
                    "description": "请求频率超限",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                },
                "500": {
                    "description": "服务器内部错误",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                }
            }
        }
        
        # 添加请求体（如果不是GET请求）
        if api.http_method.upper() != "GET" and request_schema:
            request_body = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": f"#/components/schemas/{api.api_code}Request"
                        }
                    }
                }
            }
            
            # 如果是数据上传API，添加加密请求选项
            if self._is_data_upload_api(api):
                request_body["content"]["application/json"]["examples"] = {
                    "normal": {
                        "summary": "普通请求",
                        "description": "标准的业务数据请求",
                        "value": self._generate_example_data(api)
                    },
                    "encrypted": {
                        "summary": "加密请求",
                        "description": "加密的业务数据请求",
                        "value": {
                            "timestamp": "1640995200000",
                            "nonce": "abc123def456",
                            "data": "base64_encoded_encrypted_data_here",
                            "iv": "base64_encoded_iv_here",
                            "signature": "hmac_sha256_signature_here",
                            "needread": False
                        }
                    }
                }
            
            operation["requestBody"] = request_body
        
        # 添加安全要求
        if api.require_authentication:
            operation["security"] = [{"bearerAuth": []}]
        
        # 添加标签
        operation["tags"] = ["Custom APIs"]
        
        # 添加到路径
        openapi_doc["paths"][path_key] = {method_key: operation}
        
        return json.dumps(openapi_doc, indent=2, ensure_ascii=False)
    
    def _build_field_schema(self, field: ApiField) -> dict:
        """
        构建字段的OpenAPI schema
        
        Args:
            field: 字段对象
            
        Returns:
            字段的schema定义
        """
        schema = {
            "description": getattr(field, 'description', None) or field.field_label
        }
        
        # 映射字段类型到OpenAPI类型
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "float": "number",
            "boolean": "boolean",
            "date": "string",
            "datetime": "string",
            "text": "string",
            "email": "string",
            "url": "string"
        }
        
        schema["type"] = type_mapping.get(field.field_type, "string")
        
        # 添加格式信息
        if field.field_type == "date":
            schema["format"] = "date"
        elif field.field_type == "datetime":
            schema["format"] = "date-time"
        elif field.field_type == "email":
            schema["format"] = "email"
        elif field.field_type == "url":
            schema["format"] = "uri"
        elif field.field_type == "float":
            schema["format"] = "float"
        
        # 添加验证规则
        if field.min_length:
            schema["minLength"] = field.min_length
        if field.max_length:
            schema["maxLength"] = field.max_length
        if field.min_value is not None:
            schema["minimum"] = field.min_value
        if field.max_value is not None:
            schema["maximum"] = field.max_value
        if field.validation_regex:
            schema["pattern"] = field.validation_regex
        if field.allowed_values:
            try:
                # 尝试解析允许值
                import json
                allowed_list = json.loads(field.allowed_values) if isinstance(field.allowed_values, str) else field.allowed_values
                if isinstance(allowed_list, list):
                    schema["enum"] = allowed_list
            except:
                pass
        
        # 添加默认值
        if field.default_value:
            schema["default"] = field.default_value
        
        # 添加示例值
        schema["example"] = self._get_field_example_value(field)
        
        return schema
    
    def _generate_example_data(self, api: CustomApi) -> dict:
        """
        生成示例数据
        
        Args:
            api: API对象
            
        Returns:
            示例数据字典
        """
        example_data = {}
        if hasattr(api, 'fields') and api.fields:
            for field in api.fields:
                example_data[field.field_name] = self._get_field_example_value(field)
        return example_data
    
    def _generate_html_documentation(self, api: CustomApi) -> str:
        """
        生成HTML格式的API文档
        
        Args:
            api: API对象
            
        Returns:
            HTML文档内容
        """
        import html
        import json
        
        # 生成HTML文档
        html_content = []
        
        # HTML头部
        html_content.append(f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(api.api_name)} API文档</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
            margin-top: 40px;
            margin-bottom: 20px;
        }}
        h3 {{
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 8px;
        }}
        .badge-success {{ background-color: #d4edda; color: #155724; }}
        .badge-danger {{ background-color: #f8d7da; color: #721c24; }}
        .badge-primary {{ background-color: #d1ecf1; color: #0c5460; }}
        .badge-warning {{ background-color: #fff3cd; color: #856404; }}
        .badge-info {{ background-color: #d1ecf1; color: #0c5460; }}
        .method-get {{ background-color: #28a745; color: white; }}
        .method-post {{ background-color: #007bff; color: white; }}
        .method-put {{ background-color: #ffc107; color: #212529; }}
        .method-delete {{ background-color: #dc3545; color: white; }}
        .method-patch {{ background-color: #6c757d; color: white; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
        }}
        th, td {{
            border: 1px solid #dee2e6;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        pre {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            margin: 16px 0;
        }}
        code {{
            background-color: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace;
            font-size: 87%;
        }}
        .alert {{
            padding: 15px;
            margin: 20px 0;
            border: 1px solid transparent;
            border-radius: 6px;
        }}
        .alert-info {{
            color: #0c5460;
            background-color: #d1ecf1;
            border-color: #bee5eb;
        }}
        .alert-warning {{
            color: #856404;
            background-color: #fff3cd;
            border-color: #ffeaa7;
        }}
        .copy-btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 10px;
        }}
        .copy-btn:hover {{
            background: #0056b3;
        }}
        .toc {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        .toc li {{
            margin: 8px 0;
        }}
        .toc a {{
            color: #007bff;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
""")
        
        # 文档标题和基本信息
        status_badge = "badge-success" if api.status else "badge-danger"
        status_text = "启用" if api.status else "禁用"
        method_class = f"method-{api.http_method.lower()}"
        
        html_content.append(f"""
        <h1>📋 {html.escape(api.api_name)} API文档</h1>
        
        <div style="margin-bottom: 30px;">
            <span class="badge {status_badge}">{status_text}</span>
            <span class="badge {method_class}">{api.http_method}</span>
            <span class="badge badge-info">{'需要认证' if api.require_authentication else '无需认证'}</span>
        </div>
""")
        
        # 目录
        html_content.append("""
        <div class="toc">
            <h3>📑 目录</h3>
            <ul>
                <li><a href="#basic-info">📋 基本信息</a></li>""")
        
        if self._is_data_upload_api(api):
            html_content.append('                <li><a href="#encryption">🔐 数据加密说明</a></li>')
        
        html_content.append("""
                <li><a href="#request-examples">📤 请求示例</a></li>""")
        
        if hasattr(api, 'fields') and api.fields:
            html_content.append('                <li><a href="#field-description">📝 字段说明</a></li>')
        
        html_content.append("""
                <li><a href="#response-examples">📥 响应示例</a></li>
                <li><a href="#error-codes">⚠️ 错误码说明</a></li>
                <li><a href="#sdk-examples">🔧 SDK示例</a></li>
            </ul>
        </div>
        """)
        
        # 基本信息
        html_content.append(f"""
        <h2 id="basic-info">📋 基本信息</h2>
        <table>
            <tr><th>属性</th><th>值</th></tr>
            <tr><td><strong>API名称</strong></td><td><code>{html.escape(api.api_name)}</code></td></tr>
            <tr><td><strong>API代码</strong></td><td><code>{html.escape(api.api_code)}</code></td></tr>
            <tr><td><strong>HTTP方法</strong></td><td><code>{html.escape(api.http_method)}</code></td></tr>
            <tr><td><strong>API URL</strong></td><td><code>{html.escape(api.api_url)}</code></td></tr>
            <tr><td><strong>完整路径</strong></td><td><code>/api/v1/{{batch_id}}/{html.escape(api.api_code)}</code></td></tr>
            <tr><td><strong>状态</strong></td><td><span class="badge {status_badge}">{status_text}</span></td></tr>""")
        
        if api.api_description:
            html_content.append(f'            <tr><td><strong>描述</strong></td><td>{html.escape(api.api_description)}</td></tr>')
        
        if api.rate_limit:
            html_content.append(f'            <tr><td><strong>频率限制</strong></td><td>⏱️ {api.rate_limit} 次/分钟</td></tr>')
        
        auth_text = "🔐 是" if api.require_authentication else "🔓 否"
        html_content.append(f'            <tr><td><strong>需要认证</strong></td><td>{auth_text}</td></tr>')
        html_content.append('        </table>')
        
        # 加密说明（如果是数据上传API）
        if self._is_data_upload_api(api):
            html_content.append(self._generate_html_encryption_section())
        
        # 请求示例
        html_content.append(f"""
        <h2 id="request-examples">📤 请求示例</h2>
        
        <h3>HTTP 请求头</h3>
        <pre><code>{html.escape(api.http_method)} /api/v1/{{batch_id}}/{html.escape(api.api_code)} HTTP/1.1
Host: your-domain.com
Content-Type: application/json""")
        
        if api.require_authentication:
            html_content.append('\nAuthorization: Bearer <your_access_token>')
        
        html_content.append('</code></pre>')
        
        # 请求体示例
        if hasattr(api, 'fields') and api.fields:
            example_data = self._generate_example_data(api)
            
            html_content.append("""
        <h3>请求体示例</h3>
        
        <h4>普通请求</h4>
        <pre><code>""")
            html_content.append(html.escape(json.dumps(example_data, indent=2, ensure_ascii=False)))
            html_content.append('</code></pre>')
            
            # 加密请求示例
            if self._is_data_upload_api(api):
                encrypted_example = {
                    "timestamp": "1640995200000",
                    "nonce": "abc123def456",
                    "data": "base64_encoded_encrypted_business_data_here",
                    "iv": "base64_encoded_iv_here",
                    "signature": "hmac_sha256_signature_here",
                    "needread": False
                }
                
                html_content.append("""
        <h4>加密请求</h4>
        <div class="alert alert-info">
            <strong>说明:</strong> 业务数据需要先加密，然后放入<code>data</code>字段中
        </div>
        
        <p><strong>原始业务数据:</strong></p>
        <pre><code>""")
                html_content.append(html.escape(json.dumps(example_data, indent=2, ensure_ascii=False)))
                html_content.append('</code></pre>')
                
                html_content.append('<p><strong>加密后的请求体:</strong></p>\n        <pre><code>')
                html_content.append(html.escape(json.dumps(encrypted_example, indent=2, ensure_ascii=False)))
                html_content.append('</code></pre>')
        
        # 字段说明
        if hasattr(api, 'fields') and api.fields:
            html_content.append("""
        <h2 id="field-description">📝 字段说明</h2>
        
        <h3>普通请求字段</h3>
        <table>
            <tr>
                <th>字段名</th>
                <th>标签</th>
                <th>类型</th>
                <th>必填</th>
                <th>描述</th>
                <th>验证规则</th>
            </tr>""")
            
            for field in api.fields:
                required_icon = "✅" if field.is_required else "❌"
                required_text = "是" if field.is_required else "否"
                description = getattr(field, 'description', None) or "-"
                validation_rules = self._get_field_validation_rules(field)
                
                html_content.append(f"""
            <tr>
                <td><code>{html.escape(field.field_name)}</code></td>
                <td>{html.escape(field.field_label)}</td>
                <td><code>{html.escape(field.field_type)}</code></td>
                <td>{required_icon} {required_text}</td>
                <td>{html.escape(description)}</td>
                <td>{html.escape(validation_rules)}</td>
            </tr>""")
            
            html_content.append('        </table>')
            
            # 加密请求字段说明
            if self._is_data_upload_api(api):
                html_content.append("""
        <h3>加密请求字段</h3>
        <div class="alert alert-info">
            <strong>说明:</strong> 当使用加密传输时，需要使用以下字段结构
        </div>
        <table>
            <tr>
                <th>字段名</th>
                <th>类型</th>
                <th>必填</th>
                <th>描述</th>
                <th>示例值</th>
            </tr>
            <tr>
                <td><code>timestamp</code></td>
                <td><code>string</code></td>
                <td>✅ 是</td>
                <td>请求时间戳（毫秒）</td>
                <td>"1640995200000"</td>
            </tr>
            <tr>
                <td><code>nonce</code></td>
                <td><code>string</code></td>
                <td>✅ 是</td>
                <td>随机数，用于防重放攻击</td>
                <td>"abc123def456"</td>
            </tr>
            <tr>
                <td><code>data</code></td>
                <td><code>string</code></td>
                <td>✅ 是</td>
                <td>Base64编码的加密业务数据</td>
                <td>"base64_encrypted_data"</td>
            </tr>
            <tr>
                <td><code>iv</code></td>
                <td><code>string</code></td>
                <td>✅ 是</td>
                <td>Base64编码的初始化向量</td>
                <td>"base64_iv_data"</td>
            </tr>
            <tr>
                <td><code>signature</code></td>
                <td><code>string</code></td>
                <td>✅ 是</td>
                <td>HMAC-SHA256签名</td>
                <td>"hmac_signature"</td>
            </tr>
            <tr>
                <td><code>needread</code></td>
                <td><code>boolean</code></td>
                <td>❌ 否</td>
                <td>是否需要读取确认</td>
                <td>false</td>
            </tr>
        </table>
        <div class="alert alert-warning">
            <strong>注意:</strong> <code>data</code>字段包含的是加密后的原始业务数据，而不是上述普通请求字段
        </div>""")
        
        # 响应示例
        success_response = {
            "success": True,
            "message": "处理成功",
            "data": {
                "id": 12345,
                "status": "processed",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
        
        error_response = {
            "success": False,
            "message": "验证失败",
            "errors": [
                "字段 username 不能为空"
            ]
        }
        
        html_content.append(f"""
        <h2 id="response-examples">📥 响应示例</h2>
        
        <h3>✅ 成功响应</h3>
        <p><strong>HTTP状态码:</strong> <code>200 OK</code></p>
        <pre><code>{html.escape(json.dumps(success_response, indent=2, ensure_ascii=False))}</code></pre>
        
        <h3>❌ 错误响应</h3>
        <p><strong>HTTP状态码:</strong> <code>400 Bad Request</code></p>
        <pre><code>{html.escape(json.dumps(error_response, indent=2, ensure_ascii=False))}</code></pre>
        """)
        
        # 错误码说明
        html_content.append("""
        <h2 id="error-codes">⚠️ 错误码说明</h2>
        <table>
            <tr><th>状态码</th><th>状态</th><th>说明</th></tr>
            <tr><td><code>200</code></td><td>✅ 成功</td><td>请求处理成功</td></tr>
            <tr><td><code>400</code></td><td>❌ 错误</td><td>请求参数错误或格式不正确</td></tr>
            <tr><td><code>401</code></td><td>🔐 认证</td><td>未提供有效的认证信息</td></tr>
            <tr><td><code>403</code></td><td>🚫 权限</td><td>没有访问权限</td></tr>
            <tr><td><code>404</code></td><td>🔍 未找到</td><td>请求的资源不存在</td></tr>
            <tr><td><code>429</code></td><td>⏱️ 限流</td><td>请求频率超过限制</td></tr>
            <tr><td><code>500</code></td><td>💥 服务器</td><td>服务器内部错误</td></tr>
        </table>
        """)
        
        # SDK示例
        html_content.append(self._generate_html_sdk_examples(api))
        
        # 页脚
        html_content.append("""
        <hr style="margin: 40px 0;">
        <p style="text-align: center; color: #6c757d; font-size: 14px;">
            📝 <em>本文档由系统自动生成，如有疑问请联系技术支持</em>
        </p>
        
        <script>
            // 复制功能
            function copyToClipboard(text) {
                navigator.clipboard.writeText(text).then(function() {
                    alert('已复制到剪贴板！');
                }, function(err) {
                    console.error('复制失败: ', err);
                });
            }
        </script>
    </div>
</body>
</html>
        """)
        
        return '\n'.join(html_content)
    
    def _generate_html_encryption_section(self) -> str:
        """
        生成HTML格式的加密说明部分
        
        Returns:
            HTML格式的加密说明
        """
        return """
        <h2 id="encryption">🔐 数据加密说明</h2>
        
        <div class="alert alert-info">
            <strong>重要提示:</strong> 本API支持数据加密传输，用于保护敏感业务数据的安全性。
        </div>
        
        <h3>加密流程</h3>
        <ol>
            <li><strong>准备业务数据:</strong> 将原始业务数据序列化为JSON字符串</li>
            <li><strong>生成密钥:</strong> 使用AES-256-CBC算法生成加密密钥</li>
            <li><strong>数据加密:</strong> 使用密钥和随机IV对业务数据进行加密</li>
            <li><strong>生成签名:</strong> 使用HMAC-SHA256对关键参数进行签名</li>
            <li><strong>构建请求:</strong> 将加密数据和签名信息组装成请求体</li>
        </ol>
        
        <h3>加密参数说明</h3>
        <table>
            <tr><th>参数</th><th>说明</th><th>生成方式</th></tr>
            <tr>
                <td><code>timestamp</code></td>
                <td>请求时间戳（毫秒）</td>
                <td>当前时间的毫秒时间戳</td>
            </tr>
            <tr>
                <td><code>nonce</code></td>
                <td>随机数</td>
                <td>12位随机字符串，用于防重放攻击</td>
            </tr>
            <tr>
                <td><code>data</code></td>
                <td>加密的业务数据</td>
                <td>AES-256-CBC加密后Base64编码</td>
            </tr>
            <tr>
                <td><code>iv</code></td>
                <td>初始化向量</td>
                <td>16字节随机数据Base64编码</td>
            </tr>
            <tr>
                <td><code>signature</code></td>
                <td>请求签名</td>
                <td>HMAC-SHA256(timestamp+nonce+data+iv)</td>
            </tr>
            <tr>
                <td><code>needread</code></td>
                <td>读取确认标志</td>
                <td>布尔值，默认false</td>
            </tr>
        </table>
        
        <div class="alert alert-warning">
            <strong>安全提醒:</strong>
            <ul>
                <li>请妥善保管加密密钥，不要在代码中硬编码</li>
                <li>每次请求都应使用新的随机IV</li>
                <li>时间戳误差不应超过5分钟</li>
                <li>相同的nonce在短时间内不应重复使用</li>
            </ul>
        </div>
        """
    
    def _generate_html_sdk_examples(self, api: CustomApi) -> str:
        """
        生成HTML格式的SDK示例
        
        Args:
            api: API对象
            
        Returns:
            HTML格式的SDK示例
        """
        import html
        import json
        
        # 生成示例数据
        example_data = self._generate_example_data(api)
        
        # Python SDK示例
        python_example = f"""
import requests
import json
import time
import secrets
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import hmac
import hashlib

# API配置
API_BASE_URL = "https://your-domain.com/api/v1"
BATCH_ID = "your_batch_id"
API_CODE = "{api.api_code}"
ACCESS_TOKEN = "your_access_token"  # 如果需要认证
ENCRYPTION_KEY = "your_32_byte_encryption_key"  # 32字节密钥
HMAC_SECRET = "your_hmac_secret_key"

def call_api_normal():
    \"\"\"普通API调用示例\"\"\"
    url = f"{{API_BASE_URL}}/{{BATCH_ID}}/{{API_CODE}}"
    
    # 请求数据
    data = {json.dumps(example_data, indent=4)}
    
    # 请求头
    headers = {{
        "Content-Type": "application/json"""
        
        if api.require_authentication:
            python_example += """,
        "Authorization": f"Bearer {ACCESS_TOKEN}"""
        
        python_example += """
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        print("API调用成功:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"API调用失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"错误详情: {e.response.text}")
        return None
"""
        
        # 如果是数据上传API，添加加密示例
        if self._is_data_upload_api(api):
            python_example += f"""

def call_api_encrypted():
    \"\"\"加密API调用示例\"\"\"
    url = f"{{API_BASE_URL}}/{{BATCH_ID}}/{{API_CODE}}"
    
    # 原始业务数据
    business_data = {json.dumps(example_data, indent=4)}
    
    # 生成加密参数
    timestamp = str(int(time.time() * 1000))
    nonce = secrets.token_hex(6)  # 12位随机字符串
    
    # 加密业务数据
    business_json = json.dumps(business_data, separators=(',', ':'))
    
    # 生成随机IV
    iv = secrets.token_bytes(16)
    
    # AES加密
    cipher = AES.new(ENCRYPTION_KEY.encode('utf-8')[:32], AES.MODE_CBC, iv)
    padded_data = pad(business_json.encode('utf-8'), AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    
    # Base64编码
    data_b64 = base64.b64encode(encrypted_data).decode('utf-8')
    iv_b64 = base64.b64encode(iv).decode('utf-8')
    
    # 生成签名
    sign_string = f"{{timestamp}}{{nonce}}{{data_b64}}{{iv_b64}}"
    signature = hmac.new(
        HMAC_SECRET.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # 构建加密请求
    encrypted_request = {{
        "timestamp": timestamp,
        "nonce": nonce,
        "data": data_b64,
        "iv": iv_b64,
        "signature": signature,
        "needread": False
    }}
    
    # 请求头
    headers = {{
        "Content-Type": "application/json"""
            
            if api.require_authentication:
                python_example += """,
        "Authorization": f"Bearer {ACCESS_TOKEN}"""
            
            python_example += """
    }
    
    try:
        response = requests.post(url, json=encrypted_request, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        print("加密API调用成功:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"加密API调用失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"错误详情: {e.response.text}")
        return None
"""
        
        python_example += """

if __name__ == "__main__":
    print("=== 普通API调用 ===")
    call_api_normal()
    """
        
        if self._is_data_upload_api(api):
            python_example += """
    
    print("\n=== 加密API调用 ===")
    call_api_encrypted()
    """
        
        # Java SDK示例
        java_example = f"""
import okhttp3.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import javax.crypto.Cipher;
import javax.crypto.Mac;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.*;
import java.util.concurrent.TimeUnit;

public class {api.api_code.title()}ApiClient {{
    
    private static final String API_BASE_URL = "https://your-domain.com/api/v1";
    private static final String BATCH_ID = "your_batch_id";
    private static final String API_CODE = "{api.api_code}";
    private static final String ACCESS_TOKEN = "your_access_token";  // 如果需要认证
    private static final String ENCRYPTION_KEY = "your_32_byte_encryption_key";
    private static final String HMAC_SECRET = "your_hmac_secret_key";
    
    private final OkHttpClient httpClient;
    private final ObjectMapper objectMapper;
    
    public {api.api_code.title()}ApiClient() {{
        this.httpClient = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build();
        this.objectMapper = new ObjectMapper();
    }}
    
    /**
     * 普通API调用
     */
    public void callApiNormal() {{
        try {{
            String url = API_BASE_URL + "/" + BATCH_ID + "/" + API_CODE;
            
            // 构建请求数据
            Map<String, Object> requestData = new HashMap<>();"""
        
        # 添加字段示例
        if hasattr(api, 'fields') and api.fields:
            for field in api.fields:
                example_value = self._get_field_example_value(field)
                if field.field_type == "string":
                    java_example += f'\n            requestData.put("{field.field_name}", "{example_value}");'
                elif field.field_type == "integer":
                    java_example += f'\n            requestData.put("{field.field_name}", {example_value});'
                elif field.field_type == "boolean":
                    java_example += f'\n            requestData.put("{field.field_name}", {str(example_value).lower()});'
                else:
                    java_example += f'\n            requestData.put("{field.field_name}", "{example_value}");'
        
        java_example += """
            
            // 序列化请求数据
            String jsonData = objectMapper.writeValueAsString(requestData);
            
            // 构建请求
            RequestBody body = RequestBody.create(
                jsonData, 
                MediaType.parse("application/json")
            );
            
            Request.Builder requestBuilder = new Request.Builder()
                .url(url)
                .post(body)
                .addHeader("Content-Type", "application/json");
            """
        
        if api.require_authentication:
            java_example += """
            requestBuilder.addHeader("Authorization", "Bearer " + ACCESS_TOKEN);
            """
        
        java_example += """
            
            Request request = requestBuilder.build();
            
            // 发送请求
            try (Response response = httpClient.newCall(request).execute()) {
                if (response.isSuccessful()) {
                    String responseBody = response.body().string();
                    System.out.println("API调用成功: " + responseBody);
                } else {
                    System.err.println("API调用失败: " + response.code() + " " + response.message());
                    if (response.body() != null) {
                        System.err.println("错误详情: " + response.body().string());
                    }
                }
            }
            
        } catch (Exception e) {
            System.err.println("API调用异常: " + e.getMessage());
            e.printStackTrace();
        }
    }
    """
        
        # 如果是数据上传API，添加加密方法
        if self._is_data_upload_api(api):
            java_example += """
    
    /**
     * 加密API调用
     */
    public void callApiEncrypted() {
        try {
            String url = API_BASE_URL + "/" + BATCH_ID + "/" + API_CODE;
            
            // 构建原始业务数据
            Map<String, Object> businessData = new HashMap<>();"""
            
            # 添加字段示例
            if hasattr(api, 'fields') and api.fields:
                for field in api.fields:
                    example_value = self._get_field_example_value(field)
                    if field.field_type == "string":
                        java_example += f'\n            businessData.put("{field.field_name}", "{example_value}");'
                    elif field.field_type == "integer":
                        java_example += f'\n            businessData.put("{field.field_name}", {example_value});'
                    elif field.field_type == "boolean":
                        java_example += f'\n            businessData.put("{field.field_name}", {str(example_value).lower()});'
                    else:
                        java_example += f'\n            businessData.put("{field.field_name}", "{example_value}");'
            
            java_example += """
            
            // 生成加密参数
            String timestamp = String.valueOf(System.currentTimeMillis());
            String nonce = generateNonce();
            
            // 序列化业务数据
            String businessJson = objectMapper.writeValueAsString(businessData);
            
            // 生成随机IV
            byte[] iv = new byte[16];
            new SecureRandom().nextBytes(iv);
            
            // AES加密
            Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
            SecretKeySpec keySpec = new SecretKeySpec(
                ENCRYPTION_KEY.getBytes(StandardCharsets.UTF_8), 
                "AES"
            );
            IvParameterSpec ivSpec = new IvParameterSpec(iv);
            cipher.init(Cipher.ENCRYPT_MODE, keySpec, ivSpec);
            
            byte[] encryptedData = cipher.doFinal(businessJson.getBytes(StandardCharsets.UTF_8));
            
            // Base64编码
            String dataB64 = Base64.getEncoder().encodeToString(encryptedData);
            String ivB64 = Base64.getEncoder().encodeToString(iv);
            
            // 生成签名
            String signString = timestamp + nonce + dataB64 + ivB64;
            String signature = generateHmacSha256(signString, HMAC_SECRET);
            
            // 构建加密请求
            Map<String, Object> encryptedRequest = new HashMap<>();
            encryptedRequest.put("timestamp", timestamp);
            encryptedRequest.put("nonce", nonce);
            encryptedRequest.put("data", dataB64);
            encryptedRequest.put("iv", ivB64);
            encryptedRequest.put("signature", signature);
            encryptedRequest.put("needread", false);
            
            // 序列化加密请求
            String jsonData = objectMapper.writeValueAsString(encryptedRequest);
            
            // 构建请求
            RequestBody body = RequestBody.create(
                jsonData, 
                MediaType.parse("application/json")
            );
            
            Request.Builder requestBuilder = new Request.Builder()
                .url(url)
                .post(body)
                .addHeader("Content-Type", "application/json");
            """
            
            if api.require_authentication:
                java_example += """
            requestBuilder.addHeader("Authorization", "Bearer " + ACCESS_TOKEN);
            """
            
            java_example += """
            
            Request request = requestBuilder.build();
            
            // 发送请求
            try (Response response = httpClient.newCall(request).execute()) {
                if (response.isSuccessful()) {
                    String responseBody = response.body().string();
                    System.out.println("加密API调用成功: " + responseBody);
                } else {
                    System.err.println("加密API调用失败: " + response.code() + " " + response.message());
                    if (response.body() != null) {
                        System.err.println("错误详情: " + response.body().string());
                    }
                }
            }
            
        } catch (Exception e) {
            System.err.println("加密API调用异常: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * 生成随机nonce
     */
    private String generateNonce() {
        SecureRandom random = new SecureRandom();
        byte[] bytes = new byte[6];
        random.nextBytes(bytes);
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b & 0xff));
        }
        return sb.toString();
    }
    
    /**
     * 生成HMAC-SHA256签名
     */
    private String generateHmacSha256(String data, String secret) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        SecretKeySpec secretKeySpec = new SecretKeySpec(
            secret.getBytes(StandardCharsets.UTF_8), 
            "HmacSHA256"
        );
        mac.init(secretKeySpec);
        byte[] hash = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
        
        StringBuilder sb = new StringBuilder();
        for (byte b : hash) {
            sb.append(String.format("%02x", b & 0xff));
        }
        return sb.toString();
    }
    """
        
        java_example += """
    
    public static void main(String[] args) {
        {api.api_code.title()}ApiClient client = new {api.api_code.title()}ApiClient();
        
        System.out.println("=== 普通API调用 ===");
        client.callApiNormal();
        """
        
        if self._is_data_upload_api(api):
            java_example += """
        
        System.out.println("\n=== 加密API调用 ===");
        client.callApiEncrypted();
        """
        
        java_example += """
    }
}
"""
        
        # 构建HTML内容
        html_content = f"""
        <h2 id="sdk-examples">🔧 SDK示例</h2>
        
        <div class="alert alert-info">
            <strong>说明:</strong> 以下提供Python和Java的SDK调用示例，您可以根据实际需求进行调整。
        </div>
        
        <h3>🐍 Python SDK示例</h3>
        
        <p><strong>依赖安装:</strong></p>
        <pre><code>pip install requests pycryptodome</code></pre>
        
        <p><strong>完整代码:</strong></p>
        <pre><code>{html.escape(python_example)}</code></pre>
        
        <h3>☕ Java SDK示例</h3>
        
        <p><strong>Maven依赖:</strong></p>
        <pre><code>&lt;dependencies&gt;
    &lt;dependency&gt;
        &lt;groupId&gt;com.squareup.okhttp3&lt;/groupId&gt;
        &lt;artifactId&gt;okhttp&lt;/artifactId&gt;
        &lt;version&gt;4.12.0&lt;/version&gt;
    &lt;/dependency&gt;
    &lt;dependency&gt;
        &lt;groupId&gt;com.fasterxml.jackson.core&lt;/groupId&gt;
        &lt;artifactId&gt;jackson-databind&lt;/artifactId&gt;
        &lt;version&gt;2.15.2&lt;/version&gt;
    &lt;/dependency&gt;
&lt;/dependencies&gt;</code></pre>
        
        <p><strong>完整代码:</strong></p>
        <pre><code>{html.escape(java_example)}</code></pre>
        
        <div class="alert alert-warning">
            <strong>注意事项:</strong>
            <ul>
                <li>请替换示例中的占位符为实际的配置值</li>
                <li>生产环境中请妥善保管密钥和访问令牌</li>
                <li>建议添加适当的错误处理和重试机制</li>
                <li>注意API的频率限制，避免过于频繁的调用</li>
            </ul>
        </div>
        """
        
        return html_content
    
    def _get_field_example_value(self, field: ApiField) -> Any:
        """
        获取字段示例值
        
        Args:
            field: 字段对象
            
        Returns:
            示例值
        """
        if field.default_value:
            return field.default_value
        
        if field.field_type == "string":
            return f"示例{field.field_label}"
        elif field.field_type == "integer":
            return 123
        elif field.field_type == "float":
            return 123.45
        elif field.field_type == "boolean":
            return True
        elif field.field_type == "date":
            return "2024-01-01"
        elif field.field_type == "datetime":
            return "2024-01-01T12:00:00Z"
        else:
            return "示例值"
    
    def _get_field_validation_rules(self, field: ApiField) -> str:
        """
        获取字段验证规则描述
        
        Args:
            field: 字段对象
            
        Returns:
            验证规则描述
        """
        rules = []
        
        if field.min_length:
            rules.append(f"最小长度: {field.min_length}")
        if field.max_length:
            rules.append(f"最大长度: {field.max_length}")
        if field.min_value is not None:
            rules.append(f"最小值: {field.min_value}")
        if field.max_value is not None:
            rules.append(f"最大值: {field.max_value}")
        if field.validation_regex:
            rules.append(f"正则: {field.validation_regex}")
        if field.allowed_values:
            rules.append(f"允许值: {field.allowed_values}")
        
        return "; ".join(rules) if rules else "-"
    
    def _is_data_upload_api(self, api: CustomApi) -> bool:
        """
        判断是否为数据上传API
        
        Args:
            api: API对象
            
        Returns:
            是否为数据上传API
        """
        # 根据API URL或名称判断是否为数据上传接口
        if not api:
            return False
            
        # 检查API URL是否包含数据上传相关路径
        if api.api_url and '/data/' in api.api_url.lower():
            return True
            
        # 检查API名称是否包含数据上传相关关键词
        if api.api_name:
            upload_keywords = ['数据上传', 'data upload', 'upload', '上传']
            api_name_lower = api.api_name.lower()
            for keyword in upload_keywords:
                if keyword.lower() in api_name_lower:
                    return True
                    
        # 检查API代码是否包含数据上传相关关键词
        if api.api_code:
            upload_keywords = ['data_upload', 'upload', 'data']
            api_code_lower = api.api_code.lower()
            for keyword in upload_keywords:
                if keyword in api_code_lower:
                    return True
                    
        return False
    
    def _generate_encryption_section(self) -> List[str]:
        """
        生成加密说明部分
        
        Returns:
            加密说明的文档行列表
        """
        section = []
        section.append("## 🔐 数据加密说明")
        section.append("")
        section.append("> ⚠️ **重要提示**: 为确保数据传输安全，本接口要求对敏感数据进行加密传输。")
        section.append("")
        section.append("### 🔄 加密流程")
        section.append("")
        section.append("1. **获取加密密钥**: 通过认证接口获取 `data_key`")
        section.append("2. **准备数据**: 将业务数据序列化为JSON字符串")
        section.append("3. **生成IV**: 生成16字节的随机初始化向量")
        section.append("4. **数据加密**: 使用 AES-256-GCM 算法加密原始数据")
        section.append("5. **生成签名**: 使用 HMAC-SHA256 对加密数据生成签名")
        section.append("6. **Base64编码**: 对加密数据和IV进行Base64编码")
        section.append("7. **提交数据**: 将所有参数提交到接口")
        section.append("")
        section.append("### 📋 请求参数")
        section.append("")
        section.append("| 参数名 | 类型 | 必填 | 描述 | 示例值 |")
        section.append("|--------|------|------|------|-------|")
        section.append("| `timestamp` | string | 是 | 时间戳（毫秒） | `1640995200000` |")
        section.append("| `nonce` | string | 是 | 随机字符串，防重放攻击 | `abc123def456` |")
        section.append("| `data` | string | 是 | 加密后的业务数据（Base64编码） | `base64_encoded_data` |")
        section.append("| `iv` | string | 是 | 初始化向量（Base64编码） | `base64_encoded_iv` |")
        section.append("| `signature` | string | 是 | HMAC-SHA256签名值 | `hmac_signature` |")
        section.append("| `needread` | boolean | 否 | 是否需要读取确认，默认false | `false` |")
        section.append("")
        section.append("### 🔧 加密实现示例")
        section.append("")
        section.append("#### Python 加密示例")
        section.append("")
        section.append("```python")
        section.append("import json")
        section.append("import base64")
        section.append("import hmac")
        section.append("import hashlib")
        section.append("import os")
        section.append("import time")
        section.append("from Crypto.Cipher import AES")
        section.append("from Crypto.Random import get_random_bytes")
        section.append("")
        section.append("def encrypt_data(data_key: str, plain_data: dict) -> dict:")
        section.append("    \"\"\"加密数据\"\"\"")
        section.append("    # 1. 序列化数据")
        section.append("    json_data = json.dumps(plain_data, ensure_ascii=False)")
        section.append("    data_bytes = json_data.encode('utf-8')")
        section.append("    ")
        section.append("    # 2. 生成随机IV")
        section.append("    iv = get_random_bytes(16)")
        section.append("    ")
        section.append("    # 3. AES-256-GCM加密")
        section.append("    key_bytes = data_key.encode('utf-8')[:32]  # 确保32字节")
        section.append("    cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=iv)")
        section.append("    encrypted_data, auth_tag = cipher.encrypt_and_digest(data_bytes)")
        section.append("    ")
        section.append("    # 4. Base64编码")
        section.append("    encrypted_b64 = base64.b64encode(encrypted_data + auth_tag).decode('utf-8')")
        section.append("    iv_b64 = base64.b64encode(iv).decode('utf-8')")
        section.append("    ")
        section.append("    # 5. 生成签名")
        section.append("    signature_data = f\"{encrypted_b64}{iv_b64}\"")
        section.append("    signature = hmac.new(")
        section.append("        key_bytes, ")
        section.append("        signature_data.encode('utf-8'), ")
        section.append("        hashlib.sha256")
        section.append("    ).hexdigest()")
        section.append("    ")
        section.append("    return {")
        section.append("        'timestamp': str(int(time.time() * 1000)),")
        section.append("        'nonce': os.urandom(8).hex(),")
        section.append("        'data': encrypted_b64,")
        section.append("        'iv': iv_b64,")
        section.append("        'signature': signature,")
        section.append("        'needread': False")
        section.append("    }")
        section.append("```")
        section.append("")
        section.append("#### JavaScript 加密示例")
        section.append("")
        section.append("```javascript")
        section.append("const crypto = require('crypto');")
        section.append("")
        section.append("function encryptData(dataKey, plainData) {")
        section.append("    // 1. 序列化数据")
        section.append("    const jsonData = JSON.stringify(plainData);")
        section.append("    const dataBuffer = Buffer.from(jsonData, 'utf-8');")
        section.append("    ")
        section.append("    // 2. 生成随机IV")
        section.append("    const iv = crypto.randomBytes(16);")
        section.append("    ")
        section.append("    // 3. AES-256-GCM加密")
        section.append("    const keyBuffer = Buffer.from(dataKey, 'utf-8').slice(0, 32);")
        section.append("    const cipher = crypto.createCipher('aes-256-gcm');")
        section.append("    cipher.setAAD(iv);")
        section.append("    ")
        section.append("    let encrypted = cipher.update(dataBuffer);")
        section.append("    encrypted = Buffer.concat([encrypted, cipher.final()]);")
        section.append("    const authTag = cipher.getAuthTag();")
        section.append("    ")
        section.append("    // 4. Base64编码")
        section.append("    const encryptedB64 = Buffer.concat([encrypted, authTag]).toString('base64');")
        section.append("    const ivB64 = iv.toString('base64');")
        section.append("    ")
        section.append("    // 5. 生成签名")
        section.append("    const signatureData = encryptedB64 + ivB64;")
        section.append("    const signature = crypto")
        section.append("        .createHmac('sha256', keyBuffer)")
        section.append("        .update(signatureData)")
        section.append("        .digest('hex');")
        section.append("    ")
        section.append("    return {")
        section.append("        timestamp: Date.now().toString(),")
        section.append("        nonce: crypto.randomBytes(8).toString('hex'),")
        section.append("        data: encryptedB64,")
        section.append("        iv: ivB64,")
        section.append("        signature: signature,")
        section.append("        needread: false")
        section.append("    };")
        section.append("}")
        section.append("```")
        section.append("")
        section.append("### ⚠️ 安全注意事项")
        section.append("")
        section.append("1. **密钥安全**: `data_key` 必须安全存储，不得泄露")
        section.append("2. **时间戳验证**: 服务器会验证时间戳，避免重放攻击")
        section.append("3. **随机数唯一**: `nonce` 必须每次请求都不同")
        section.append("4. **签名验证**: 服务器会验证HMAC签名的完整性")
        section.append("5. **HTTPS传输**: 必须使用HTTPS协议传输加密数据")
        section.append("")
        return section


class ApiFieldService(BaseService[ApiField, ApiFieldCreate, ApiFieldUpdate]):
    """
    API字段服务
    
    提供API字段管理的业务逻辑处理
    """
    
    def __init__(self):
        super().__init__(ApiField)
        self._cache_ttl = 300  # 5分钟缓存过期时间
    
    def _get_cache_key(self, api_id: int, ordered: bool = True) -> str:
        """
        生成缓存键
        
        Args:
            api_id: API ID
            ordered: 是否按排序顺序
            
        Returns:
            缓存键字符串
        """
        return f"api_fields:{api_id}:{ordered}"
    
    def _invalidate_cache(self, api_id: int):
        """
        清除指定API的字段缓存
        
        Args:
            api_id: API ID
        """
        if not redis_client:
            return
        
        try:
            # 删除有序和无序两种缓存
            cache_keys = [
                self._get_cache_key(api_id, True),
                self._get_cache_key(api_id, False)
            ]
            
            for key in cache_keys:
                redis_client.delete(key)
                
            self.logger.debug(f"Invalidated cache for API {api_id}")
        except Exception as e:
            self.logger.warning(f"Failed to invalidate cache for API {api_id}: {e}")
    
    def _serialize_fields(self, fields: List[ApiField]) -> str:
        """
        序列化字段列表为JSON字符串
        
        Args:
            fields: 字段列表
            
        Returns:
            JSON字符串
        """
        field_data = []
        for field in fields:
            field_dict = {
                'id': field.id,
                'api_id': field.api_id,
                'field_name': field.field_name,
                'field_label': field.field_label,
                'field_type': field.field_type,
                'is_required': field.is_required,
                'default_value': field.default_value,
                'max_length': field.max_length,
                'min_length': field.min_length,
                'max_value': float(field.max_value) if field.max_value is not None else None,
                'min_value': float(field.min_value) if field.min_value is not None else None,
                'allowed_values': field.allowed_values,
                'validation_regex': field.validation_regex,
                'validation_message': field.validation_message,
                'sort_order': field.sort_order,
                'created_at': field.created_at.isoformat() if field.created_at else None,
                'updated_at': field.updated_at.isoformat() if field.updated_at else None
            }
            field_data.append(field_dict)
        
        return json.dumps(field_data)
    
    def _deserialize_fields(self, data: str, db: Session) -> List[ApiField]:
        """
        反序列化JSON字符串为字段列表
        
        Args:
            data: JSON字符串
            db: 数据库会话
            
        Returns:
            字段列表
        """
        try:
            field_data = json.loads(data)
            fields = []
            
            for item in field_data:
                field = ApiField()
                field.id = item['id']
                field.api_id = item['api_id']
                field.field_name = item['field_name']
                field.field_label = item['field_label']
                field.field_type = item['field_type']
                field.is_required = item['is_required']
                field.default_value = item['default_value']
                field.max_length = item['max_length']
                field.min_length = item['min_length']
                field.max_value = item['max_value']
                field.min_value = item['min_value']
                field.allowed_values = item['allowed_values']
                field.validation_regex = item['validation_regex']
                field.validation_message = item['validation_message']
                field.sort_order = item['sort_order']
                
                if item['created_at']:
                    field.created_at = datetime.fromisoformat(item['created_at'])
                if item['updated_at']:
                    field.updated_at = datetime.fromisoformat(item['updated_at'])
                
                fields.append(field)
            
            return fields
        except Exception as e:
            self.logger.warning(f"Failed to deserialize fields from cache: {e}")
            return []
    
    def create_field(
        self,
        db: Session,
        field_data: ApiFieldCreate,
        api_id: int,
        created_by: Optional[int] = None
    ) -> ApiField:
        """
        创建API字段
        
        Args:
            db: 数据库会话
            field_data: 字段创建数据
            api_id: API ID
            created_by: 创建者ID
            
        Returns:
            创建的字段对象
            
        Raises:
            ConflictException: 字段名已存在
            NotFoundException: API不存在
        """
        # 检查API是否存在
        api = db.query(CustomApi).filter(CustomApi.id == api_id).first()
        if not api:
            raise NotFoundException(f"API {api_id} 不存在")
        
        # 检查字段名是否已存在（同一API下）
        if self.exists(db, filters={
            "api_id": api_id,
            "field_name": field_data.field_name
        }):
            raise ConflictException(f"字段名 '{field_data.field_name}' 已存在")
        
        # 验证字段名格式
        if not self._is_valid_field_name(field_data.field_name):
            raise ValidationException("字段名格式不正确，只能包含字母、数字和下划线")
        
        # 获取下一个排序值
        max_sort_order = db.query(func.max(ApiField.sort_order)).filter(
            ApiField.api_id == api_id
        ).scalar() or 0
        
        # 准备创建数据
        create_data = field_data.dict()
        create_data.update({
            "api_id": api_id,
            "sort_order": max_sort_order + 1
        })
        
        # 创建字段
        field = self.create(db, obj_in=create_data)
        
        # 清除相关缓存
        self._invalidate_cache(api_id)
        
        self.logger.info(f"Created field: {field.field_name} for API: {api_id}")
        return field
    
    def update_field(
        self,
        db: Session,
        field_id: int,
        field_data: ApiFieldUpdate,
        updated_by: Optional[int] = None
    ) -> ApiField:
        """
        更新API字段
        
        Args:
            db: 数据库会话
            field_id: 字段ID
            field_data: 更新数据
            updated_by: 更新者ID
            
        Returns:
            更新后的字段对象
            
        Raises:
            NotFoundException: 字段不存在
            ConflictException: 字段名冲突
        """
        field = self.get_or_404(db, field_id)
        
        # 检查字段名是否冲突
        if field_data.field_name and field_data.field_name != field.field_name:
            if self.exists(db, filters={
                "api_id": field.api_id,
                "field_name": field_data.field_name,
                "id": {"ne": field_id}
            }):
                raise ConflictException(f"字段名 '{field_data.field_name}' 已存在")
        
        # 更新数据
        update_data = field_data.dict(exclude_unset=True)
        
        updated_field = self.update(db, db_obj=field, obj_in=update_data)
        
        # 清除相关缓存
        self._invalidate_cache(field.api_id)
        
        self.logger.info(f"Updated field: {field.field_name} (ID: {field.id})")
        return updated_field
    
    def get_api_fields(
        self,
        db: Session,
        api_id: int,
        ordered: bool = True
    ) -> List[ApiField]:
        """
        获取API的字段列表（带Redis缓存）
        
        Args:
            db: 数据库会话
            api_id: API ID
            ordered: 是否按排序顺序
            
        Returns:
            字段列表
        """
        # 生成缓存键
        cache_key = self._get_cache_key(api_id, ordered)
        
        # 尝试从Redis缓存获取
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    fields = self._deserialize_fields(cached_data.decode('utf-8'), db)
                    if fields:  # 确保反序列化成功
                        self.logger.debug(f"Cache hit for API {api_id} fields (ordered={ordered})")
                        return fields
            except Exception as e:
                self.logger.warning(f"Failed to get fields from cache: {e}")
        
        # 缓存未命中或Redis不可用，查询数据库
        self.logger.debug(f"Cache miss for API {api_id} fields (ordered={ordered}), querying database")
        query = db.query(ApiField).filter(ApiField.api_id == api_id)
        
        if ordered:
            query = query.order_by(ApiField.sort_order, ApiField.id)
        
        result = query.all()
        
        # 将结果存入Redis缓存
        if redis_client and result:
            try:
                serialized_data = self._serialize_fields(result)
                redis_client.setex(cache_key, self._cache_ttl, serialized_data)
                self.logger.debug(f"Cached fields for API {api_id} (ordered={ordered})")
            except Exception as e:
                self.logger.warning(f"Failed to cache fields for API {api_id}: {e}")
        
        return result
    
    def reorder_fields(
        self,
        db: Session,
        api_id: int,
        field_orders: List[Dict[str, int]]  # [{"field_id": 1, "sort_order": 1}, ...]
    ) -> List[ApiField]:
        """
        重新排序API字段
        
        Args:
            db: 数据库会话
            api_id: API ID
            field_orders: 字段排序列表
            
        Returns:
            更新后的字段列表
        """
        # 获取所有字段
        fields = {f.id: f for f in self.get_api_fields(db, api_id, ordered=False)}
        
        # 更新排序
        for order_info in field_orders:
            field_id = order_info["field_id"]
            sort_order = order_info["sort_order"]
            
            if field_id in fields:
                fields[field_id].sort_order = sort_order
        
        db.commit()
        
        # 清除相关缓存
        self._invalidate_cache(api_id)
        
        # 返回排序后的字段列表
        return self.get_api_fields(db, api_id, ordered=True)
    
    def validate_field_data(
        self,
        db: Session,
        api_id: int,
        data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        验证提交的数据是否符合字段定义
        
        Args:
            db: 数据库会话
            api_id: API ID
            data: 要验证的数据
            
        Returns:
            (是否有效, 错误信息列表)
        """
        fields = self.get_api_fields(db, api_id)
        errors = []
        
        # 检查必填字段
        required_fields = [f.field_name for f in fields if f.is_required]
        for field_name in required_fields:
            if field_name not in data or data[field_name] is None:
                errors.append(f"字段 '{field_name}' 是必填的")
        # print("*"*50)

        # 验证字段类型和规则
        for field in fields:
            field_name = field.field_name
            if field_name not in data:
                continue
            value = data[field_name]
            field_errors = self._validate_field_value(field, value)
            errors.extend(field_errors)
        
        return len(errors) == 0, errors
    
    def delete(self, db: Session, *, id: int) -> bool:
        """
        删除API字段（重写父类方法以添加缓存失效）
        
        Args:
            db: 数据库会话
            id: 字段ID
            
        Returns:
            是否删除成功
        """
        # 获取字段信息以便清除缓存
        field = self.get_or_404(db, id)
        api_id = field.api_id
        
        # 调用父类删除方法
        result = super().delete(db, id=id)
        
        # 清除相关缓存
        if result:
            self._invalidate_cache(api_id)
            self.logger.info(f"Deleted field {field.field_name} for API {api_id}")
        
        return result
    
    def validate_field_structure(
        self,
        db: Session,
        api_id: int,
        data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        轻量级字段结构验证（只验证字段名称和必填字段，不验证具体内容）
        
        Args:
            db: 数据库会话
            api_id: API ID
            data: 要验证的数据
            
        Returns:
            (是否有效, 错误信息列表)
        """
        fields = self.get_api_fields(db, api_id)
        errors = []
        
        # 获取API定义的字段名称
        api_field_names = {f.field_name for f in fields}
        required_fields = {f.field_name for f in fields if f.is_required}
        
        # 获取数据中的字段名称
        data_field_names = set(data.keys())
        
        # 检查必填字段是否存在
        missing_required = required_fields - data_field_names
        if missing_required:
            errors.extend([f"缺少必填字段: {field}" for field in missing_required])
        
        # 检查是否有多余字段
        extra_fields = data_field_names - api_field_names
        if extra_fields:
            errors.extend([f"未定义的字段: {field}" for field in extra_fields])
        
        return len(errors) == 0, errors
    
    def validate_request_data(
        self,
        db: Session,
        api_id: int,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证请求数据（支持单条和批量数据）
        优化版本：批量数据只验证第一条的字段结构，提高性能
        
        Args:
            db: 数据库会话
            api_id: API ID
            request_data: 请求数据（可以是单条数据或包含data数组的批量数据）
            
        Returns:
            验证后的数据
            
        Raises:
            ValidationException: 数据验证失败
        """
        print(f"*** 开始数据验证，数据类型: {type(request_data)} ***")
        
        # 检查是否为批量数据格式
        if isinstance(request_data, list):
            # 直接传入数组格式的数据
            print(f"*** 批量数据验证（数组格式），共 {len(request_data)} 条数据 ***")
            if len(request_data) == 0:
                raise ValidationException("批量数据不能为空")
            
            # 只验证第一条数据的字段结构
            first_item = request_data[0]
            is_valid, errors = self.validate_field_structure(db, api_id, first_item)
            if not is_valid:
                raise ValidationException(f"字段结构验证失败: {'; '.join(errors)}")
            
            print(f"*** 批量数据字段结构验证通过，跳过详细验证 ***")
            return request_data
            
        elif isinstance(request_data, dict) and 'data' in request_data and isinstance(request_data['data'], list):
            # 包装格式的批量数据: {"data": [{...}, {...}]}
            data_list = request_data['data']
            print(f"*** 批量数据验证（包装格式），共 {len(data_list)} 条数据 ***")
            
            if len(data_list) == 0:
                raise ValidationException("批量数据不能为空")
            
            # 只验证第一条数据的字段结构
            first_item = data_list[0]
            is_valid, errors = self.validate_field_structure(db, api_id, first_item)
            if not is_valid:
                raise ValidationException(f"字段结构验证失败: {'; '.join(errors)}")
            
            print(f"*** 批量数据字段结构验证通过，跳过详细验证 ***")
            return request_data
        
        else:
            # 单条数据验证（保持原有详细验证逻辑）
            print(f"*** 单条数据验证 ***")
            is_valid, errors = self.validate_field_data(db, api_id, request_data)
            if not is_valid:
                raise ValidationException(f"数据验证失败: {'; '.join(errors)}")
            
            return request_data
    
    def process_custom_api(
        self,
        db: Session,
        api_config: CustomApi,
        validated_data: Dict[str, Any],
        customer_id: Optional[int] = None,
        batch_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理自定义API逻辑（支持单条和批量数据）
        
        Args:
            db: 数据库会话
            api_config: API配置
            validated_data: 验证后的数据（可以是单条数据、数组或包含data数组的对象）
            customer_id: 客户ID（通过认证获取）
            batch_id: 批次ID（用于批量上传）
            request_id: 请求ID（用于标识单次请求）
            
        Returns:
            处理结果
        """
        from app.models.log import DataUpload
        import uuid
        import time
        
        start_time = time.time()
        self.logger.debug(f"[API处理] 开始处理API: {api_config.api_code}, batch_id: {batch_id}")
        
        try:
            # 检查是否为批量数据
            data_type_check_time = time.time()
            # if isinstance(validated_data, list):
                # 直接数组格式的批量数据
            self.logger.debug(f"[API处理] 检测到直接数组格式批量数据，耗时: {(time.time() - data_type_check_time)*1000:.2f}ms")
            result = self._process_batch_data(
                db, api_config, validated_data, customer_id, batch_id, request_id
            )
            # elif isinstance(validated_data, dict) and 'data' in validated_data and isinstance(validated_data['data'], list):
            #     # 包装格式的批量数据
            #     self.logger.debug(f"[API处理] 检测到包装格式批量数据，耗时: {(time.time() - data_type_check_time)*1000:.2f}ms")
            #     data_list = validated_data['data']
            #     result = self._process_batch_data(
            #         db, api_config, data_list, customer_id, batch_id, request_id
            #     )
            #     # 保持原有的包装格式
            #     format_time = time.time()
            #     result['data'] = {
            #         'items': result['data'],
            #         'total_count': result.get('total_count', len(data_list))
            #     }
            #     self.logger.debug(f"[API处理] 包装格式转换耗时: {(time.time() - format_time)*1000:.2f}ms")
            # else:
            #     # 单条数据处理（原有逻辑）
            #     self.logger.debug(f"[API处理] 检测到单条数据，耗时: {(time.time() - data_type_check_time)*1000:.2f}ms")
            #     result = self._process_single_data(
            #         db, api_config, validated_data, customer_id, batch_id, request_id
            #     )
            
            total_time = time.time() - start_time
            self.logger.debug(f"[API处理] API处理完成: {api_config.api_code}, 总耗时: {total_time*1000:.2f}ms")
            
            if total_time > 0.5:  # 超过500ms记录警告
                self.logger.warning(f"[API处理] API处理耗时较长: {api_config.api_code}, 耗时: {total_time*1000:.2f}ms")
            
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(f"[API处理] API处理异常: {api_config.api_code}, 耗时: {total_time*1000:.2f}ms, 错误: {str(e)}")
            raise
    
    def _process_single_data(
        self,
        db: Session,
        api_config: CustomApi,
        validated_data: Dict[str, Any],
        customer_id: Optional[int] = None,
        batch_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理单条数据
        
        Args:
            db: 数据库会话
            api_config: API配置
            validated_data: 验证后的单条数据
            customer_id: 客户ID
            batch_id: 批次ID
            request_id: 请求ID
            
        Returns:
            处理结果
        """
        import uuid
        import time
        
        start_time = time.time()
        self.logger.debug(f"[单条数据处理] 开始处理单条数据: customer_id={customer_id}, batch_id={batch_id}")
        
        # 生成唯一的上传ID
        uuid_time = time.time()
        upload_id = str(uuid.uuid4())
        self.logger.debug(f"[单条数据处理] UUID生成耗时: {(time.time() - uuid_time)*1000:.2f}ms")
        
        try:
            # 创建数据上传记录
            if customer_id:
                record_create_time = time.time()
                upload_record = DataUpload(
                    customer_id=customer_id,
                    api_id=api_config.id,
                    upload_id=upload_id,
                    batch_id=batch_id,
                    data_content=json.dumps(validated_data, ensure_ascii=False),
                    status='completed',
                    processed_at=datetime.utcnow(),
                    record_count=1,
                    file_type='json'
                )
                self.logger.debug(f"[单条数据处理] 数据记录对象创建耗时: {(time.time() - record_create_time)*1000:.2f}ms")
                
                db_add_time = time.time()
                db.add(upload_record)
                self.logger.debug(f"[单条数据处理] 数据库add耗时: {(time.time() - db_add_time)*1000:.2f}ms")
                
                db_commit_time = time.time()
                db.commit()
                self.logger.debug(f"[单条数据处理] 数据库commit耗时: {(time.time() - db_commit_time)*1000:.2f}ms")
                
                db_refresh_time = time.time()
                db.refresh(upload_record)
                self.logger.debug(f"[单条数据处理] 数据库refresh耗时: {(time.time() - db_refresh_time)*1000:.2f}ms")
                
                self.logger.info(
                    f"数据上传记录已保存: upload_id={upload_id}, "
                    f"customer_id={customer_id}, api_id={api_config.id}, "
                    f"batch_id={batch_id}"
                )
                
                # 返回包含上传记录信息的响应
                response_time = time.time()
                result = {
                    "success": True,
                    "message": f"API {api_config.api_code} 处理成功",
                    # "data": validated_data,
                    "upload_id": upload_id,
                    "batch_id": batch_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.logger.debug(f"[单条数据处理] 响应构建耗时: {(time.time() - response_time)*1000:.2f}ms")
                
                total_time = time.time() - start_time
                self.logger.debug(f"[单条数据处理] 单条数据处理完成，总耗时: {total_time*1000:.2f}ms")
                
                if total_time > 0.3:  # 超过300ms记录警告
                    self.logger.warning(f"[单条数据处理] 单条数据处理耗时较长: {total_time*1000:.2f}ms")
                
                return result
            else:
                # 如果没有平台信息，只返回简单响应（向后兼容）
                response_time = time.time()
                result = {
                    "success": True,
                    "message": f"API {api_config.api_code} 处理成功",
                    "data": validated_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.logger.debug(f"[单条数据处理] 简单响应构建耗时: {(time.time() - response_time)*1000:.2f}ms")
                
                total_time = time.time() - start_time
                self.logger.debug(f"[单条数据处理] 单条数据处理完成（无平台信息），总耗时: {total_time*1000:.2f}ms")
                
                return result
                
        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(f"[单条数据处理] 保存数据上传记录失败，耗时: {total_time*1000:.2f}ms, 错误: {str(e)}")
            # 即使保存失败，也返回成功响应，避免影响API调用
            return {
                "success": True,
                "message": f"API {api_config.api_code} 处理成功",
                "data": validated_data,
                "warning": "数据记录保存失败",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _process_batch_data(
        self,
        db: Session,
        api_config: CustomApi,
        data_list: List[Dict[str, Any]],
        customer_id: Optional[int] = None,
        batch_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理批量数据
        
        Args:
            db: 数据库会话
            api_config: API配置
            data_list: 验证后的数据列表
            customer_id: 客户ID
            batch_id: 批次ID
            request_id: 请求ID
            
        Returns:
            批量处理结果
        """
        import uuid
        import time
        
        start_time = time.time()
        data_count = len(data_list)
        self.logger.debug(f"[批量数据处理] 开始处理批量数据: customer_id={customer_id}, 数据量={data_count}")
        
        # 如果没有提供batch_id，生成一个
        batch_id_time = time.time()
        if not batch_id:
            batch_id = str(uuid.uuid4())
        self.logger.debug(f"[批量数据处理] batch_id处理耗时: {(time.time() - batch_id_time)*1000:.2f}ms")
        
        try:
            # 数据处理逻辑（这里可以添加实际的批量处理逻辑）
            processing_time = time.time()
            
            # 保存数据到MinIO
            saved_object_path = None
            try:
                self.logger.info(f"🔄 [批量数据处理] 开始保存数据到MinIO...")
                self.logger.info(f"   批次ID: {batch_id}")
                self.logger.info(f"   客户ID: {customer_id}")
                self.logger.info(f"   API代码: {api_config.api_code}")
                self.logger.info(f"   请求ID: {request_id}")
                self.logger.info(f"   数据量: {data_count} 条")
                
                from app.services.minio_service import minio_service
                
                # 准备保存的数据
                save_data = {
                    "api_code": api_config.api_code,
                    "api_id": api_config.id,
                    "request_id": request_id,
                    "customer_id": customer_id,
                    "data_list": data_list,
                    "processing_info": {
                        "total_count": data_count,
                        "processed_at": datetime.utcnow().isoformat()
                    }
                }
                
                # 生成文件名
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"{api_config.api_code}_{request_id}_{timestamp}.json"
                
                self.logger.info(f"   生成文件名: {filename}")
                
                # 保存数据到MinIO
                self.logger.info(f"🚀 [批量数据处理] 调用MinIO服务保存数据...")
                saved_object_path = minio_service.save_batch_data(batch_id, save_data, filename)
                
                self.logger.info(f"✅ [批量数据处理] 数据已成功保存到MinIO!")
                self.logger.info(f"   MinIO对象路径: {saved_object_path}")
                self.logger.info(f"   存储桶: cepiec-read-data")
                
                # 保存记录到api_usage_logs表
                try:
                    from app.models.log import ApiUsageLog
                    import uuid
                    
                    self.logger.info(f"💾 [批量数据处理] 开始保存使用日志到数据库...")
                    
                    # 计算数据大小（JSON字符串的字节数）
                    json_data = json.dumps(save_data, ensure_ascii=False)
                    data_size = len(json_data.encode('utf-8'))
                    
                    # 构建存储路径（格式：/bucket_name/batchfile/batch_id/filename.json）
                    storage_path = f"/{settings.MINIO_BUCKET_NAME}/batchfile/{batch_id}/{filename}"
                    
                    # 创建API使用日志记录
                    usage_log = ApiUsageLog(
                        customer_id=customer_id,
                        api_id=api_config.id,
                        request_id=request_id,
                        client_ip="127.0.0.1",  # 批量处理时的默认IP
                        http_method="POST",
                        request_url=f"/api/v1/custom/{api_config.api_code}/batch",
                        request_headers={"Content-Type": "application/json"},
                        request_params={"batch_id": batch_id},
                        file_path=storage_path,  # 保存存储路径
                        response_status=200,
                        processing_time=time.time() - start_time,
                        batch_id=batch_id,
                        data_size=data_size,
                        record_count=data_count,
                        user_agent="BatchProcessor/1.0",
                        needread=False,
                        is_encrypted=False
                    )
                    
                    # 保存到数据库
                    db.add(usage_log)
                    db.commit()
                    db.refresh(usage_log)
                    
                    self.logger.info(f"✅ [批量数据处理] 使用日志已保存到数据库!")
                    self.logger.info(f"   请求ID: {request_id}")
                    self.logger.info(f"   数据库记录ID: {usage_log.id}")
                    self.logger.info(f"   存储路径: {storage_path}")
                    
                except Exception as db_error:
                    self.logger.error(f"❌ [批量数据处理] 保存使用日志到数据库失败: {str(db_error)}")
                    self.logger.error(f"   错误详情: {type(db_error).__name__}: {db_error}")
                    # 数据库保存失败不影响主流程，数据已经保存到MinIO
                    try:
                        db.rollback()
                    except Exception:
                        pass
                
            except Exception as save_error:
                self.logger.error(f"❌ [批量数据处理] 数据保存到MinIO失败: {str(save_error)}")
                self.logger.error(f"   错误详情: {type(save_error).__name__}: {save_error}")
                # 保存失败不影响主流程，继续处理
            
            # 目前只是简单返回，实际可能需要批量插入数据库等操作
            self.logger.debug(f"[批量数据处理] 数据处理逻辑耗时: {(time.time() - processing_time)*1000:.2f}ms")
            
            self.logger.info(
                f"批量数据处理完成: batch_id={batch_id}, "
                f"customer_id={customer_id}, api_id={api_config.id}, "
                f"记录数={data_count}"
            )
            
            # 返回批量处理结果
            response_time = time.time()
            result = {
                "success": True,
                "message": f"API {api_config.api_code} 批量处理完成",
                "batch_id": batch_id,
                "total_count": data_count,
                "timestamp": datetime.utcnow().isoformat(),
                "data_saved": saved_object_path is not None,  # 标识数据是否成功保存到MinIO
                "storage_type": "minio",  # 存储类型
                "bucket_name": "cepiec-read-data",  # 存储桶名称
                "object_path": saved_object_path,  # MinIO对象路径
                "minio_full_path": minio_full_path if 'minio_full_path' in locals() else None,  # MinIO完整路径
                "database_record": {
                    "request_id": request_id,
                    "record_id": usage_log.id if 'usage_log' in locals() else None,
                    "status": "completed" if 'usage_log' in locals() else "storage_only",
                    "storage_path": storage_path if 'storage_path' in locals() else None
                }
            }
            self.logger.debug(f"[批量数据处理] 响应构建耗时: {(time.time() - response_time)*1000:.2f}ms")
            
            total_time = time.time() - start_time
            self.logger.debug(f"[批量数据处理] 批量数据处理完成，总耗时: {total_time*1000:.2f}ms, 数据量: {data_count}")
            
            if total_time > 1.0:  # 超过1秒记录警告
                self.logger.warning(f"[批量数据处理] 批量数据处理耗时较长: {total_time*1000:.2f}ms, 数据量: {data_count}")
            
            return result
                
        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(f"[批量数据处理] 批量数据处理失败，耗时: {total_time*1000:.2f}ms, 数据量: {data_count}, 错误: {str(e)}")
            
            # 返回错误响应
            return {
                "success": False,
                "message": f"API {api_config.api_code} 批量处理失败",
                "batch_id": batch_id,
                "total_count": data_count,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _validate_field_value(self, field: ApiField, value: Any) -> List[str]:
        """
        验证单个字段值
        
        Args:
            field: 字段定义
            value: 字段值
            
        Returns:
            错误信息列表
        """
        errors = []
        field_name = field.field_name
        # 类型验证
        if field.field_type == FieldTypeEnum.STRING.value:
            if not isinstance(value, str):
                errors.append(f"字段 '{field_name}' 必须是字符串类型")
            elif field.max_length and len(value) > field.max_length:
                errors.append(f"字段 '{field_name}' 长度不能超过 {field.max_length}")
            elif field.min_length and len(value) < field.min_length:
                errors.append(f"字段 '{field_name}' 长度不能少于 {field.min_length}")
        
        elif field.field_type == FieldTypeEnum.INTEGER.value:
            if not isinstance(value, int):
                errors.append(f"字段 '{field_name}' 必须是整数类型")
            elif field.max_value is not None and value > field.max_value:
                errors.append(f"字段 '{field_name}' 不能大于 {field.max_value}")
            elif field.min_value is not None and value < field.min_value:
                errors.append(f"字段 '{field_name}' 不能小于 {field.min_value}")
        
        elif field.field_type == FieldTypeEnum.FLOAT.value:
            if not isinstance(value, (int, float)):
                errors.append(f"字段 '{field_name}' 必须是数字类型")
            elif field.max_value is not None and value > field.max_value:
                errors.append(f"字段 '{field_name}' 不能大于 {field.max_value}")
            elif field.min_value is not None and value < field.min_value:
                errors.append(f"字段 '{field_name}' 不能小于 {field.min_value}")
        
        elif field.field_type == FieldTypeEnum.BOOLEAN.value:
            if not isinstance(value, bool):
                errors.append(f"字段 '{field_name}' 必须是布尔类型")
        
        elif field.field_type == FieldTypeEnum.DATE.value:
            if not isinstance(value, str):
                errors.append(f"字段 '{field_name}' 必须是日期字符串")
            else:
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    errors.append(f"字段 '{field_name}' 日期格式不正确，应为 YYYY-MM-DD")
        
        elif field.field_type == FieldTypeEnum.DATETIME.value:
            if not isinstance(value, str):
                errors.append(f"字段 '{field_name}' 必须是日期时间字符串")
            else:
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    errors.append(f"字段 '{field_name}' 日期时间格式不正确")
        
        # 允许值验证
        if field.allowed_values:
            try:
                allowed = json.loads(field.allowed_values)
                if value not in allowed:
                    errors.append(f"字段 '{field_name}' 的值必须是 {allowed} 中的一个")
            except json.JSONDecodeError:
                pass
        
        # 正则表达式验证
        if field.validation_regex and isinstance(value, str):
            try:
                if not re.match(field.validation_regex, value):
                    errors.append(f"字段 '{field_name}' 格式不符合要求")
            except re.error:
                pass
        return errors
    
    def _is_valid_field_name(self, field_name: str) -> bool:
        """
        验证字段名格式
        
        Args:
            field_name: 字段名
            
        Returns:
            是否有效
        """
        # 字段名规则：1-50个字符，只能包含字母、数字和下划线，不能以数字开头
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]{0,49}$'
        return bool(re.match(pattern, field_name))
    
    def validate_business_rules(self, db: Session, obj_data: Dict[str, Any]) -> None:
        """
        验证字段业务规则
        
        Args:
            db: 数据库会话
            obj_data: 对象数据
            
        Raises:
            BusinessException: 业务规则验证失败
        """
        # 检查字段名格式
        field_name = obj_data.get("field_name")
        if field_name and not self._is_valid_field_name(field_name):
            raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "字段名格式不正确")
        
        # 检查字段类型
        field_type = obj_data.get("field_type")
        if field_type and field_type not in [ft.value for ft in FieldTypeEnum]:
            raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "不支持的字段类型")
        
        # 检查长度限制
        min_length = obj_data.get("min_length")
        max_length = obj_data.get("max_length")
        if min_length is not None and max_length is not None:
            if min_length > max_length:
                raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "最小长度不能大于最大长度")
        
        # 检查数值限制
        min_value = obj_data.get("min_value")
        max_value = obj_data.get("max_value")
        if min_value is not None and max_value is not None:
            if min_value > max_value:
                raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "最小值不能大于最大值")
        
        # 验证正则表达式
        validation_regex = obj_data.get("validation_regex")
        if validation_regex:
            try:
                re.compile(validation_regex)
            except re.error:
                raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "正则表达式格式不正确")
        
        # 验证允许值JSON格式
        allowed_values = obj_data.get("allowed_values")
        if allowed_values:
            try:
                json.loads(allowed_values)
            except json.JSONDecodeError:
                raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "允许值必须是有效的JSON格式")
    
    def get_with_fields(self, db: Session, api_id: int) -> Optional[CustomApi]:
        """
        获取API详细信息（包含字段定义）
        
        Args:
            db: 数据库会话
            api_id: API ID
            
        Returns:
            API对象（包含字段信息）
        """
        api = db.query(CustomApi).filter(CustomApi.id == api_id).first()
        if api:
            # 预加载字段信息
            api.fields = db.query(ApiField).filter(
                ApiField.api_id == api_id
            ).order_by(ApiField.sort_order).all()
        return api
    



# 全局服务实例
custom_api_service = CustomApiService()
api_field_service = ApiFieldService()


if __name__ == "__main__":
    import logging
    logger = logging.getLogger(__name__)
    logger.info("API服务定义完成")