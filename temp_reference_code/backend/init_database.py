#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本

用于创建数据库表结构，不依赖Alembic迁移工具。
直接使用SQLAlchemy的create_all方法创建所有表。

Author: System
Date: 2024
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
from app.models import *  # 导入所有模型

def create_database_if_not_exists():
    """
    如果数据库不存在则创建数据库
    """
    try:
        # 解析数据库URL，获取数据库名
        db_url_parts = settings.DATABASE_URL.split('/')
        db_name = db_url_parts[-1].split('?')[0]  # 移除查询参数
        base_url = '/'.join(db_url_parts[:-1])
        
        # 连接到MySQL服务器（不指定数据库）
        engine = create_engine(base_url)
        
        with engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(text(f"SHOW DATABASES LIKE '{db_name}'"))
            if not result.fetchone():
                # 创建数据库
                conn.execute(text(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                print(f"✅ 数据库 '{db_name}' 创建成功")
            else:
                print(f"ℹ️  数据库 '{db_name}' 已存在")
        
        engine.dispose()
        
    except Exception as e:
        print(f"❌ 创建数据库时出错: {str(e)}")
        return False
    
    return True

def create_tables():
    """
    创建所有数据库表
    """
    try:
        # 创建数据库引擎
        engine = create_engine(settings.DATABASE_URL)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        print("✅ 数据库表创建成功")
        
        # 显示创建的表
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 已创建的表: {', '.join(tables)}")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ 创建表时出错: {str(e)}")
        return False

def insert_default_data():
    """
    插入默认数据
    """
    try:
        from sqlalchemy.orm import sessionmaker
        from app.models.admin import AdminUser
        from app.services.auth import AuthService
        
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 检查是否已有管理员用户
            existing_admin = db.query(AdminUser).filter(
                AdminUser.username == 'admin'
            ).first()
            
            if not existing_admin:
                # 创建默认管理员
                auth_service = AuthService()
                hashed_password = auth_service.get_password_hash('admin123')
                
                admin_user = AdminUser(
                    username='admin',
                    password_hash=hashed_password,
                    email='admin@example.com',
                    real_name='系统管理员',
                    is_active=True,
                    is_superuser=True
                )
                
                db.add(admin_user)
                db.commit()
                
                print("✅ 默认管理员账户创建成功")
                print("   用户名: admin")
                print("   密码: admin123")
                print("   邮箱: admin@example.com")
            else:
                print("ℹ️  默认管理员账户已存在")
                
        finally:
            db.close()
            engine.dispose()
        
        return True
        
    except Exception as e:
        print(f"❌ 插入默认数据时出错: {str(e)}")
        return False

def main():
    """
    主函数：执行数据库初始化流程
    """
    print("🚀 开始数据库初始化...")
    print(f"📍 数据库URL: {settings.DATABASE_URL}")
    print()
    
    # 1. 创建数据库（如果不存在）
    print("1️⃣ 检查并创建数据库...")
    if not create_database_if_not_exists():
        print("❌ 数据库创建失败，退出")
        return False
    print()
    
    # 2. 创建表结构
    print("2️⃣ 创建数据库表...")
    if not create_tables():
        print("❌ 表创建失败，退出")
        return False
    print()
    
    # 3. 插入默认数据
    print("3️⃣ 插入默认数据...")
    if not insert_default_data():
        print("❌ 默认数据插入失败，但表结构已创建")
        return False
    print()
    
    print("🎉 数据库初始化完成！")
    print()
    print("📊 数据库包含以下功能:")
    print("   - 平台管理和认证")
    print("   - 自定义接口定义")
    print("   - 数据上传和验证")
    print("   - 批次管理和状态跟踪")
    print("   - 系统管理和配置")
    print()
    print("📝 后续步骤:")
    print("   1. 启动应用: python main.py")
    print("   2. 访问API文档: http://localhost:8000/docs")
    print("   3. 使用默认管理员账户登录: admin/admin123")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 未预期的错误: {str(e)}")
        sys.exit(1)