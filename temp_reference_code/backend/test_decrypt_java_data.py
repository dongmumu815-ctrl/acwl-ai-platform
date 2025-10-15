#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java加密数据解密测试脚本

使用Python解密Java生成的AES-GCM加密数据，验证两种语言的加密解密兼容性。
"""

import json
import base64
from Crypto.Cipher import AES


def decrypt_java_data(data_key: str, encrypted_data: str, iv: str) -> dict:
    """
    解密Java生成的AES-GCM加密数据
    
    Args:
        data_key: Base64编码的数据密钥
        encrypted_data: Base64编码的加密数据（包含密文+认证标签）
        iv: Base64编码的初始化向量
        
    Returns:
        dict: 解密后的数据
        
    Raises:
        Exception: 解密失败时抛出异常
    """
    try:
        print("=== Java加密数据解密测试 ===")
        print(f"输入参数:")
        print(f"  data_key: {data_key}")
        print(f"  encrypted_data: {encrypted_data}")
        print(f"  iv: {iv}")
        print()
        
        # 1. 解码Base64
        key = base64.b64decode(data_key)
        encrypted_bytes = base64.b64decode(encrypted_data)
        iv_bytes = base64.b64decode(iv)
        
        print(f"解码后的数据:")
        print(f"  密钥长度: {len(key)} 字节")
        print(f"  加密数据长度: {len(encrypted_bytes)} 字节")
        print(f"  IV长度: {len(iv_bytes)} 字节")
        print()
        
        # 2. 分离密文和认证标签（GCM模式下，最后16字节是认证标签）
        ciphertext = encrypted_bytes[:-16]
        tag = encrypted_bytes[-16:]
        
        print(f"数据分离:")
        print(f"  密文长度: {len(ciphertext)} 字节")
        print(f"  认证标签长度: {len(tag)} 字节")
        print()
        
        # 3. AES-GCM解密
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv_bytes)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        
        # 4. 解析JSON数据
        decrypted_data = json.loads(plaintext.decode('utf-8'))
        
        print(f"解密成功!")
        print(f"解密后的明文: {plaintext.decode('utf-8')}")
        print(f"解析后的数据: {json.dumps(decrypted_data, ensure_ascii=False, indent=2)}")
        
        return decrypted_data
        
    except Exception as e:
        print(f"解密失败: {str(e)}")
        raise Exception(f"数据解密失败: {str(e)}")


if __name__ == "__main__":
    # 测试数据（来自Java加密结果）
    test_data_key = "m6Ln7V+kS4S/9ArgyUkEhiS105TnbU2evcyyYqvxcVg="
    test_encrypted_data = "6HwGibANrFhofntqq/BNfqEwrqRb4JD5VHj+oiIkNBFOChFlvYTZoHYlClbJ8lS08n8M3VrmzinNkATIrk9JmjIzzKdfKLmtpSOZPlHmtugSNA=="
    test_iv = "COwA9GhPENzifT3O"
    
    try:
        # 执行解密测试
        result = decrypt_java_data(test_data_key, test_encrypted_data, test_iv)
        print("\n✅ Java加密数据解密测试成功!")
        print("✅ Python可以正确解密Java生成的AES-GCM加密数据")
        
    except Exception as e:
        print(f"\n❌ 解密测试失败: {e}")