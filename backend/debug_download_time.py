#!/usr/bin/env python3
"""调试资源包下载时间的脚本"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.resource_package import ResourcePackage

def debug_download_time():
    """调试资源包下载时间"""
    
    # 创建数据库连接
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        # 查询资源包ID=2的信息
        result = db.execute(
            select(ResourcePackage.id, ResourcePackage.name, ResourcePackage.download_time)
            .where(ResourcePackage.id == 2)
        )
        
        package = result.first()
        
        if package:
            print(f"资源包ID: {package.id}")
            print(f"资源包名称: {package.name}")
            print(f"下载时间值: {package.download_time}")
            print(f"下载时间类型: {type(package.download_time)}")
            
            # 检查是否为整数或浮点数
            if isinstance(package.download_time, (int, float)):
                print(f"⚠️  发现问题：download_time是数字类型 {type(package.download_time)}")
                try:
                    converted_time = datetime.fromtimestamp(package.download_time)
                    print(f"转换后的时间: {converted_time}")
                except Exception as e:
                    print(f"转换失败: {e}")
            elif isinstance(package.download_time, datetime):
                print("✅ download_time是正确的datetime类型")
            elif package.download_time is None:
                print("ℹ️  download_time为None")
            else:
                print(f"❓ 未知类型: {type(package.download_time)}")
        else:
            print("未找到资源包ID=2")

if __name__ == "__main__":
    debug_download_time()