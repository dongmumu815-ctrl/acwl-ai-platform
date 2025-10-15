#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token认证接口的pytest测试

使用pytest框架测试/api/v1/auth/token接口的各种场景

Author: System
Date: 2024
"""

import pytest
import time
import hmac
import hashlib
import random
import string
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db
from app.core.config import settings
from app.models.customer import Customer

# 创建测试数据库引擎
engine = create_engine(settings.DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建测试客户端
client = TestClient(app)

# 测试数据
TEST_CUSTOMER_DATA = {
    "app_id": "test_app_001",
    "app_secret": "test_secret_123456789",
    "name": "测试客户",
    "email": "test@example.com",
    "status": True
}

class TestTokenAuth:
    """
    Token认证测试类
    """
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """
        测试前置设置
        """
        self.used_nonces = set()
        
        # 确保测试客户存在
        db = TestingSessionLocal()
        try:
            customer = db.query(Customer).filter(
                Customer.app_id == TEST_CUSTOMER_DATA["app_id"]
            ).first()
            
            if not customer:
                # 创建测试客户
                customer = Customer(
                    app_id=TEST_CUSTOMER_DATA["app_id"],
                    app_secret=TEST_CUSTOMER_DATA["app_secret"],
                    name=TEST_CUSTOMER_DATA["name"],
                    email=TEST_CUSTOMER_DATA["email"],
                    status=TEST_CUSTOMER_DATA["status"]
                )
                db.add(customer)
                db.commit()
        finally:
            db.close()
    
    def generate_nonce(self, length: int = 12) -> str:
        """
        生成唯一的随机nonce
        
        Args:
            length: nonce长度
            
        Returns:
            str: 随机nonce字符串
        """
        chars = string.ascii_letters + string.digits
        nonce = ''.join(random.choice(chars) for _ in range(length))
        
        # 确保nonce唯一
        while nonce in self.used_nonces:
            nonce = ''.join(random.choice(chars) for _ in range(length))
        
        self.used_nonces.add(nonce)
        return nonce
    
    def generate_signature(self, appid: str, timestamp: int, nonce: str, secret: str) -> str:
        """
        生成HMAC-SHA256签名
        
        Args:
            appid: 应用ID
            timestamp: 时间戳
            nonce: 随机字符串
            secret: 预共享密钥
            
        Returns:
            str: 签名值（大写十六进制）
        """
        signature_data = f"{appid}{timestamp}{nonce}"
        signature = hmac.new(
            secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        return signature
    
    def create_auth_request(self, **kwargs) -> dict:
        """
        创建认证请求数据
        
        Args:
            **kwargs: 可选参数覆盖
            
        Returns:
            dict: 认证请求数据
        """
        appid = kwargs.get('appid', TEST_CUSTOMER_DATA['app_id'])
        timestamp = kwargs.get('timestamp', int(time.time()))
        nonce = kwargs.get('nonce', self.generate_nonce())
        secret = kwargs.get('secret', TEST_CUSTOMER_DATA['app_secret'])
        
        if 'signature' in kwargs:
            signature = kwargs['signature']
        else:
            signature = self.generate_signature(appid, timestamp, nonce, secret)
        
        return {
            "appid": appid,
            "timestamp": timestamp,
            "nonce": nonce,
            "signature": signature
        }
    
    def test_successful_authentication(self):
        """
        测试成功的认证流程
        """
        auth_data = self.create_auth_request()
        
        response = client.post("/api/v1/auth/token", json=auth_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应字段
        assert "access_token" in data
        assert "data_key" in data
        assert "expires_in" in data
        
        # 验证字段类型和格式
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert isinstance(data["data_key"], str)
        assert len(data["data_key"]) > 0
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0
    
    def test_time_window_validation(self):
        """
        测试时间窗口校验
        """
        # 测试过期时间戳（超过5分钟）
        old_timestamp = int(time.time()) - 400  # 6分40秒前
        auth_data = self.create_auth_request(timestamp=old_timestamp)
        
        response = client.post("/api/v1/auth/token", json=auth_data)
        
        assert response.status_code == 402
        assert "时间戳" in response.json()["message"]
    
    def test_nonce_replay_protection(self):
        """
        测试防重放攻击（nonce校验）
        """
        # 第一次请求
        nonce = self.generate_nonce()
        timestamp = int(time.time())
        auth_data = self.create_auth_request(timestamp=timestamp, nonce=nonce)
        
        response1 = client.post("/api/v1/auth/token", json=auth_data)
        assert response1.status_code == 200
        
        # 重复使用相同的nonce
        response2 = client.post("/api/v1/auth/token", json=auth_data)
        assert response2.status_code == 403
        assert "重放" in response2.json()["message"]
    
    def test_signature_validation(self):
        """
        测试签名验证
        """
        # 使用错误的签名
        auth_data = self.create_auth_request(
            signature="WRONG_SIGNATURE_12345678901234567890123456789012"
        )
        
        response = client.post("/api/v1/auth/token", json=auth_data)
        
        assert response.status_code == 401
        assert "签名" in response.json()["message"]
    
    def test_invalid_appid(self):
        """
        测试无效的appid
        """
        auth_data = self.create_auth_request(appid="invalid_app_id")
        
        response = client.post("/api/v1/auth/token", json=auth_data)
        
        assert response.status_code == 404
        assert "appid" in response.json()["message"]
    
    def test_missing_parameters(self):
        """
        测试缺少必需参数
        """
        base_data = self.create_auth_request()
        
        # 测试缺少各个必需字段
        required_fields = ["appid", "timestamp", "nonce", "signature"]
        
        for field in required_fields:
            incomplete_data = base_data.copy()
            del incomplete_data[field]
            
            response = client.post("/api/v1/auth/token", json=incomplete_data)
            assert response.status_code == 422  # Validation Error
    
    def test_invalid_nonce_length(self):
        """
        测试无效的nonce长度
        """
        # nonce太短（少于8位）
        auth_data = self.create_auth_request(nonce="short")
        response = client.post("/api/v1/auth/token", json=auth_data)
        assert response.status_code == 422
        
        # nonce太长（超过16位）
        auth_data = self.create_auth_request(nonce="a" * 20)
        response = client.post("/api/v1/auth/token", json=auth_data)
        assert response.status_code == 422
    
    def test_invalid_timestamp_type(self):
        """
        测试无效的时间戳类型
        """
        # 使用字符串而不是整数
        auth_data = self.create_auth_request()
        auth_data["timestamp"] = "invalid_timestamp"
        
        response = client.post("/api/v1/auth/token", json=auth_data)
        assert response.status_code == 422
    
    def test_empty_signature(self):
        """
        测试空签名
        """
        auth_data = self.create_auth_request(signature="")
        
        response = client.post("/api/v1/auth/token", json=auth_data)
        assert response.status_code == 401
    
    def test_future_timestamp(self):
        """
        测试未来时间戳
        """
        # 使用未来时间戳（超过5分钟）
        future_timestamp = int(time.time()) + 400  # 6分40秒后
        auth_data = self.create_auth_request(timestamp=future_timestamp)
        
        response = client.post("/api/v1/auth/token", json=auth_data)
        assert response.status_code == 402
    
    def test_disabled_customer(self):
        """
        测试禁用的客户
        """
        # 创建一个禁用的测试客户
        disabled_customer_data = {
            "app_id": "disabled_app_001",
            "app_secret": "disabled_secret_123",
            "name": "禁用客户",
            "email": "disabled@example.com",
            "status": False  # 禁用状态
        }
        
        db = TestingSessionLocal()
        try:
            # 删除可能存在的旧记录
            db.query(Customer).filter(
                Customer.app_id == disabled_customer_data["app_id"]
            ).delete()
            
            # 创建禁用的客户
            customer = Customer(**disabled_customer_data)
            db.add(customer)
            db.commit()
            
            # 使用禁用客户的凭据进行认证
            auth_data = self.create_auth_request(
                appid=disabled_customer_data["app_id"],
                secret=disabled_customer_data["app_secret"]
            )
            
            response = client.post("/api/v1/auth/token", json=auth_data)
            assert response.status_code == 404  # 禁用的客户应该被视为不存在
            
        finally:
            # 清理测试数据
            db.query(Customer).filter(
                Customer.app_id == disabled_customer_data["app_id"]
            ).delete()
            db.commit()
            db.close()
    
    def test_signature_case_sensitivity(self):
        """
        测试签名的大小写敏感性
        """
        auth_data = self.create_auth_request()
        
        # 将签名转换为小写
        auth_data["signature"] = auth_data["signature"].lower()
        
        response = client.post("/api/v1/auth/token", json=auth_data)
        assert response.status_code == 401  # 签名应该是大写的
    
    def test_multiple_valid_requests(self):
        """
        测试多个有效请求（使用不同的nonce）
        """
        for i in range(3):
            auth_data = self.create_auth_request()  # 每次生成新的nonce
            response = client.post("/api/v1/auth/token", json=auth_data)
            assert response.status_code == 200
            
            data = response.json()
            assert "access_token" in data
            assert "data_key" in data
            assert "expires_in" in data
    
    @pytest.mark.parametrize("nonce_length", [8, 10, 12, 16])
    def test_valid_nonce_lengths(self, nonce_length):
        """
        测试有效的nonce长度
        
        Args:
            nonce_length: nonce长度
        """
        nonce = self.generate_nonce(nonce_length)
        auth_data = self.create_auth_request(nonce=nonce)
        
        response = client.post("/api/v1/auth/token", json=auth_data)
        assert response.status_code == 200
    
    def test_concurrent_requests_different_nonces(self):
        """
        测试并发请求（使用不同的nonce）
        """
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            """发送单个请求"""
            try:
                auth_data = self.create_auth_request()
                response = client.post("/api/v1/auth/token", json=auth_data)
                results.put(response.status_code)
            except Exception as e:
                results.put(f"error: {e}")
        
        # 创建5个并发线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
        
        # 所有请求都应该成功（因为使用了不同的nonce）
        assert success_count == 5

# 运行测试的便捷函数
def run_tests():
    """
    运行所有测试
    """
    pytest.main(["-v", __file__])

if __name__ == "__main__":
    run_tests()