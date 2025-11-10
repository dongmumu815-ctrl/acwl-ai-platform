#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台管理服务模块

提供客户和客户会话的业务逻辑处理功能。

Author: System
Date: 2024
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
import secrets
import string

from .base import BaseService
from .auth import auth_service, jwt_service
from app.models.customer import Customer, CustomerSession
from app.models.api import CustomApi
from app.core.exceptions import (
    ValidationException,
    ConflictException,
    NotFoundException
)
from app.core.business_codes import BusinessException, BusinessCode, BusinessResponse
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerLoginRequest,
    CustomerStatsResponse
)
from app.schemas.base import PaginationInfo


class CustomerService(BaseService[Customer, CustomerCreate, CustomerUpdate]):
    """
    客户服务
    
    提供平台管理的业务逻辑处理
    """
    
    def __init__(self):
        super().__init__(Customer)
    
    def create_customer(
        self,
        db: Session,
        customer_data: CustomerCreate,
        created_by: Optional[int] = None
    ) -> Customer:
        """
        创建客户
        
        Args:
            db: 数据库会话
            customer_data: 客户创建数据
            created_by: 创建者ID
            
        Returns:
            创建的客户对象
            
        Raises:
            ConflictException: 用户名或邮箱已存在
            ValidationException: 数据验证失败
        """
        # 检查邮箱是否已存在
        if self.exists(db, filters={"email": customer_data.email}):
            raise ConflictException(f"邮箱 '{customer_data.email}' 已存在")
        
        # 生成app_id和app_secret
        app_id = self._generate_app_id()
        app_secret = auth_service.generate_app_secret(app_id, 0)  # 临时使用0
        
        # 准备创建数据
        create_data = customer_data.dict()
        
        # 转换status字段：字符串转布尔值
        if "status" in create_data:
            create_data["status"] = create_data["status"] == "active"
        
        create_data.update({
            "app_id": app_id,
            "app_secret": app_secret
        })
        
        # 创建客户
        customer = self.create(db, obj_in=create_data)
        
        # 重新生成app_secret（使用真实的customer_id）
        customer.app_secret = auth_service.generate_app_secret(app_id, customer.id)
        db.commit()
        db.refresh(customer)
        
        self.logger.info(f"Created customer: {customer.name} (ID: {customer.id})")
        return customer
    
    def update_customer(
        self,
        db: Session,
        customer_id: int,
        customer_data: CustomerUpdate,
        updated_by: Optional[int] = None
    ) -> Customer:
        """
        更新平台信息
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            customer_data: 更新数据
            updated_by: 更新者ID
            
        Returns:
            更新后的客户对象
            
        Raises:
            NotFoundException: 客户不存在
            ConflictException: 邮箱已被其他用户使用
        """
        customer = self.get_or_404(db, customer_id)
        
        # 检查邮箱是否被其他用户使用
        if customer_data.email and customer_data.email != customer.email:
            existing = db.query(Customer).filter(
                Customer.email == customer_data.email,
                Customer.id != customer_id
            ).first()
            if existing:
                raise ConflictException(f"邮箱 '{customer_data.email}' 已被其他用户使用")
        
        # 更新数据
        update_data = customer_data.dict(exclude_unset=True)
        
        # 转换status字段：字符串转布尔值
        if "status" in update_data:
            update_data["status"] = update_data["status"] == "active"
        
        updated_customer = self.update(db, db_obj=customer, obj_in=update_data)
        
        self.logger.info(f"Updated customer: {customer.name} (ID: {customer.id})")
        return updated_customer
    
    def reset_app_secret(
        self,
        db: Session,
        customer_id: int,
        reset_by: Optional[int] = None
    ) -> Customer:
        """
        重置客户的app_secret
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            reset_by: 重置者ID
            
        Returns:
            更新后的客户对象
        """
        customer = self.get_or_404(db, customer_id)
        
        # 生成新的app_secret
        new_secret = auth_service.generate_app_secret(customer.app_id, customer.id)
        
        # 更新客户
        customer.app_secret = new_secret
        
        db.commit()
        db.refresh(customer)
        
        self.logger.info(f"Reset app_secret for customer: {customer.name} (ID: {customer.id})")
        return customer
    

    
    def activate_customer(self, db: Session, customer_id: int) -> Customer:
        """
        激活客户账户
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            
        Returns:
            更新后的客户对象
        """
        customer = self.get_or_404(db, customer_id)
        
        customer.status = True
        
        db.commit()
        db.refresh(customer)
        
        self.logger.info(f"Activated customer: {customer.name} (ID: {customer.id})")
        return customer
    
    def deactivate_customer(self, db: Session, customer_id: int) -> Customer:
        """
        停用客户账户
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            
        Returns:
            更新后的客户对象
        """
        customer = self.get_or_404(db, customer_id)
        
        customer.status = False
        
        db.commit()
        db.refresh(customer)
        
        self.logger.info(f"Deactivated customer: {customer.name} (ID: {customer.id})")
        return customer
    

    
    def get_customer_stats(
        self,
        db: Session,
        customer_id: int,
        days: int = 30
    ) -> CustomerStatsResponse:
        """
        获取客户统计信息
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            days: 统计天数
            
        Returns:
            客户统计信息
        """
        customer = self.get_or_404(db, customer_id)
        
        # 计算日期范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # API统计
        api_count = db.query(CustomApi).filter(
            CustomApi.customer_id == customer_id
        ).count()
        
        active_api_count = db.query(CustomApi).filter(
            CustomApi.customer_id == customer_id,
            CustomApi.status == True
        ).count()
        
        # 调用统计（这里需要根据实际的日志表来查询）
        # total_api_calls = db.query(ApiUsageLog).filter(
        #     ApiUsageLog.customer_id == customer_id,
        #     ApiUsageLog.created_at >= start_date
        # ).count()
        
        # 暂时使用模拟数据
        total_api_calls = customer.total_api_calls or 0
        successful_calls = int(total_api_calls * 0.95)  # 假设95%成功率
        failed_calls = total_api_calls - successful_calls
        
        return CustomerStatsResponse(
            customer_id=customer_id,
            api_count=api_count,
            active_api_count=active_api_count,
            total_api_calls=total_api_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            success_rate=successful_calls / total_api_calls if total_api_calls > 0 else 0,
            last_api_call=customer.last_api_call_at,
            period_days=days
        )
    
    def search_customers(
        self,
        db: Session,
        *,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Customer], PaginationInfo]:
        """
        搜索客户
        
        Args:
            db: 数据库会话
            keyword: 关键词（客户名称、邮箱、公司）
            status: 客户状态
            created_after: 创建时间之后
            created_before: 创建时间之前
            page: 页码
            page_size: 每页大小
            
        Returns:
            (客户列表, 分页信息)
        """
        query = db.query(Customer)
        
        # 关键词搜索
        if keyword:
            search_filter = or_(
                Customer.name.ilike(f"%{keyword}%"),
                Customer.email.ilike(f"%{keyword}%"),
                Customer.company.ilike(f"%{keyword}%")
            )
            query = query.filter(search_filter)
        
        # 状态过滤
        if status is not None:
            # 将字符串状态转换为布尔值
            status_bool = status == "active" if isinstance(status, str) else status
            query = query.filter(Customer.status == status_bool)
        
        # 日期过滤
        if created_after:
            query = query.filter(Customer.created_at >= created_after)
        
        if created_before:
            query = query.filter(Customer.created_at <= created_before)
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        customers = query.order_by(Customer.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # 创建分页信息
        pagination = PaginationInfo.create(
            page=page,
            size=page_size,
            total=total
        )
        
        return customers, pagination
    
    def customer_to_response_dict(self, customer: Customer) -> dict:
        """
        将Customer对象转换为响应字典，处理status字段类型转换
        
        Args:
            customer: Customer对象
            
        Returns:
            响应字典
        """
        return {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "company": customer.company,
            "link_read_id": customer.link_read_id,
            "app_id": customer.app_id,
            "status": "active" if customer.status else "inactive",
            "rate_limit": customer.rate_limit,
            "max_apis": customer.max_apis,
            "api_count": getattr(customer, 'api_count', 0),
            "total_calls": getattr(customer, 'total_calls', 0),
            "last_called_at": getattr(customer, 'last_called_at', None),
            "created_at": customer.created_at,
            "updated_at": customer.updated_at
        }
    
    def customer_to_detail_response_dict(self, customer: Customer) -> dict:
        """
        将Customer对象转换为详细响应字典，处理status字段类型转换
        
        Args:
            customer: Customer对象
            
        Returns:
            详细响应字典
        """
        base_dict = self.customer_to_response_dict(customer)
        base_dict.update({
            "app_secret": customer.app_secret,
            "active_sessions": getattr(customer, 'active_sessions', 0),
            "today_calls": getattr(customer, 'today_calls', 0),
            "this_month_calls": getattr(customer, 'this_month_calls', 0),
            "apis": getattr(customer, 'apis', None)
        })
        return base_dict
    
    def _generate_app_id(self) -> str:
        """
        生成应用ID
        
        Returns:
            应用ID
        """
        # 生成8位随机字符串
        chars = string.ascii_uppercase + string.digits
        app_id = ''.join(secrets.choice(chars) for _ in range(8))
        return f"APP_{app_id}"
    
    def validate_business_rules(self, db: Session, obj_data: Dict[str, Any]) -> None:
        """
        验证客户业务规则
        
        Args:
            db: 数据库会话
            obj_data: 对象数据
            
        Raises:
            BusinessException: 业务规则验证失败
        """
        # 检查邮箱格式（Pydantic已经验证，这里可以添加额外规则）
        email = obj_data.get("email")
        if email and self._is_blacklisted_email(email):
            raise BusinessException(BusinessCode.DATA_VALIDATION_FAILED, "该邮箱域名不被允许")
    

    def _is_blacklisted_email(self, email: str) -> bool:
        """
        检查邮箱是否在黑名单中
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否在黑名单中
        """
        # 可以从配置或数据库中获取黑名单
        blacklisted_domains = [
            "tempmail.com",
            "10minutemail.com",
            "guerrillamail.com"
        ]
        
        domain = email.split('@')[-1].lower()
        return domain in blacklisted_domains


class CustomerSessionService(BaseService[CustomerSession, dict, dict]):
    """
    客户会话服务
    
    提供客户会话管理的业务逻辑处理
    """
    
    def __init__(self):
        super().__init__(CustomerSession)
    
    def login_customer(
        self,
        db: Session,
        login_data: CustomerLoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        客户登录
        
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
        # 认证客户
        customer = auth_service.authenticate_customer_by_app_credentials(
            db, login_data.app_id, login_data.app_secret
        )
        
        if not customer:
            raise ValidationException("应用ID或密钥错误")
        
        # 创建会话
        session = auth_service.create_customer_session(
            db, customer, ip_address, user_agent
        )
        
        # 生成JWT令牌
        access_token = jwt_service.create_access_token(
            subject=customer.id,
            user_type="customer"
        )
        
        refresh_token = jwt_service.create_refresh_token(
            subject=customer.id,
            user_type="customer"
        )
        
        # 转换客户对象为响应格式
        customer_dict = customer_service.customer_to_response_dict(customer)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,  # 1小时
            "session_token": session.session_token,
            "customer": customer_dict
        }
    
    def logout_customer(
        self,
        db: Session,
        session_token: str
    ) -> bool:
        """
        客户登出
        
        Args:
            db: 数据库会话
            session_token: 会话令牌
            
        Returns:
            是否登出成功
        """
        return auth_service.revoke_customer_session(db, session_token)
    
    def get_active_sessions(
        self,
        db: Session,
        customer_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[CustomerSession], PaginationInfo]:
        """
        获取客户的活跃会话
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            page: 页码
            page_size: 每页大小
            
        Returns:
            (会话列表, 分页信息)
        """
        filters = {
            "customer_id": customer_id,
            "is_active": True,
            "expires_at": {"gt": datetime.utcnow()}
        }
        
        return self.get_paginated(
            db,
            page=page,
            page_size=page_size,
            filters=filters,
            order_by="last_activity_at",
            order_desc=True
        )
    
    def revoke_all_sessions(
        self,
        db: Session,
        customer_id: int,
        except_session: Optional[str] = None
    ) -> int:
        """
        撤销客户的所有会话
        
        Args:
            db: 数据库会话
            customer_id: 客户ID
            except_session: 排除的会话令牌
            
        Returns:
            撤销的会话数量
        """
        query = db.query(CustomerSession).filter(
            CustomerSession.customer_id == customer_id,
            CustomerSession.is_active == True
        )
        
        if except_session:
            query = query.filter(
                CustomerSession.session_token != except_session
            )
        
        sessions = query.all()
        revoked_count = 0
        
        for session in sessions:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            revoked_count += 1
        
        db.commit()
        
        self.logger.info(
            f"Revoked {revoked_count} sessions for customer: {customer_id}"
        )
        return revoked_count
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """
        清理过期会话
        
        Args:
            db: 数据库会话
            
        Returns:
            清理的会话数量
        """
        expired_sessions = db.query(CustomerSession).filter(
            CustomerSession.expires_at <= datetime.utcnow(),
            CustomerSession.is_active == True
        ).all()
        
        cleaned_count = 0
        for session in expired_sessions:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            cleaned_count += 1
        
        db.commit()
        
        self.logger.info(f"Cleaned up {cleaned_count} expired sessions")
        return cleaned_count


# 全局服务实例
customer_service = CustomerService()
customer_session_service = CustomerSessionService()


if __name__ == "__main__":
    print("客户服务定义完成")