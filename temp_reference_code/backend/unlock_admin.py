#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, text
from app.core.config import settings

def unlock_admin():
    engine = create_engine(settings.DATABASE_URL)
    conn = engine.connect()
    
    try:
        # 检查当前状态
        result = conn.execute(text(
            "SELECT username, failed_login_count, locked_until FROM admin_users WHERE username = 'admin'"
        ))
        row = result.fetchone()
        
        if row:
            print(f'用户名: {row[0]}')
            print(f'失败登录次数: {row[1]}')
            print(f'锁定到: {row[2]}')
            
            # 解锁账户
            conn.execute(text(
                "UPDATE admin_users SET failed_login_count = 0, locked_until = NULL WHERE username = 'admin'"
            ))
            conn.commit()
            print('✅ 管理员账户已解锁')
        else:
            print('❌ 未找到管理员用户')
            
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        engine.dispose()

if __name__ == '__main__':
    unlock_admin()