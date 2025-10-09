"""
用户相关的CRUD操作
提供数据库操作的封装
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.models.user import User
from app.models.role import UserRole, Role
from app.core.security import get_password_hash, verify_password


class CRUDUser:
    """用户CRUD操作类"""
    
    def get(self, db: Session, id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == id).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        username: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """获取用户列表"""
        query = db.query(User)
        
        # 添加过滤条件
        if username:
            query = query.filter(User.username.contains(username))
        if email:
            query = query.filter(User.email.contains(email))
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        return users, total
    
    def create(self, db: Session, username: str, email: str, password: str, **kwargs) -> User:
        """创建用户"""
        password_hash = get_password_hash(password)
        db_obj = User(
            username=username,
            email=email,
            password_hash=password_hash,
            **kwargs
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, db_obj: User, **kwargs) -> User:
        """更新用户"""
        for field, value in kwargs.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_password(self, db: Session, db_obj: User, new_password: str) -> User:
        """更新用户密码"""
        db_obj.password_hash = get_password_hash(new_password)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: int) -> bool:
        """删除用户"""
        db_obj = self.get(db, id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False
    
    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = self.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    def is_active(self, user: User) -> bool:
        """检查用户是否活跃"""
        return user.is_active
    
    def is_admin(self, user: User) -> bool:
        """检查用户是否是管理员"""
        return user.is_admin
    
    def get_with_roles(self, db: Session, user_id: int) -> Optional[User]:
        """获取用户及其角色信息"""
        return db.query(User).options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        ).filter(User.id == user_id).first()
    
    def get_users_by_role(self, db: Session, role_code: str) -> List[User]:
        """根据角色代码获取用户列表"""
        return db.query(User).join(UserRole).join(Role).filter(
            Role.code == role_code
        ).all()
    
    def assign_role(self, db: Session, user_id: int, role_id: int, created_by: Optional[int] = None) -> bool:
        """为用户分配角色"""
        # 检查是否已存在
        existing = db.query(UserRole).filter(
            and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
        ).first()
        
        if existing:
            return True
        
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            created_by=created_by
        )
        db.add(user_role)
        db.commit()
        return True
    
    def remove_role(self, db: Session, user_id: int, role_id: int) -> bool:
        """移除用户角色"""
        user_role = db.query(UserRole).filter(
            and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
        ).first()
        
        if user_role:
            db.delete(user_role)
            db.commit()
            return True
        return False


# 创建CRUD实例
crud_user = CRUDUser()