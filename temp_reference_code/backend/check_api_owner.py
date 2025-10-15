#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查API所有者信息
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from app.db.database import get_db
    from app.models.api import CustomApi
except ImportError:
    # 如果直接导入失败，尝试设置PYTHONPATH
    import subprocess
    result = subprocess.run([
        'python', '-c', 
        'import sys; sys.path.insert(0, "."); from app.db.database import get_db; from app.models.api import CustomApi; db = next(get_db()); api = db.query(CustomApi).filter(CustomApi.api_code == "test22333_upload").first(); print(f"API: {api.api_code}, Customer ID: {api.customer_id}, Status: {api.status}" if api else "API not found"); db.close()'
    ], capture_output=True, text=True, cwd=project_root)
    print(result.stdout)
    if result.stderr:
        print(f"错误: {result.stderr}")
    sys.exit(0)

def check_api_owner(api_code: str):
    """
    检查API的所有者信息
    
    Args:
        api_code: API代码
    """
    db = next(get_db())
    
    try:
        api = db.query(CustomApi).filter(
            CustomApi.api_code == api_code
        ).first()
        
        if api:
            print(f"API代码: {api.api_code}")
            print(f"所有者ID: {api.customer_id}")
            print(f"状态: {'激活' if api.status else '停用'}")
            print(f"创建时间: {api.created_at}")
            return api.customer_id
        else:
            print(f"❌ 未找到API: {api_code}")
            return None
            
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    api_code = "test22333_upload"
    print(f"检查API代码: {api_code}")
    print("=" * 50)
    check_api_owner(api_code)