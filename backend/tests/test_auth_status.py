#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试认证状态和创建测试用户
"""

import requests
import json
import pymysql
from backend.app.core.config import settings


def check_users_table():
    """检查用户表数据"""
    
    try:
        # 创建数据库连接
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset=settings.DB_CHARSET
        )
        
        print("检查用户表数据...")
        
        with connection.cursor() as cursor:
            # 检查用户表是否存在
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = %s AND table_name = 'acwl_users'",
                (settings.DB_NAME,)
            )
            table_exists = cursor.fetchone()[0]
            
            if table_exists == 0:
                print("用户表不存在")
                return
            
            # 查看表结构
            cursor.execute("DESCRIBE acwl_users")
            columns = cursor.fetchall()
            print("\n用户表结构:")
            for col in columns:
                print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]}")
            
            # 查看所有用户数据
            cursor.execute("SELECT id, username, email, role, is_active, is_admin, created_at FROM acwl_users")
            users = cursor.fetchall()
            
            print(f"\n用户表数据 (共{len(users)}条):")
            if users:
                for user in users:
                    print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}, Active: {user[4]}, Admin: {user[5]}, Created: {user[6]}")
            else:
                print("  没有用户数据")
                
    except Exception as e:
        print(f"检查用户表失败: {e}")
    
    finally:
        if 'connection' in locals():
            connection.close()


def create_simple_user():
    """创建简单测试用户"""
    
    try:
        # 创建数据库连接
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset=settings.DB_CHARSET
        )
        
        print("\n创建简单测试用户...")
        
        with connection.cursor() as cursor:
            # 删除已存在的测试用户
            cursor.execute("DELETE FROM acwl_users WHERE username = 'testuser'")
            
            # 使用简单的密码哈希（实际应用中不推荐）
            import hashlib
            simple_hash = hashlib.sha256("testpass123".encode()).hexdigest()
            
            # 创建测试用户
            cursor.execute(
                "INSERT INTO acwl_users (username, email, password_hash, role, is_active, is_admin) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                ("testuser", "test@example.com", simple_hash, "user", 1, 0)
            )
            
            connection.commit()
            user_id = cursor.lastrowid
            print(f"简单测试用户创建成功: ID={user_id}, Username=testuser, Password=testpass123")
            print(f"密码哈希: {simple_hash}")
            return user_id
            
    except Exception as e:
        print(f"创建简单测试用户失败: {e}")
        return None
    
    finally:
        if 'connection' in locals():
            connection.close()


def test_register_new_user():
    """测试注册新用户"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("\n测试用户注册...")
    register_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpass123",
        "confirm_password": "newpass123"
    }
    
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{base_url}/api/v1/auth/register", 
                               json=register_data, headers=headers)
        print(f"注册状态码: {response.status_code}")
        print(f"注册响应: {response.text}")
        
        if response.status_code == 201 or response.status_code == 200:
             print("用户注册成功")
             print(f"用户信息: {response.text}")
            
            # 尝试登录新注册的用户
            print("\n尝试登录新注册的用户...")
            login_data = {
                "username": "newuser",
                "password": "newpass123"
            }
            
            response = requests.post(f"{base_url}/api/v1/auth/login/json", 
                                   json=login_data, headers=headers)
            print(f"登录状态码: {response.status_code}")
            print(f"登录响应: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                
                if access_token:
                    print(f"\n登录成功，获得token: {access_token[:50]}...")
                    
                    # 使用token测试模型API
                    print("\n使用token测试模型API...")
                    auth_headers = {"Authorization": f"Bearer {access_token}"}
                    
                    response = requests.get(f"{base_url}/api/v1/models/", headers=auth_headers)
                    print(f"模型API状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"模型API响应成功:")
                        print(f"  总数: {data.get('total', 'N/A')}")
                        print(f"  页码: {data.get('page', 'N/A')}")
                        print(f"  每页大小: {data.get('size', 'N/A')}")
                        print(f"  项目数量: {len(data.get('items', []))}")
                        
                        if data.get('items'):
                            print("\n模型列表:")
                            for i, item in enumerate(data['items']):
                                print(f"  {i+1}. {item.get('name')}:{item.get('version')} (Type: {item.get('model_type')}, Active: {item.get('is_active')})")
                        else:
                            print("\n没有找到模型数据")
                    else:
                        print(f"模型API调用失败: {response.text}")
        else:
            print(f"用户注册失败: {response.text}")
            
    except Exception as e:
        print(f"注册测试失败: {e}")


def test_without_auth():
    """测试不带认证的API调用"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("\n测试不带认证的API调用...")
    
    try:
        # 测试健康检查
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"健康检查状态码: {response.status_code}")
        print(f"健康检查响应: {response.text}")
        
        # 测试模型API（应该返回401）
        response = requests.get(f"{base_url}/api/v1/models/")
        print(f"\n模型API（无认证）状态码: {response.status_code}")
        print(f"模型API（无认证）响应: {response.text}")
        
    except Exception as e:
        print(f"无认证API测试失败: {e}")


if __name__ == "__main__":
    print("开始测试认证状态...")
    print("注意：请确保后端服务器正在运行")
    
    check_users_table()
    create_simple_user()
    test_register_new_user()
    test_without_auth()