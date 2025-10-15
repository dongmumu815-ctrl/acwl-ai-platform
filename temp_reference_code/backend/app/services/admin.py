#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统管理服务模块

提供管理员用户和系统配置的业务逻辑处理功能。

Author: System
Date: 2024
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
import json
from pathlib import Path

from .base import BaseService
from .auth import auth_service, jwt_service
from app.models.admin import AdminUser, SystemConfig
from app.models.customer import Customer
from app.models.api import CustomApi
from app.models.log import ApiUsageLog, DataUpload
from app.core.exceptions import (
    ValidationException,
    ConflictException,
    NotFoundException,
    AuthorizationException
)
from app.core.business_codes import BusinessException, BusinessCode, BusinessResponse
from app.schemas.admin import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminLoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigQuery,
    ConfigBatchUpdateRequest,
    SystemStatsResponse,
    SystemHealthResponse
)
from app.schemas.base import PaginationInfo


class AdminUserService(BaseService[AdminUser, AdminUserCreate, AdminUserUpdate]):
    """
    管理员用户服务
    
    提供管理员用户管理的业务逻辑处理
    """
    
    def __init__(self):
        super().__init__(AdminUser)
    
    def create_admin(
        self,
        db: Session,
        admin_data: AdminUserCreate,
        created_by: Optional[int] = None
    ) -> AdminUser:
        """
        创建管理员用户
        
        Args:
            db: 数据库会话
            admin_data: 管理员创建数据
            created_by: 创建者ID
            
        Returns:
            创建的管理员对象
            
        Raises:
            ConflictException: 用户名或邮箱已存在
            ValidationException: 数据验证失败
        """
        # 检查用户名是否已存在
        if self.exists(db, filters={"username": admin_data.username}):
            raise ConflictException(f"用户名 '{admin_data.username}' 已存在")
        
        # 检查邮箱是否已存在
        if self.exists(db, filters={"email": admin_data.email}):
            raise ConflictException(f"邮箱 '{admin_data.email}' 已存在")
        
        # 哈希密码
        password_hash = auth_service.get_password_hash(admin_data.password)
        
        # 准备创建数据
        create_data = admin_data.dict(exclude={"password", "confirm_password"})
        create_data.update({
            "password_hash": password_hash,
            "created_by": created_by
        })
        
        # 创建管理员
        admin = self.create(db, obj_in=create_data)
        
        self.logger.info(f"Created admin user: {admin.username} (ID: {admin.id})")
        return admin
    
    def update_admin(
        self,
        db: Session,
        admin_id: int,
        admin_data: AdminUserUpdate,
        updated_by: Optional[int] = None
    ) -> AdminUser:
        """
        更新管理员信息
        
        Args:
            db: 数据库会话
            admin_id: 管理员ID
            admin_data: 更新数据
            updated_by: 更新者ID
            
        Returns:
            更新后的管理员对象
            
        Raises:
            NotFoundException: 管理员不存在
            ConflictException: 邮箱已被其他用户使用
        """
        admin = self.get_or_404(db, admin_id)
        
        # 检查邮箱是否被其他用户使用
        if admin_data.email and admin_data.email != admin.email:
            existing = db.query(AdminUser).filter(
                AdminUser.email == admin_data.email,
                AdminUser.id != admin_id
            ).first()
            if existing:
                raise ConflictException(f"邮箱 '{admin_data.email}' 已被其他用户使用")
        
        # 更新数据
        update_data = admin_data.dict(exclude_unset=True)
        if updated_by:
            update_data["updated_by"] = updated_by
        
        updated_admin = self.update(db, db_obj=admin, obj_in=update_data)
        
        self.logger.info(f"Updated admin user: {admin.username} (ID: {admin.id})")
        return updated_admin
    
    def login_admin(
        self,
        db: Session,
        login_data: AdminLoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        管理员登录
        
        Args:
            db: 数据库会话
            login_data: 登录数据
            ip_address: IP地址
            user_agent: 用户代理
            
        Returns:
            登录响应数据
            
        Raises:
            ValidationException: 登录失败
        """
        # 认证管理员
        admin = auth_service.authenticate_admin(
            db, login_data.username, login_data.password
        )
        
        if not admin:
            raise ValidationException("用户名或密码错误")
        
        # 更新登录信息
        admin.last_login_at = datetime.utcnow()
        admin.last_login_ip = ip_address
        admin.login_count = (admin.login_count or 0) + 1
        
        db.commit()
        
        # 生成JWT令牌
        access_token = jwt_service.create_access_token(
            subject=admin.id,
            user_type="admin"
        )
        
        refresh_token = jwt_service.create_refresh_token(
            subject=admin.id,
            user_type="admin"
        )
        
        self.logger.info(f"Admin login: {admin.username} from {ip_address}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,  # 1小时
            "admin": admin
        }
    
    def change_password(
        self,
        db: Session,
        admin_id: int,
        password_data: PasswordChangeRequest
    ) -> bool:
        """
        修改管理员密码
        
        Args:
            db: 数据库会话
            admin_id: 管理员ID
            password_data: 密码修改数据
            
        Returns:
            是否修改成功
            
        Raises:
            ValidationException: 当前密码错误
        """
        admin = self.get_or_404(db, admin_id)
        
        # 验证当前密码
        if not auth_service.verify_password(password_data.current_password, admin.password_hash):
            raise ValidationException("当前密码错误")
        
        # 更新密码
        admin.password_hash = auth_service.get_password_hash(password_data.new_password)
        admin.password_changed_at = datetime.utcnow()
        
        db.commit()
        
        self.logger.info(f"Changed password for admin: {admin.username} (ID: {admin.id})")
        return True
    
    def reset_password(
        self,
        db: Session,
        admin_id: int,
        password_data: PasswordResetRequest,
        reset_by: Optional[int] = None
    ) -> bool:
        """
        重置管理员密码
        
        Args:
            db: 数据库会话
            admin_id: 管理员ID
            password_data: 密码重置数据
            reset_by: 重置者ID
            
        Returns:
            是否重置成功
        """
        admin = self.get_or_404(db, admin_id)
        
        # 更新密码
        admin.password_hash = auth_service.get_password_hash(password_data.new_password)
        admin.password_changed_at = datetime.utcnow()
        admin.password_reset_at = datetime.utcnow()
        if reset_by:
            admin.updated_by = reset_by
        
        db.commit()
        
        self.logger.info(f"Reset password for admin: {admin.username} (ID: {admin.id})")
        return True
    
    def activate_admin(self, db: Session, admin_id: int) -> AdminUser:
        """
        激活管理员账户
        
        Args:
            db: 数据库会话
            admin_id: 管理员ID
            
        Returns:
            更新后的管理员对象
        """
        admin = self.get_or_404(db, admin_id)
        
        admin.is_active = True
        admin.activated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(admin)
        
        self.logger.info(f"Activated admin: {admin.username} (ID: {admin.id})")
        return admin
    
    def deactivate_admin(self, db: Session, admin_id: int) -> AdminUser:
        """
        停用管理员账户
        
        Args:
            db: 数据库会话
            admin_id: 管理员ID
            
        Returns:
            更新后的管理员对象
        """
        admin = self.get_or_404(db, admin_id)
        
        admin.is_active = False
        admin.deactivated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(admin)
        
        self.logger.info(f"Deactivated admin: {admin.username} (ID: {admin.id})")
        return admin
    
    def unlock_admin(self, db: Session, admin_id: int) -> AdminUser:
        """
        解锁管理员账户
        
        Args:
            db: 数据库会话
            admin_id: 管理员ID
            
        Returns:
            更新后的管理员对象
        """
        admin = self.get_or_404(db, admin_id)
        
        admin.is_locked = False
        admin.failed_login_count = 0
        admin.locked_at = None
        admin.locked_until = None
        
        db.commit()
        db.refresh(admin)
        
        self.logger.info(f"Unlocked admin: {admin.username} (ID: {admin.id})")
        return admin
    
    def search_admins(
        self,
        db: Session,
        *,
        keyword: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_locked: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AdminUser], PaginationInfo]:
        """
        搜索管理员
        
        Args:
            db: 数据库会话
            keyword: 关键词（用户名、邮箱、姓名）
            role: 角色
            is_active: 是否激活
            is_locked: 是否锁定
            created_after: 创建时间之后
            created_before: 创建时间之前
            page: 页码
            page_size: 每页大小
            
        Returns:
            (管理员列表, 分页信息)
        """
        query = db.query(AdminUser)
        
        # 关键词搜索
        if keyword:
            search_filter = or_(
                AdminUser.username.ilike(f"%{keyword}%"),
                AdminUser.email.ilike(f"%{keyword}%"),
                AdminUser.real_name.ilike(f"%{keyword}%")
            )
            query = query.filter(search_filter)
        
        # 角色过滤
        if role:
            query = query.filter(AdminUser.role == role)
        
        # 状态过滤
        if is_active is not None:
            query = query.filter(AdminUser.is_active == is_active)
        
        if is_locked is not None:
            query = query.filter(AdminUser.is_locked == is_locked)
        
        # 日期过滤
        if created_after:
            query = query.filter(AdminUser.created_at >= created_after)
        
        if created_before:
            query = query.filter(AdminUser.created_at <= created_before)
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        admins = query.order_by(AdminUser.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # 创建分页信息
        pagination = PaginationInfo.create(
            page=page,
            size=page_size,
            total=total
        )
        
        return admins, pagination
    
    def validate_business_rules(self, db: Session, obj_data: Dict[str, Any]) -> None:
        """
        验证管理员业务规则
        
        Args:
            db: 数据库会话
            obj_data: 对象数据
            
        Raises:
            BusinessException: 业务规则验证失败
        """
        # 检查用户名格式
        username = obj_data.get("username")
        if username and not self._is_valid_username(username):
            raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "用户名格式不正确，只能包含字母、数字、下划线和连字符")
        
        # 检查角色权限
        role = obj_data.get("role")
        if role and role not in ["super_admin", "admin", "operator", "viewer"]:
            raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "无效的角色类型")
    
    def _is_valid_username(self, username: str) -> bool:
        """
        验证用户名格式
        
        Args:
            username: 用户名
            
        Returns:
            是否有效
        """
        return (
            len(username) >= 3 and
            len(username) <= 50 and
            username.replace('_', '').replace('-', '').isalnum() and
            not username.startswith('_') and
            not username.startswith('-')
        )


class SystemConfigService(BaseService[SystemConfig, SystemConfigCreate, SystemConfigUpdate]):
    """
    系统配置服务
    
    提供系统配置管理的业务逻辑处理
    """
    
    def __init__(self):
        super().__init__(SystemConfig)
    
    def create_config(
        self,
        db: Session,
        config_data: SystemConfigCreate,
        created_by: Optional[int] = None
    ) -> SystemConfig:
        """
        创建系统配置
        
        Args:
            db: 数据库会话
            config_data: 配置创建数据
            created_by: 创建者ID
            
        Returns:
            创建的配置对象
            
        Raises:
            ConflictException: 配置键已存在
        """
        # 检查配置键是否已存在
        if self.exists(db, filters={"config_key": config_data.config_key}):
            raise ConflictException(f"配置键 '{config_data.config_key}' 已存在")
        
        # 准备创建数据
        create_data = config_data.dict()
        create_data.update({
            "created_by": created_by
        })
        
        # 创建配置
        config = self.create(db, obj_in=create_data)
        
        self.logger.info(f"Created config: {config.config_key}")
        return config
    
    def update_config(
        self,
        db: Session,
        config_id: int,
        config_data: SystemConfigUpdate,
        updated_by: Optional[int] = None
    ) -> SystemConfig:
        """
        更新系统配置
        
        Args:
            db: 数据库会话
            config_id: 配置ID
            config_data: 更新数据
            updated_by: 更新者ID
            
        Returns:
            更新后的配置对象
        """
        config = self.get_or_404(db, config_id)
        
        # 更新数据
        update_data = config_data.dict(exclude_unset=True)
        if updated_by:
            update_data["updated_by"] = updated_by
        
        updated_config = self.update(db, db_obj=config, obj_in=update_data)
        
        self.logger.info(f"Updated config: {config.config_key}")
        return updated_config
    
    def get_config_by_key(
        self,
        db: Session,
        config_key: str
    ) -> Optional[SystemConfig]:
        """
        根据配置键获取配置
        
        Args:
            db: 数据库会话
            config_key: 配置键
            
        Returns:
            配置对象或None
        """
        return db.query(SystemConfig).filter(
            SystemConfig.config_key == config_key
        ).first()
    
    def get_config_value(
        self,
        db: Session,
        config_key: str,
        default_value: Any = None
    ) -> Any:
        """
        获取配置值
        
        Args:
            db: 数据库会话
            config_key: 配置键
            default_value: 默认值
            
        Returns:
            配置值
        """
        config = self.get_config_by_key(db, config_key)
        if not config:
            return default_value
        
        return config.get_typed_value()
    
    def set_config_value(
        self,
        db: Session,
        config_key: str,
        config_value: Any,
        value_type: str = "string",
        description: Optional[str] = None,
        updated_by: Optional[int] = None
    ) -> SystemConfig:
        """
        设置配置值
        
        Args:
            db: 数据库会话
            config_key: 配置键
            config_value: 配置值
            value_type: 值类型
            description: 描述
            updated_by: 更新者ID
            
        Returns:
            配置对象
        """
        config = self.get_config_by_key(db, config_key)
        
        if config:
            # 更新现有配置
            config.config_value = str(config_value)
            config.config_type = value_type  # 修正字段名：value_type -> config_type
            if description:
                config.description = description
            if updated_by:
                config.updated_by = updated_by
            
            db.commit()
            db.refresh(config)
        else:
            # 创建新配置
            config_data = SystemConfigCreate(
                config_key=config_key,
                config_value=str(config_value),
                value_type=value_type,
                description=description or f"Auto-created config: {config_key}"
            )
            config = self.create_config(db, config_data, updated_by)
        
        return config
    
    def batch_update_configs(
        self,
        db: Session,
        batch_data: ConfigBatchUpdateRequest,
        updated_by: Optional[int] = None
    ) -> List[SystemConfig]:
        """
        批量更新配置
        
        Args:
            db: 数据库会话
            batch_data: 批量更新数据
            updated_by: 更新者ID
            
        Returns:
            更新后的配置列表
        """
        updated_configs = []
        
        for config_update in batch_data.configs:
            try:
                # 从字典中获取值，使用默认值处理可能不存在的键
                config_key = config_update.get('key')
                config_value = config_update.get('value')
                # 使用默认值'string'替代value_type
                config_type = config_update.get('type', 'string')
                description = config_update.get('description')
                
                config = self.set_config_value(
                    db,
                    config_key,
                    config_value,
                    config_type,
                    description,
                    updated_by
                )
                updated_configs.append(config)
            except Exception as e:
                self.logger.error(f"Failed to update config {config_update.get('key', 'unknown')}: {e}")
                if not batch_data.ignore_errors:
                    raise
        
        self.logger.info(f"Batch updated {len(updated_configs)} configs")
        return updated_configs
    
    def search_configs(
        self,
        db: Session,
        query_params: SystemConfigQuery,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SystemConfig], PaginationInfo]:
        """
        搜索系统配置
        
        Args:
            db: 数据库会话
            query_params: 查询参数
            page: 页码
            page_size: 每页大小
            
        Returns:
            (配置列表, 分页信息)
        """
        query = db.query(SystemConfig)
        
        # 关键词搜索
        if query_params.keyword:
            search_filter = or_(
                SystemConfig.config_key.ilike(f"%{query_params.keyword}%"),
                SystemConfig.description.ilike(f"%{query_params.keyword}%")
            )
            query = query.filter(search_filter)
        
        # 分类过滤 - 数据库中暂无category字段，暂时注释掉
        # if query_params.category:
        #     query = query.filter(SystemConfig.category == query_params.category)
        
        # 值类型过滤
        if query_params.config_type:
            query = query.filter(SystemConfig.config_type == query_params.config_type)
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        configs = query.order_by(SystemConfig.config_key).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # 创建分页信息
        pagination = PaginationInfo.create(
            page=page,
            size=page_size,
            total=total
        )
        
        return configs, pagination
    
    def get_configs_by_category(
        self,
        db: Session,
        category: str
    ) -> List[SystemConfig]:
        """
        根据分类获取配置列表
        
        Args:
            db: 数据库会话
            category: 分类
            
        Returns:
            配置列表
        """
        return db.query(SystemConfig).filter(
            SystemConfig.category == category
        ).order_by(SystemConfig.config_key).all()
    
    def export_configs(
        self,
        db: Session,
        category: Optional[str] = None
    ) -> str:
        """
        导出配置
        
        Args:
            db: 数据库会话
            category: 分类（可选）
            
        Returns:
            导出文件路径
        """
        query = db.query(SystemConfig)
        
        if category:
            query = query.filter(SystemConfig.category == category)
        
        configs = query.order_by(SystemConfig.config_key).all()
        
        # 准备导出数据
        export_data = []
        for config in configs:
            export_data.append({
                "config_key": config.config_key,
                "config_value": config.config_value,
                "value_type": config.value_type,
                "category": config.category,
                "description": config.description,
                "created_at": config.created_at.isoformat() if config.created_at else None,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None
            })
        
        # 保存文件
        filename = f"system_configs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        if category:
            filename = f"system_configs_{category}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        file_path = Path("exports") / filename
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Exported {len(configs)} configs to {file_path}")
        return str(file_path)
    
    def validate_business_rules(self, db: Session, obj_data: Dict[str, Any]) -> None:
        """
        验证配置业务规则
        
        Args:
            db: 数据库会话
            obj_data: 对象数据
            
        Raises:
            BusinessException: 业务规则验证失败
        """
        # 检查配置键格式
        config_key = obj_data.get("config_key")
        if config_key and not self._is_valid_config_key(config_key):
            raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "配置键格式不正确，只能包含字母、数字、下划线和点号")
        
        # 检查值类型
        value_type = obj_data.get("value_type")
        if value_type and value_type not in ["string", "integer", "float", "boolean", "json"]:
            raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "无效的值类型")
        
        # 验证JSON格式
        if value_type == "json":
            config_value = obj_data.get("config_value")
            if config_value:
                try:
                    json.loads(config_value)
                except json.JSONDecodeError:
                    raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "JSON格式不正确")
    
    def _is_valid_config_key(self, config_key: str) -> bool:
        """
        验证配置键格式
        
        Args:
            config_key: 配置键
            
        Returns:
            是否有效
        """
        import re
        pattern = r'^[a-zA-Z][a-zA-Z0-9_.]{1,99}$'
        return bool(re.match(pattern, config_key))


class SystemStatsService:
    """
    系统统计服务
    
    提供系统整体统计信息
    """
    
    def __init__(self):
        self.logger = self._get_logger()
    
    def _get_logger(self):
        import logging
        return logging.getLogger(self.__class__.__name__)
    
    def get_system_stats(
        self,
        db: Session,
        days: int = 30
    ) -> SystemStatsResponse:
        """
        获取系统统计信息
        
        Args:
            db: 数据库会话
            days: 统计天数
            
        Returns:
            系统统计信息
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 用户统计
        total_customers = db.query(Customer).count()
        active_customers = db.query(Customer).filter(Customer.is_active == True).count()
        new_customers = db.query(Customer).filter(
            Customer.created_at >= start_date
        ).count()
        
        # API统计
        total_apis = db.query(CustomApi).count()
        active_apis = db.query(CustomApi).filter(CustomApi.status == True).count()
        new_apis = db.query(CustomApi).filter(
            CustomApi.created_at >= start_date
        ).count()
        
        # 调用统计
        total_api_calls = db.query(ApiUsageLog).count()
        successful_calls = db.query(ApiUsageLog).filter(
            and_(ApiUsageLog.response_status >= 200, ApiUsageLog.response_status < 300)
        ).count()
        recent_calls = db.query(ApiUsageLog).filter(
            ApiUsageLog.created_at >= start_date
        ).count()
        
        # 上传统计
        total_uploads = db.query(DataUpload).count()
        successful_uploads = db.query(DataUpload).filter(
            DataUpload.status == "completed"
        ).count()
        recent_uploads = db.query(DataUpload).filter(
            DataUpload.created_at >= start_date
        ).count()
        
        # 管理员统计
        total_admins = db.query(AdminUser).count()
        active_admins = db.query(AdminUser).filter(AdminUser.is_active == True).count()
        
        # 今日API调用统计
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_api_calls = db.query(ApiUsageLog).filter(
            ApiUsageLog.created_at >= today_start
        ).count()
        
        # 系统运行时间（简单实现，可以根据需要改进）
        import psutil
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.utcnow().timestamp() - boot_time
            uptime_days = int(uptime_seconds // 86400)
            uptime_hours = int((uptime_seconds % 86400) // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)
            system_uptime = f"{uptime_days}天 {uptime_hours}小时 {uptime_minutes}分钟"
        except Exception:
            system_uptime = "未知"
        
        # 数据库大小（简单实现）
        try:
            # 获取数据库文件大小（适用于SQLite）
            import os
            from app.core.config import settings
            if hasattr(settings, 'DATABASE_URL') and 'sqlite' in settings.DATABASE_URL:
                db_path = settings.DATABASE_URL.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    size_bytes = os.path.getsize(db_path)
                    if size_bytes < 1024:
                        database_size = f"{size_bytes} B"
                    elif size_bytes < 1024 * 1024:
                        database_size = f"{size_bytes / 1024:.1f} KB"
                    elif size_bytes < 1024 * 1024 * 1024:
                        database_size = f"{size_bytes / (1024 * 1024):.1f} MB"
                    else:
                        database_size = f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
                else:
                    database_size = "未知"
            else:
                # 对于其他数据库类型，可以使用SQL查询
                database_size = "未知"
        except Exception:
            database_size = "未知"
        
        return SystemStatsResponse(
            total_customers=total_customers,
            active_customers=active_customers,
            total_admins=total_admins,
            active_admins=active_admins,
            total_apis=total_apis,
            active_apis=active_apis,
            total_api_calls=total_api_calls,
            today_api_calls=today_api_calls,
            system_uptime=system_uptime,
            database_size=database_size
        )
    
    def get_system_health(
        self,
        db: Session
    ) -> SystemHealthResponse:
        """
        获取系统健康状态
        
        Args:
            db: 数据库会话
            
        Returns:
            系统健康状态
        """
        try:
            # 数据库连接检查
            db.execute("SELECT 1")
            database_status = "healthy"
            database_message = "数据库连接正常"
        except Exception as e:
            database_status = "unhealthy"
            database_message = f"数据库连接异常: {str(e)}"
        
        # 磁盘空间检查
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            disk_usage_percent = (used / total) * 100
            
            if disk_usage_percent > 90:
                disk_status = "critical"
                disk_message = f"磁盘使用率过高: {disk_usage_percent:.1f}%"
            elif disk_usage_percent > 80:
                disk_status = "warning"
                disk_message = f"磁盘使用率较高: {disk_usage_percent:.1f}%"
            else:
                disk_status = "healthy"
                disk_message = f"磁盘使用率正常: {disk_usage_percent:.1f}%"
        except Exception as e:
            disk_status = "unknown"
            disk_message = f"无法获取磁盘信息: {str(e)}"
            disk_usage_percent = 0
        
        # 内存使用检查
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_usage_percent = memory.percent
            
            if memory_usage_percent > 90:
                memory_status = "critical"
                memory_message = f"内存使用率过高: {memory_usage_percent:.1f}%"
            elif memory_usage_percent > 80:
                memory_status = "warning"
                memory_message = f"内存使用率较高: {memory_usage_percent:.1f}%"
            else:
                memory_status = "healthy"
                memory_message = f"内存使用率正常: {memory_usage_percent:.1f}%"
        except ImportError:
            memory_status = "unknown"
            memory_message = "psutil未安装，无法获取内存信息"
            memory_usage_percent = 0
        except Exception as e:
            memory_status = "unknown"
            memory_message = f"无法获取内存信息: {str(e)}"
            memory_usage_percent = 0
        
        # 整体状态评估
        if any(status == "critical" for status in [database_status, disk_status, memory_status]):
            overall_status = "critical"
        elif any(status == "warning" for status in [database_status, disk_status, memory_status]):
            overall_status = "warning"
        elif any(status == "unhealthy" for status in [database_status, disk_status, memory_status]):
            overall_status = "unhealthy"
        else:
            overall_status = "healthy"
        
        return SystemHealthResponse(
            overall_status=overall_status,
            database_status=database_status,
            database_message=database_message,
            disk_status=disk_status,
            disk_message=disk_message,
            disk_usage_percent=disk_usage_percent,
            memory_status=memory_status,
            memory_message=memory_message,
            memory_usage_percent=memory_usage_percent,
            check_time=datetime.utcnow()
        )


# 全局服务实例
admin_user_service = AdminUserService()
system_config_service = SystemConfigService()
system_stats_service = SystemStatsService()


if __name__ == "__main__":
    print("系统管理服务定义完成")