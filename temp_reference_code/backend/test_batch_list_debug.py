#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次列表接口调试脚本
检查data_batches表中的数据和接口返回情况
"""

import requests
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 测试配置
API_BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidHlwZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzUzMTY0MDc1LCJpYXQiOjE3NTMwNzc2NzUsImp0aSI6InlOUm9GZWpobkZJR3p6YlB4QkF4ejVfTkRrdWl2Um5pSXhhOGxUQXBJWUUiLCJjdXN0b21lcl9pZCI6NiwiYXBwX2lkIjoidGVzdF9hcHBfMDAxIn0.r1if0CDb9ANFCd2_VVA1Q_k59YmTLrKOSqPu1oM8QoQ"

def check_database_data():
    """
    检查数据库中的data_batches表数据
    """
    print("=== 检查数据库中的data_batches表数据 ===")
    
    try:
        # 从环境变量获取数据库连接信息
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            # 尝试构建数据库URL
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '3306')
            db_user = os.getenv('DB_USER', 'root')
            db_password = os.getenv('DB_PASSWORD', '')
            db_name = os.getenv('DB_NAME', 'acwl_api')
            database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        print(f"数据库连接: {database_url.replace(db_password, '***') if 'db_password' in locals() else database_url}")
        
        # 创建数据库连接
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            # 检查data_batches表总数
            result = session.execute(text("SELECT COUNT(*) as total FROM data_batches"))
            total_count = result.fetchone()[0]
            print(f"data_batches表总记录数: {total_count}")
            
            # 检查customer_id=6的记录数
            result = session.execute(text("SELECT COUNT(*) as total FROM data_batches WHERE customer_id = 6"))
            customer_count = result.fetchone()[0]
            print(f"customer_id=6的记录数: {customer_count}")
            
            # 查看最近的几条记录
            result = session.execute(text("""
                SELECT batch_id, customer_id, batch_name, status, created_at 
                FROM data_batches 
                ORDER BY created_at DESC 
                LIMIT 10
            """))
            
            records = result.fetchall()
            print(f"\n最近的{len(records)}条记录:")
            for record in records:
                print(f"  - batch_id: {record[0]}, customer_id: {record[1]}, batch_name: {record[2]}, status: {record[3]}, created_at: {record[4]}")
            
            # 查看customer_id=6的记录
            result = session.execute(text("""
                SELECT batch_id, customer_id, batch_name, status, created_at 
                FROM data_batches 
                WHERE customer_id = 6
                ORDER BY created_at DESC 
                LIMIT 5
            """))
            
            customer_records = result.fetchall()
            print(f"\ncustomer_id=6的最近{len(customer_records)}条记录:")
            for record in customer_records:
                print(f"  - batch_id: {record[0]}, customer_id: {record[1]}, batch_name: {record[2]}, status: {record[3]}, created_at: {record[4]}")
                
    except Exception as e:
        print(f"数据库检查失败: {e}")
        print("请确保数据库连接配置正确")

def test_batch_list_api():
    """
    测试批次列表API接口
    """
    print("\n=== 测试批次列表API接口 ===")
    
    # 准备请求头
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    # 构建请求URL
    url = f"{API_BASE_URL}/api/v1/batch/?page=1&size=20"
    
    print(f"请求URL: {url}")
    print(f"请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    
    try:
        # 发送请求
        response = requests.get(url, headers=headers)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                print(f"\n✅ 接口调用成功！")
                print(f"总数: {response_data.get('total', 0)}")
                print(f"当前页: {response_data.get('page', 0)}")
                print(f"每页大小: {response_data.get('size', 0)}")
                print(f"返回项目数: {len(response_data.get('items', []))}")
            else:
                print(f"\n❌ 接口调用失败！")
                
        except json.JSONDecodeError:
            print(f"响应文本: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求异常: {e}")
    except Exception as e:
        print(f"\n❌ 其他异常: {e}")

def test_token_validation():
    """
    测试token验证
    """
    print("\n=== 测试Token验证 ===")
    
    # 准备请求头
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    # 测试一个简单的接口来验证token
    url = f"{API_BASE_URL}/api/v1/batch/test_batch_123"
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Token验证测试 - 状态码: {response.status_code}")
        
        if response.status_code == 401:
            print("❌ Token无效或已过期")
        elif response.status_code == 404:
            print("✅ Token有效（批次不存在是正常的）")
        else:
            print(f"Token验证结果: {response.status_code}")
            
    except Exception as e:
        print(f"Token验证失败: {e}")

if __name__ == "__main__":
    print("批次列表接口调试脚本")
    print(f"Token: {TOKEN[:50]}...")
    
    # 检查数据库数据
    check_database_data()
    
    # 测试token验证
    test_token_validation()
    
    # 测试批次列表接口
    test_batch_list_api()
    
    print("\n调试完成！")