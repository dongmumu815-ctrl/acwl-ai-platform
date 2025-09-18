#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
from app.core.security import get_password_hash, verify_password

def fix_password():
    """直接使用pymysql修复密码"""
    
    # 数据库连接配置
    config = {
        'host': '10.20.1.200',
        'port': 3306,
        'user': 'root',
        'password': '2wsx1QAZaczt',
        'database': 'acwl-ai',
        'charset': 'utf8mb4'
    }
    
    # 新密码
    new_password = "password"
    new_password_hash = get_password_hash(new_password)
    
    print(f"新密码: {new_password}")
    print(f"新密码哈希: {new_password_hash}")
    print("="*50)
    
    try:
        # 连接数据库
        connection = pymysql.connect(**config)
        cursor = connection.cursor()
        
        # 更新admin用户密码
        sql = "UPDATE acwl_users SET password_hash = %s WHERE email = 'admin@acwl.ai'"
        cursor.execute(sql, (new_password_hash,))
        connection.commit()
        
        print(f"更新了 {cursor.rowcount} 行")
        
        # 验证更新
        cursor.execute("SELECT username, email, password_hash FROM acwl_users WHERE email = 'admin@acwl.ai'")
        result = cursor.fetchone()
        
        if result:
            username, email, stored_hash = result
            print(f"\n用户: {username}")
            print(f"邮箱: {email}")
            print(f"存储的哈希: {stored_hash}")
            
            # 验证密码
            is_valid = verify_password(new_password, stored_hash)
            print(f"密码验证: {'✅ 成功' if is_valid else '❌ 失败'}")
            
            if is_valid:
                print(f"\n✅ admin用户密码已成功更新为: {new_password}")
                print("现在可以使用以下凭据登录:")
                print(f"邮箱: admin@acwl.ai")
                print(f"密码: {new_password}")
            else:
                print(f"\n❌ 密码更新失败，验证不通过")
        else:
            print("❌ 未找到admin用户")
            
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_password()