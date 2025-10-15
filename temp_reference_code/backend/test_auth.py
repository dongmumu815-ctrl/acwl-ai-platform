#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.services.auth import AuthService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def test_admin_auth():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        auth_service = AuthService()
        admin = auth_service.authenticate_admin(db, 'admin', 'admin123')
        
        print(f'认证结果: {admin is not None}')
        if admin:
            print(f'管理员: {admin.username}, ID: {admin.id}')
            print(f'邮箱: {admin.email}')
            print(f'状态: {admin.is_active}')
            print(f'锁定状态: {getattr(admin, "is_locked", "未定义")}')
        else:
            print('认证失败')
            
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        engine.dispose()

if __name__ == '__main__':
    test_admin_auth()