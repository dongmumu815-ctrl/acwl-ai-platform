#!/usr/bin/env python3
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url.replace('aiomysql', 'pymysql'))
with engine.connect() as conn:
    result = conn.execute(text('SHOW COLUMNS FROM acwl_scheduler_nodes'))
    print('表字段:')
    for row in result:
        print(row[0])