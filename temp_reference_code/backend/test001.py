# 导入必要的库
import time
import hmac
import hashlib
import random
import string

# 测试用客户数据
TEST_CUSTOMER = {
    "app_id": "test_app_001",
    "app_secret": "test_secret_123456789"
}

def generate_nonce(length: int = 12) -> str:
    """
    生成随机nonce字符串
    
    Args:
        length: nonce长度
        
    Returns:
        str: 随机nonce字符串
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_signature(appid: str, timestamp: int, nonce: str, secret: str) -> str:
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

def create_auth_request() -> dict:
    """
    创建认证请求数据
    
    Returns:
        dict: 认证请求数据
    """
    appid = TEST_CUSTOMER["app_id"]
    timestamp = int(time.time())
    nonce = generate_nonce()
    secret = TEST_CUSTOMER["app_secret"]
    
    signature = generate_signature(appid, timestamp, nonce, secret)
    
    return {
        "appid": appid,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": signature
    }

# 生成10个不同的请求参数
print("=== 10个不同的认证请求参数 ===")
for i in range(1, 11):
    request_data = create_auth_request()
    print(f"\n请求参数 {i}:")
    print(f"  appid: {request_data['appid']}")
    print(f"  timestamp: {request_data['timestamp']}")
    print(f"  nonce: {request_data['nonce']}")
    print(f"  signature: {request_data['signature']}")
    
    # 稍微延迟以确保时间戳不同
    time.sleep(0.1)

# 如果您需要JSON格式的数据，可以使用以下代码：
import json

print("\n\n=== JSON格式的请求参数 ===")
request_list = []
for i in range(10):
    request_data = create_auth_request()
    request_list.append(request_data)
    time.sleep(0.1)

print(json.dumps(request_list, indent=2, ensure_ascii=False))