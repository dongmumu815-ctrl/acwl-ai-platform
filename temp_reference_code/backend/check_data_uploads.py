#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')

from app.core.database import get_db
from app.models.log import DataUpload
from sqlalchemy import desc

def main():
    db = next(get_db())
    try:
        # 查询最近的数据上传记录
        uploads = db.query(DataUpload).order_by(desc(DataUpload.created_at)).limit(5).all()
        
        print(f'最近的 {len(uploads)} 条数据上传记录:')
        print('-' * 80)
        
        for upload in uploads:
            print(f'ID: {upload.id}')
            print(f'API ID: {upload.api_id}')
            print(f'客户ID: {upload.customer_id}')
            print(f'批次ID: {upload.batch_id}')
            print(f'数据: {upload.data}')
            print(f'创建时间: {upload.created_at}')
            print('-' * 40)
            
        # 查询特定批次的数据
        batch_uploads = db.query(DataUpload).filter(
            DataUpload.batch_id.like('batch_20250716_%')
        ).order_by(desc(DataUpload.created_at)).all()
        
        print(f'\n今天批次的数据上传记录 ({len(batch_uploads)} 条):')
        print('-' * 80)
        
        for upload in batch_uploads:
            print(f'ID: {upload.id}')
            print(f'批次ID: {upload.batch_id}')
            print(f'数据: {upload.data}')
            print(f'创建时间: {upload.created_at}')
            print('-' * 40)
            
    finally:
        db.close()

if __name__ == '__main__':
    main()