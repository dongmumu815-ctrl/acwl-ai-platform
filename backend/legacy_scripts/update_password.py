#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from sqlalchemy import select, update
from app.core.database import get_db_context
from app.models.user import User
from app.core.security import get_password_hash

async def update_user_passwords():
    """更新测试用户密码"""
    
    # 新密码设置
    new_password = "password123"  # 设置一个简单易记的测试密码
    new_password_hash = get_password_hash(new_password)
    
    print(f"新密码: {new_password}")
    print(f"新密码哈希: {new_password_hash}")
    print("="*50)
    
    async with get_db_context() as db:
        # 获取所有测试用户
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print(f"找到 {len(users)} 个用户")
        
        # 更新所有用户的密码
        for user in users:
            print(f"更新用户: {user.username} ({user.email})")
            
            # 更新密码哈希
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(password_hash=new_password_hash)
            )
        
        # 提交更改
        await db.commit()
        print("\n密码更新完成！")
        print(f"所有用户的新密码都是: {new_password}")
        
        # 验证更新结果
        print("\n验证更新结果:")
        result = await db.execute(select(User).where(User.email == 'admin@acwl.ai'))
        admin_user = result.scalar_one_or_none()
        
        if admin_user:
            from app.core.security import verify_password
            is_valid = verify_password(new_password, admin_user.password_hash)
            print(f"admin@acwl.ai 密码验证: {'✅ 成功' if is_valid else '❌ 失败'}")
        
if __name__ == "__main__":
    asyncio.run(update_user_passwords())