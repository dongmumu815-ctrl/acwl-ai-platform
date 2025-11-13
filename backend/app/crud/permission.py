"""
权限相关的CRUD操作
提供数据库操作的封装
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload, load_only
from sqlalchemy import and_, or_, func

from app.models.permission import Permission
from app.models.role import Role, RolePermission
from app.schemas.permission import PermissionCreate, PermissionUpdate


class CRUDPermission:
    """权限CRUD操作类"""
    
    def get(self, db: Session, permission_id: int) -> Optional[Permission]:
        """根据ID获取权限"""
        return db.query(Permission).filter(Permission.id == permission_id).first()
    
    def get_by_code(self, db: Session, code: str) -> Optional[Permission]:
        """根据代码获取权限"""
        return db.query(Permission).filter(Permission.code == code).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[Permission]:
        """根据名称获取权限"""
        return db.query(Permission).filter(Permission.name == name).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        name: Optional[str] = None,
        module: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        status: Optional[bool] = None,
        is_system: Optional[bool] = None
    ) -> tuple[List[Permission], int]:
        """获取权限列表"""
        query = db.query(Permission)
        
        # 添加过滤条件
        if name:
            query = query.filter(Permission.name.contains(name))
        if module:
            query = query.filter(Permission.module == module)
        if resource:
            query = query.filter(Permission.resource == resource)
        if action:
            query = query.filter(Permission.action == action)
        if status is not None:
            query = query.filter(Permission.status == status)
        if is_system is not None:
            query = query.filter(Permission.is_system == is_system)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        permissions = query.order_by(
            Permission.module, 
            Permission.sort_order, 
            Permission.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return permissions, total
    
    def create(self, db: Session, obj_in: PermissionCreate, created_by: Optional[int] = None) -> Permission:
        """创建权限"""
        db_obj = Permission(
            name=obj_in.name,
            code=obj_in.code,
            description=obj_in.description,
            module=obj_in.module,
            resource=obj_in.resource,
            action=obj_in.action,
            status=obj_in.status,
            sort_order=obj_in.sort_order,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        db_obj: Permission, 
        obj_in: PermissionUpdate, 
        updated_by: Optional[int] = None
    ) -> Permission:
        """更新权限"""
        update_data = obj_in.model_dump(exclude_unset=True)
        if updated_by:
            update_data["updated_by"] = updated_by
            
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, permission_id: int) -> bool:
        """删除权限"""
        db_obj = self.get(db, permission_id)
        if db_obj and not db_obj.is_system:  # 系统权限不能删除
            db.delete(db_obj)
            db.commit()
            return True
        return False
    
    def get_with_roles(self, db: Session, permission_id: int) -> Optional[Permission]:
        """获取权限及其角色信息"""
        return db.query(Permission).options(
            joinedload(Permission.role_permissions).joinedload(RolePermission.role)
        ).filter(Permission.id == permission_id).first()
    
    def get_modules(self, db: Session) -> List[str]:
        """获取所有权限模块"""
        result = db.query(Permission.module).distinct().filter(
            Permission.status == True
        ).all()
        return [row[0] for row in result if row[0]]
    
    def get_by_module(self, db: Session, module: str) -> List[Permission]:
        """根据模块获取权限列表"""
        return db.query(Permission).filter(
            and_(Permission.module == module, Permission.status == True)
        ).order_by(Permission.sort_order, Permission.created_at).all()
    
    def get_tree_structure(self, db: Session) -> Dict[str, List[Permission]]:
        """获取权限的树形结构（按模块分组）
        仅加载树节点所需字段与列属性（role_count），减少不必要的列与关系加载。
        """
        permissions = db.query(Permission).options(
            load_only(
                Permission.id,
                Permission.name,
                Permission.code,
                Permission.module,
                Permission.resource,
                Permission.action,
                Permission.is_system,
                Permission.status,
                Permission.sort_order,
                Permission.role_count,
            )
        ).filter(Permission.status == True).order_by(
            Permission.module, Permission.sort_order, Permission.created_at
        ).all()
        
        tree = {}
        for permission in permissions:
            module = permission.module or "其他"
            if module not in tree:
                tree[module] = []
            tree[module].append(permission)
        
        return tree
    
    def get_user_permissions(self, db: Session, user_id: int) -> List[Permission]:
        """获取用户的所有权限（通过角色）"""
        from app.models.user import User
        from app.models.role import UserRole
        
        return db.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                Role.status == True,
                Permission.status == True
            )
        ).distinct().order_by(Permission.module, Permission.sort_order).all()
    
    def check_user_permission(self, db: Session, user_id: int, permission_code: str) -> bool:
        """检查用户是否拥有指定权限"""
        from app.models.user import User
        from app.models.role import UserRole
        
        count = db.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                Permission.code == permission_code,
                Role.status == True,
                Permission.status == True
            )
        ).count()
        
        return count > 0
    
    def get_permission_codes_by_user(self, db: Session, user_id: int) -> List[str]:
        """获取用户的所有权限代码"""
        permissions = self.get_user_permissions(db, user_id)
        return [p.code for p in permissions]
    
    def batch_create(self, db: Session, permissions_data: List[PermissionCreate], created_by: Optional[int] = None) -> List[Permission]:
        """批量创建权限"""
        permissions = []
        for perm_data in permissions_data:
            # 检查是否已存在
            existing = self.get_by_code(db, perm_data.code)
            if not existing:
                permission = self.create(db, perm_data, created_by)
                permissions.append(permission)
            else:
                permissions.append(existing)
        
        return permissions
    
    def get_permissions_by_resource(self, db: Session, resource: str) -> List[Permission]:
        """根据资源获取权限列表"""
        return db.query(Permission).filter(
            and_(Permission.resource == resource, Permission.status == True)
        ).order_by(Permission.sort_order, Permission.created_at).all()
    
    def get_permissions_by_action(self, db: Session, action: str) -> List[Permission]:
        """根据操作获取权限列表"""
        return db.query(Permission).filter(
            and_(Permission.action == action, Permission.status == True)
        ).order_by(Permission.module, Permission.sort_order).all()


# 创建CRUD实例
crud_permission = CRUDPermission()