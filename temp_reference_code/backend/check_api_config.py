#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.api import CustomApi

def main():
    # 获取命令行参数中的API代码，默认为'test22333'
    api_code = sys.argv[1] if len(sys.argv) > 1 else 'test22333'
    print(f'查询API代码: {api_code}')
    
    db = next(get_db())
    try:
        api = db.query(CustomApi).filter(CustomApi.api_code == api_code).first()
        if api:
            print('API配置:')
            print(f'ID: {api.id}')
            print(f'名称: {api.api_name}')
            print(f'URL: {api.api_url}')
            print(f'方法: {api.http_method}')
            print(f'需要认证: {api.require_authentication}')
            
            fields = list(api.fields)
            print(f'字段数量: {len(fields)}')
            for field in fields:
                print(f'字段: {field.field_name}, 类型: {field.field_type}, 必填: {field.is_required}')
        else:
            print('API不存在')
    finally:
        db.close()

if __name__ == '__main__':
    main()