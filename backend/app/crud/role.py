"""
角色相关的CRUD操作
提供数据库操作的封装
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.models.role import Role, UserRole, RolePermission
from app.models.user import User
from app.models.permission import Permission
from app.schemas.role import RoleCreate, RoleUpdate, UserRoleCreate, RolePermissionCreate


class CRUDRole:
    """角色CRUD操作类"""
    
    def get(self, db: Session, role_id: int) -> Optional[Role]:
        """根据ID获取角色"""
        return db.query(Role).filter(Role.id == role_id).first()
    
    def get_by_code(self, db: Session, code: str) -> Optional[Role]:
        """根据代码获取角色"""
        return db.query(Role).filter(Role.code == code).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        return db.query(Role).filter(Role.name == name).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        name: Optional[str] = None,
        status: Optional[bool] = None,
        is_system: Optional[bool] = None
    ) -> tuple[List[Role], int]:
        """获取角色列表"""
        query = db.query(Role)
        
        # 添加过滤条件
        if name:
            query = query.filter(Role.name.contains(name))
        if status is not None:
            query = query.filter(Role.status == status)
        if is_system is not None:
            query = query.filter(Role.is_system == is_system)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        roles = query.order_by(Role.created_at.desc()).offset(skip).limit(limit).all()
        
        return roles, total
    
    def create(self, db: Session, obj_in: RoleCreate, created_by: Optional[int] = None) -> Role:
        """创建角色"""
        db_obj = Role(
            name=obj_in.name,
            code=obj_in.code,
            description=obj_in.description,
            status=obj_in.status,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        db_obj: Role, 
        obj_in: RoleUpdate, 
        updated_by: Optional[int] = None
    ) -> Role:
        """更新角色"""
        update_data = obj_in.model_dump(exclude_unset=True)
        if updated_by:
            update_data["updated_by"] = updated_by
            
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, role_id: int) -> bool:
        """删除角色"""
        db_obj = self.get(db, role_id)
        if db_obj and not db_obj.is_system:  # 系统角色不能删除
            db.delete(db_obj)
            db.commit()
            return True
        return False
    
    def get_with_permissions(self, db: Session, role_id: int) -> Optional[Role]:
        """获取角色及其权限信息"""
        return db.query(Role).options(
            joinedload(Role.role_permissions).joinedload(RolePermission.permission)
        ).filter(Role.id == role_id).first()
    
    def get_users_by_role(self, db: Session, role_id: int) -> List[User]:
        """获取拥有指定角色的用户列表"""
        return db.query(User).join(UserRole).filter(UserRole.role_id == role_id).all()


class CRUDUserRole:
    """用户角色关联CRUD操作类"""
    
    def get(self, db: Session, user_role_id: int) -> Optional[UserRole]:
        """根据ID获取用户角色关联"""
        return db.query(UserRole).filter(UserRole.id == user_role_id).first()
    
    def get_by_user_role(self, db: Session, user_id: int, role_id: int) -> Optional[UserRole]:
        """根据用户ID和角色ID获取关联"""
        return db.query(UserRole).filter(
            and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
        ).first()
    
    def get_roles_by_user(self, db: Session, user_id: int) -> List[Role]:
        """获取用户的所有角色"""
        return db.query(Role).join(UserRole).filter(
            and_(UserRole.user_id == user_id, Role.status == True)
        ).all()
    
    def get_users_by_role(self, db: Session, role_id: int) -> List[User]:
        """获取拥有指定角色的用户"""
        return db.query(User).join(UserRole).filter(UserRole.role_id == role_id).all()
    
    def create(self, db: Session, obj_in: UserRoleCreate, created_by: Optional[int] = None) -> UserRole:
        """创建用户角色关联"""
        # 检查是否已存在
        existing = self.get_by_user_role(db, obj_in.user_id, obj_in.role_id)
        if existing:
            return existing
        
        db_obj = UserRole(
            user_id=obj_in.user_id,
            role_id=obj_in.role_id,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, user_id: int, role_id: int) -> bool:
        """删除用户角色关联"""
        db_obj = self.get_by_user_role(db, user_id, role_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False
    
    def delete_user_roles(self, db: Session, user_id: int) -> bool:
        """删除用户的所有角色"""
        db.query(UserRole).filter(UserRole.user_id == user_id).delete()
        db.commit()
        return True
    
    def assign_roles_to_user(
        self, 
        db: Session, 
        user_id: int, 
        role_ids: List[int], 
        created_by: Optional[int] = None
    ) -> List[UserRole]:
        """为用户分配多个角色"""
        # 先删除用户现有的角色
        self.delete_user_roles(db, user_id)
        
        # 分配新角色
        user_roles = []
        for role_id in role_ids:
            user_role = self.create(db, UserRoleCreate(user_id=user_id, role_id=role_id), created_by)
            user_roles.append(user_role)
        
        return user_roles


class CRUDRolePermission:
    """角色权限关联CRUD操作类"""
    
    def get(self, db: Session, role_permission_id: int) -> Optional[RolePermission]:
        """根据ID获取角色权限关联"""
        return db.query(RolePermission).filter(RolePermission.id == role_permission_id).first()
    
    def get_by_role_permission(self, db: Session, role_id: int, permission_id: int) -> Optional[RolePermission]:
        """根据角色ID和权限ID获取关联"""
        return db.query(RolePermission).filter(
            and_(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id)
        ).first()
    
    def get_permissions_by_role(self, db: Session, role_id: int) -> List[Permission]:
        """获取角色的所有权限"""
        return db.query(Permission).join(RolePermission).filter(
            and_(RolePermission.role_id == role_id, Permission.status == True)
        ).order_by(Permission.module, Permission.sort_order).all()
    
    def get_roles_by_permission(self, db: Session, permission_id: int) -> List[Role]:
        """获取拥有指定权限的角色"""
        return db.query(Role).join(RolePermission).filter(
            and_(RolePermission.permission_id == permission_id, Role.status == True)
        ).all()
    
    def create(self, db: Session, obj_in: RolePermissionCreate, created_by: Optional[int] = None) -> RolePermission:
        """创建角色权限关联"""
        # 检查是否已存在
        existing = self.get_by_role_permission(db, obj_in.role_id, obj_in.permission_id)
        if existing:
            return existing
        
        db_obj = RolePermission(
            role_id=obj_in.role_id,
            permission_id=obj_in.permission_id,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, role_id: int, permission_id: int) -> bool:
        """删除角色权限关联"""
        db_obj = self.get_by_role_permission(db, role_id, permission_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False
    
    def delete_role_permissions(self, db: Session, role_id: int) -> bool:
        """删除角色的所有权限"""
        db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
        db.commit()
        return True
    
    def assign_permissions_to_role(
        self, 
        db: Session, 
        role_id: int, 
        permission_ids: List[int], 
        created_by: Optional[int] = None
    ) -> List[RolePermission]:
        """为角色分配多个权限"""
        # 先删除角色现有的权限
        self.delete_role_permissions(db, role_id)
        
        # 分配新权限
        role_permissions = []
        for permission_id in permission_ids:
            role_permission = self.create(
                db, 
                RolePermissionCreate(role_id=role_id, permission_id=permission_id), 
                created_by
            )
            role_permissions.append(role_permission)
        
        return role_permissions


# 创建CRUD实例
crud_role = CRUDRole()
crud_user_role = CRUDUserRole()
crud_role_permission = CRUDRolePermission()