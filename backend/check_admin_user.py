#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查管理员用户信息
"""

import asyncio
from app.core.database import get_db_context
from app.models.user import User
from sqlalchemy import select
from app.core.security import verify_password

async def check_admin_user():
    """检查管理员用户信息"""
    try:
        async with get_db_context() as db:
            # 查找所有用户
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            print(f"数据库中共有 {len(users)} 个用户:")
            for user in users:
                print(f"\n用户ID: {user.id}")
                print(f"用户名: {user.username}")
                print(f"邮箱: {user.email}")
                print(f"是否管理员: {user.is_admin}")
                print(f"是否激活: {user.is_active}")
                print(f"密码哈希: {user.password_hash[:50]}...")
                
                # 测试密码验证
                test_passwords = ["admin123", "password", "passoword", "admin", "123456"]
                for pwd in test_passwords:
                    if verify_password(pwd, user.password_hash):
                        print(f"✅ 密码 '{pwd}' 验证成功")
                    else:
                        print(f"❌ 密码 '{pwd}' 验证失败")
                        
    except Exception as e:
        print(f"检查用户信息时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_admin_user())