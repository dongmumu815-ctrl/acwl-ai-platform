#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务模块

提供JWT令牌管理、用户认证、权限验证等功能。

Author: System
Date: 2024
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import hashlib
import logging

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ValidationException
)
from app.models.customer import Customer, CustomerSession
from app.models.admin import AdminUser

# OAuth2 scheme for token authentication
oauth2_scheme = HTTPBearer()


class JWTService:
    """
    JWT令牌服务
    
    提供JWT令牌的生成、验证、刷新等功能
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_access_token(
        self,
        subject: Union[str, int],
        user_type: str = "customer",
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建访问令牌
        
        Args:
            subject: 用户标识（用户ID或用户名）
            user_type: 用户类型（customer/admin）
            expires_delta: 过期时间间隔
            additional_claims: 额外的声明
            
        Returns:
            JWT访问令牌
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {
            "sub": str(subject),
            "type": user_type,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32)  # JWT ID
        }
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.SECRET_KEY,
            algorithm=self.settings.ALGORITHM
        )
        
        self.logger.info(f"Created access token for {user_type}: {subject}")
        return encoded_jwt
    
    def create_refresh_token(
        self,
        subject: Union[str, int],
        user_type: str = "customer",
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建刷新令牌
        
        Args:
            subject: 用户标识
            user_type: 用户类型
            expires_delta: 过期时间间隔
            
        Returns:
            JWT刷新令牌
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode = {
            "sub": str(subject),
            "type": user_type,
            "token_type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32)
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.SECRET_KEY,
            algorithm=self.settings.ALGORITHM
        )
        
        self.logger.info(f"Created refresh token for {user_type}: {subject}")
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            令牌载荷
            
        Raises:
            AuthenticationException: 令牌无效或过期
        """
        try:
            print("tokenxx:",token)
            payload = jwt.decode(
                token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.ALGORITHM]
            )
            print("payload:",payload)
            
            # 检查必要字段
            if "sub" not in payload or "type" not in payload:
                print("payload: sub",payload)
                raise AuthenticationException("令牌格式无效")
            
            return payload
            
        except JWTError as e:
            print("JWTError:",e)
            self.logger.warning(f"JWT verification failed: {str(e)}")
            raise AuthenticationException("令牌无效或已过期")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        使用刷新令牌生成新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的访问令牌
            
        Raises:
            AuthenticationException: 刷新令牌无效
        """
        try:
            payload = self.verify_token(refresh_token)
            
            # 检查是否为刷新令牌
            if payload.get("token_type") != "refresh":
                raise AuthenticationException("无效的刷新令牌")
            
            # 生成新的访问令牌
            return self.create_access_token(
                subject=payload["sub"],
                user_type=payload["type"]
            )
            
        except JWTError:
            raise AuthenticationException("刷新令牌无效或已过期")
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码JWT令牌（不验证签名）
        
        Args:
            token: JWT令牌
            
        Returns:
            令牌载荷或None
        """
        try:
            return jwt.get_unverified_claims(token)
        except JWTError:
            return None


