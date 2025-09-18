#!/usr/bin/env python3
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url.replace('aiomysql', 'pymysql'))
with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE acwl_scheduler_nodes ADD COLUMN capabilities JSON COMMENT "节点能力列表"'))
        print('capabilities字段已添加')
    except Exception as e:
        print(f'capabilities字段添加失败或已存在: {e}')
    
    try:
        conn.execute(text('ALTER TABLE acwl_scheduler_nodes ADD COLUMN metrics JSON COMMENT "性能指标"'))
        print('metrics字段已添加')
    except Exception as e:
        print(f'metrics字段添加失败或已存在: {e}')
    
    conn.commit()
    print('操作完成')