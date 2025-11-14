#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
from pathlib import Path
from app.core.config import settings

def run_migration():
    """执行为用户表添加部门、手机号、状态、备注字段的迁移（函数级注释）

    - 读取 `migrations/022_add_user_profile_fields.sql`
    - 使用配置中的数据库连接执行每条 SQL 语句
    - 对已存在字段的错误进行容忍处理，保证幂等执行
    - 最后验证字段是否存在并打印结果
    """
    migration_file = Path(__file__).parent / "migrations" / "022_add_user_profile_fields.sql"
    if not migration_file.exists():
        print(f"❌ 迁移文件不存在: {migration_file}")
        return False

    sql_text = migration_file.read_text(encoding="utf-8")
    statements = [stmt.strip() for stmt in sql_text.split(';') if stmt.strip()]

    conn = None
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset=settings.DB_CHARSET,
            autocommit=False
        )
        print(f"✅ 已连接数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        cur = conn.cursor()

        for i, stmt in enumerate(statements, 1):
            print(f"🔄 执行语句 {i}: {stmt[:80]}...")
            try:
                cur.execute(stmt)
                print(f"✅ 语句 {i} 执行成功")
            except Exception as e:
                msg = str(e)
                # 容忍已存在列/索引等错误，保证幂等
                if "Duplicate column name" in msg or "already exists" in msg or "Duplicate key name" in msg:
                    print(f"⚠️  语句 {i} 跳过（对象已存在）: {e}")
                    continue
                else:
                    print(f"❌ 语句 {i} 执行失败: {e}")
                    conn.rollback()
                    return False

        conn.commit()
        print("✅ 迁移执行成功，事务已提交")

        # 验证新字段是否存在
        verify_sql = """
        SELECT COLUMN_NAME FROM information_schema.columns
        WHERE table_schema = %s AND table_name = 'acwl_users'
          AND COLUMN_NAME IN ('department','phone','status','remark')
        """
        cur.execute(verify_sql, (settings.DB_NAME,))
        cols = [row[0] for row in cur.fetchall()]
        print(f"📊 新字段存在情况: {cols}")
        missing = {"department","phone","status","remark"} - set(cols)
        if missing:
            print(f"❌ 仍缺失字段: {missing}")
            return False

        return True
    except Exception as e:
        print(f"❌ 迁移执行异常: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    ok = run_migration()
    print("结果:", "成功" if ok else "失败")