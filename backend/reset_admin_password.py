#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置管理员密码的脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db_context
from app.models.user import User
from app.core.security import get_password_hash, verify_password

async def reset_admin_password():
    """
    重置管理员密码
    """
    async with get_db_context() as db:
        try:
            # 查找管理员用户
            result = await db.execute(select(User).where(User.username == "admin"))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("❌ 未找到管理员用户")
                return
            
            print(f"找到管理员用户: {admin_user.username} ({admin_user.email})")
            print(f"当前角色: {admin_user.role}")
            print(f"是否为管理员: {admin_user.is_admin}")
            print(f"是否激活: {admin_user.is_active}")
            
            # 测试当前密码
            current_password = "admin123"
            if verify_password(current_password, admin_user.password_hash):
                print(f"✅ 当前密码 '{current_password}' 验证成功")
                return admin_user
            else:
                print(f"❌ 当前密码 '{current_password}' 验证失败")
            
            # 重置密码
            new_password = "admin123"
            admin_user.password_hash = get_password_hash(new_password)
            
            # 确保用户是管理员且激活
            admin_user.is_admin = True
            admin_user.is_active = True
            admin_user.role = "admin"
            
            await db.commit()
            
            print(f"✅ 管理员密码重置成功!")
            print(f"新密码: {new_password}")
            
            # 验证新密码
            if verify_password(new_password, admin_user.password_hash):
                print(f"✅ 新密码验证成功")
            else:
                print(f"❌ 新密码验证失败")
            
            return admin_user
            
        except Exception as e:
            print(f"❌ 重置密码失败: {e}")
            raise

async def test_login():
    """
    测试登录
    """
    import requests
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            "http://localhost:8082/api/v1/auth/login/json",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n登录测试结果: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user = data.get("user")
            print(f"✅ 登录成功!")
            print(f"Token: {token[:50]}...")
            print(f"用户: {user.get('username')} ({user.get('email')})")
            print(f"角色: {user.get('role')}")
            return token
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录测试异常: {e}")
        return None

async def main():
    """
    主函数
    """
    print("=== 重置管理员密码 ===")
    
    # 重置密码
    admin_user = await reset_admin_password()
    
    if admin_user:
        print("\n=== 测试登录 ===")
        token = await test_login()
        
        if token:
            print("\n=== 登录信息 ===")
            print("用户名: admin")
            print("密码: admin123")
            print("或者")
            print("邮箱: admin@acwl.ai")
            print("密码: admin123")
    
    print("\n=== 完成 ===")

if __name__ == "__main__":
    asyncio.run(main())