class AuthService:
    """
    认证服务
    
    提供用户认证、密码验证、会话管理等功能
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.jwt_service = JWTService()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            密码是否正确
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        生成密码哈希
        
        Args:
            password: 明文密码
            
        Returns:
            哈希密码
        """
        return self.pwd_context.hash(password)
    
    def authenticate_customer_by_app_credentials(
        self,
        db: Session,
        app_id: str,
        app_secret: str
    ) -> Optional[Customer]:
        """
        通过应用凭据认证客户
        
        Args:
            db: 数据库会话
            app_id: 应用ID
            app_secret: 应用密钥
            
        Returns:
            认证成功的客户对象或None
        """
        # 查找客户
        customer = db.query(Customer).filter(
            Customer.app_id == app_id,
            Customer.app_secret == app_secret
        ).first()
        
        if not customer:
            self.logger.warning(f"Customer not found or invalid credentials: {app_id}")
            return None
        
        # 检查账户状态
        if not customer.status:
            self.logger.warning(f"Customer account inactive: {app_id}")
            return None
        
        # 更新最后登录时间
        customer.last_login_at = datetime.utcnow()
        
        db.commit()
        
        self.logger.info(f"Customer authenticated successfully: {app_id}")
        return customer
    
    def authenticate_admin(
        self,
        db: Session,
        username: str,
        password: str
    ) -> Optional[AdminUser]:
        """
        管理员认证
        
        Args:
            db: 数据库会话
            username: 用户名或邮箱
            password: 密码
            
        Returns:
            认证成功的管理员对象或None
        """
        # 查找管理员
        admin = db.query(AdminUser).filter(
            (AdminUser.username == username) | (AdminUser.email == username)
        ).first()
        
        if not admin:
            self.logger.warning(f"Admin not found: {username}")
            return None
        
        # 检查账户状态
        if not admin.is_active:
            self.logger.warning(f"Admin account inactive: {username}")
            return None
        
        if admin.is_locked():
            self.logger.warning(f"Admin account locked: {username}")
            return None
        
        # 验证密码
        if not self.verify_password(password, admin.password_hash):
            # 增加失败登录次数
            admin.failed_login_count += 1
            
            # 检查是否需要锁定账户
            if admin.failed_login_count >= self.settings.MAX_LOGIN_ATTEMPTS:
                admin.is_locked = True
                admin.locked_at = datetime.utcnow()
                admin.locked_until = datetime.utcnow() + timedelta(
                    minutes=self.settings.ACCOUNT_LOCK_DURATION_MINUTES
                )
                self.logger.warning(f"Admin account locked due to failed attempts: {username}")
            
            db.commit()
            self.logger.warning(f"Invalid password for admin: {username}")
            return None
        
        # 重置失败登录次数
        admin.failed_login_count = 0
        admin.last_login_at = datetime.utcnow()
        admin.login_count += 1
        
        db.commit()
        
        self.logger.info(f"Admin authenticated successfully: {username}")
        return admin
    
    def create_customer_session(
        self,
        db: Session,
        customer: Customer,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> CustomerSession:
        """
        创建客户会话
        
        Args:
            db: 数据库会话
            customer: 客户对象
            ip_address: IP地址
            user_agent: 用户代理
            
        Returns:
            客户会话对象
        """
        # 生成会话令牌
        session_token = secrets.token_urlsafe(32)
        
        # 创建会话
        session = CustomerSession(
            customer_id=customer.id,
            login_ip=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(
                seconds=self.settings.SESSION_TIMEOUT
            )
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        self.logger.info(f"Created session for customer: {customer.id}")
        return session
    
    def get_customer_session(
        self,
        db: Session,
        session_token: str
    ) -> Optional[CustomerSession]:
        """
        获取客户会话
        
        Args:
            db: 数据库会话
            session_token: 会话令牌
            
        Returns:
            客户会话对象或None
        """
        session = db.query(CustomerSession).filter(
            CustomerSession.session_token == session_token,
            CustomerSession.is_active == True,
            CustomerSession.expires_at > datetime.utcnow()
        ).first()
        
        if session:
            # 更新最后活动时间
            session.last_activity_at = datetime.utcnow()
            db.commit()
        
        return session
    
    def revoke_customer_session(
        self,
        db: Session,
        session_token: str
    ) -> bool:
        """
        撤销客户会话
        
        Args:
            db: 数据库会话
            session_token: 会话令牌
            
        Returns:
            是否撤销成功
        """
        session = db.query(CustomerSession).filter(
            CustomerSession.session_token == session_token
        ).first()
        
        if session:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            db.commit()
            
            self.logger.info(f"Revoked session: {session_token}")
            return True
        
        return False
    
    def generate_app_secret(self, app_id: str, customer_id: int) -> str:
        """
        生成应用密钥
        
        Args:
            app_id: 应用ID
            customer_id: 客户ID
            
        Returns:
            应用密钥
        """
        # 使用HMAC生成密钥
        message = f"{app_id}:{customer_id}:{datetime.utcnow().isoformat()}"
        secret = hashlib.sha256(
            f"{self.settings.SECRET_KEY}:{message}".encode()
        ).hexdigest()
        
        return secret
    
    def verify_app_credentials(
        self,
        db: Session,
        app_id: str,
        app_secret: str
    ) -> Optional[Customer]:
        """
        验证应用凭据
        
        Args:
            db: 数据库会话
            app_id: 应用ID
            app_secret: 应用密钥
            
        Returns:
            验证成功的客户对象或None
        """
        customer = db.query(Customer).filter(
            Customer.app_id == app_id,
            Customer.app_secret == app_secret,
            Customer.is_active == True
        ).first()
        
        if customer:
            self.logger.info(f"App credentials verified for customer: {customer.id}")
        else:
            self.logger.warning(f"Invalid app credentials: {app_id}")
        
        return customer
    
    def check_permission(
        self,
        user: Union[Customer, AdminUser],
        permission: str,
        resource_id: Optional[int] = None
    ) -> bool:
        """
        检查用户权限
        
        Args:
            user: 用户对象
            permission: 权限名称
            resource_id: 资源ID（可选）
            
        Returns:
            是否有权限
        """
        # 管理员权限检查
        if isinstance(user, AdminUser):
            # 超级管理员拥有所有权限
            if user.role == "super_admin":
                return True
            
            # 检查角色权限
            role_permissions = {
                "admin": [
                    "customer.read", "customer.write", "customer.delete",
                    "api.read", "api.write", "api.delete",
                    "log.read", "config.read", "config.write"
                ],
                "operator": [
                    "customer.read", "customer.write",
                    "api.read", "api.write",
                    "log.read", "config.read"
                ],
                "viewer": [
                    "customer.read", "api.read", "log.read", "config.read"
                ]
            }
            
            return permission in role_permissions.get(user.role, [])
        
        # 客户权限检查
        elif isinstance(user, Customer):
            # 客户只能访问自己的资源
            if resource_id and hasattr(user, 'id'):
                return user.id == resource_id
            
            # 基本权限
            customer_permissions = [
                "api.read", "api.write", "data.upload", "log.read"
            ]
            
            return permission in customer_permissions
        
        return False
    
    def require_permission(
        self,
        user: Union[Customer, AdminUser],
        permission: str,
        resource_id: Optional[int] = None
    ) -> None:
        """
        要求用户具有指定权限
        
        Args:
            user: 用户对象
            permission: 权限名称
            resource_id: 资源ID（可选）
            
        Raises:
            AuthorizationException: 权限不足
        """
        if not self.check_permission(user, permission, resource_id):
            self.logger.warning(
                f"Permission denied for user {user.id}: {permission}"
            )
            raise AuthorizationException(f"权限不足: {permission}")
    
    def generate_api_key(self, customer_id: int, api_name: str) -> str:
        """
        生成API密钥
        
        Args:
            customer_id: 客户ID
            api_name: API名称
            
        Returns:
            API密钥
        """
        message = f"{customer_id}:{api_name}:{datetime.utcnow().isoformat()}"
        api_key = hashlib.sha256(
            f"{self.settings.SECRET_KEY}:{message}".encode()
        ).hexdigest()[:32]
        
        return f"ak_{api_key}"
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        验证API密钥格式
        
        Args:
            api_key: API密钥
            
        Returns:
            是否有效
        """
        return (
            isinstance(api_key, str) and
            api_key.startswith("ak_") and
            len(api_key) == 35 and
            api_key[3:].isalnum()
        )


def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> AdminUser:
    """
    获取当前管理员用户
    
    Args:
        token: JWT令牌
        db: 数据库会话
        
    Returns:
        当前管理员对象
        
    Raises:
        HTTPException: 认证失败
    """
    try:
        # 验证令牌
        token = credentials.credentials
        payload = jwt_service.verify_token(token)
        
        # 检查用户类型
        if payload.get("type") != "admin":
            raise AuthenticationException("无效的用户类型")
        
        # 获取管理员ID
        admin_id = int(payload.get("sub"))
        
        # 查询管理员
        admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
        
        if not admin:
            raise AuthenticationException("管理员不存在")
        
        if not admin.is_active:
            raise AuthenticationException("管理员账户已停用")
        
        if admin.is_locked():
            raise AuthenticationException("管理员账户已锁定")
        
        return admin
        
    except AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


# 全局服务实例
jwt_service = JWTService()
auth_service = AuthService()


if __name__ == "__main__":
    # 测试认证服务
    print("认证服务定义完成")
    
    # 测试JWT服务
    try:
        token = jwt_service.create_access_token("test_user", "customer")
        payload = jwt_service.verify_token(token)
        print(f"JWT测试成功: {payload['sub']}")
    except Exception as e:
        print(f"JWT测试失败: {e}")
    
    # 测试密码哈希
    try:
        password = "test_password"
        hashed = auth_service.get_password_hash(password)
        verified = auth_service.verify_password(password, hashed)
        print(f"密码哈希测试成功: {verified}")
    except Exception as e:
        print(f"密码哈希测试失败: {e}")
    
    print("\n认证服务测试完成")