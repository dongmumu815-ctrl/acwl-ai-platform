#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密服务模块

提供数据加密、解密、签名验证等功能。

Author: System
Date: 2024
"""

import hashlib
import hmac
import base64
from typing import Optional, Union
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import logging


class EncryptionService:
    """
    加密服务
    
    提供AES加密解密、HMAC签名验证等功能
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.block_size = AES.block_size
    
    def encrypt_data(
        self, 
        data: Union[str, bytes], 
        key: Union[str, bytes], 
        iv: Optional[bytes] = None
    ) -> tuple[bytes, bytes]:
        """
        使用AES-CBC模式加密数据
        
        Args:
            data: 要加密的数据
            key: 加密密钥（32字节）
            iv: 初始化向量（16字节），如果为None则自动生成
            
        Returns:
            tuple: (加密后的数据, 初始化向量)
            
        Raises:
            ValueError: 密钥长度不正确
        """
        try:
            # 处理输入数据
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            if isinstance(key, str):
                key = key.encode('utf-8')
            
            # 确保密钥长度为32字节
            if len(key) != 32:
                key = hashlib.sha256(key).digest()
            
            # 生成或使用提供的IV
            if iv is None:
                iv = get_random_bytes(self.block_size)
            
            # 创建加密器
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # 填充数据并加密
            padded_data = pad(data, self.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            
            self.logger.debug(f"Data encrypted successfully, size: {len(encrypted_data)}")
            return encrypted_data, iv
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"加密失败: {str(e)}")
    
    def decrypt_data(
        self, 
        encrypted_data: bytes, 
        key: Union[str, bytes], 
        iv: bytes
    ) -> str:
        """
        使用AES-CBC模式解密数据
        
        Args:
            encrypted_data: 加密的数据
            key: 解密密钥（32字节）
            iv: 初始化向量（16字节）
            
        Returns:
            str: 解密后的数据
            
        Raises:
            ValueError: 解密失败
        """
        try:
            # 处理密钥
            if isinstance(key, str):
                key = key.encode('utf-8')
            
            # 确保密钥长度为32字节
            if len(key) != 32:
                key = hashlib.sha256(key).digest()
            
            # 创建解密器
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # 解密并去除填充
            decrypted_padded = cipher.decrypt(encrypted_data)
            decrypted_data = unpad(decrypted_padded, self.block_size)
            
            self.logger.debug(f"Data decrypted successfully, size: {len(decrypted_data)}")
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"解密失败: {str(e)}")
    
    def generate_signature(
        self, 
        key: Union[str, bytes], 
        data: Union[str, bytes]
    ) -> str:
        """
        生成HMAC-SHA256签名
        
        Args:
            key: 签名密钥
            data: 要签名的数据
            
        Returns:
            str: Base64编码的签名
        """
        try:
            # 处理输入
            if isinstance(key, str):
                key = key.encode('utf-8')
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # 生成HMAC签名
            signature = hmac.new(
                key, 
                data, 
                hashlib.sha256
            ).digest()
            
            # Base64编码
            encoded_signature = base64.b64encode(signature).decode('utf-8')
            
            self.logger.debug("Signature generated successfully")
            return encoded_signature
            
        except Exception as e:
            self.logger.error(f"Signature generation failed: {str(e)}")
            raise ValueError(f"签名生成失败: {str(e)}")
    
    def verify_signature(
        self, 
        key: Union[str, bytes], 
        data: Union[str, bytes], 
        signature: str
    ) -> bool:
        """
        验证HMAC-SHA256签名
        
        Args:
            key: 签名密钥
            data: 原始数据
            signature: Base64编码的签名
            
        Returns:
            bool: 签名是否有效
        """
        try:
            # 生成期望的签名
            expected_signature = self.generate_signature(key, data)
            
            # 比较签名
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            self.logger.debug(f"Signature verification result: {is_valid}")
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Signature verification failed: {str(e)}")
            return False
    
    def generate_random_key(self, length: int = 32) -> bytes:
        """
        生成随机密钥
        
        Args:
            length: 密钥长度（字节）
            
        Returns:
            bytes: 随机密钥
        """
        return get_random_bytes(length)
    
    def generate_random_iv(self) -> bytes:
        """
        生成随机初始化向量
        
        Returns:
            bytes: 16字节的随机IV
        """
        return get_random_bytes(self.block_size)
    
    def hash_data(self, data: Union[str, bytes], algorithm: str = 'sha256') -> str:
        """
        计算数据哈希值
        
        Args:
            data: 要哈希的数据
            algorithm: 哈希算法（sha256, sha1, md5等）
            
        Returns:
            str: 十六进制哈希值
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            hash_obj = hashlib.new(algorithm)
            hash_obj.update(data)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Hash calculation failed: {str(e)}")
            raise ValueError(f"哈希计算失败: {str(e)}")


# 全局服务实例
encryption_service = EncryptionService()


if __name__ == "__main__":
    # 测试加密服务
    print("加密服务测试开始...")
    
    service = EncryptionService()
    
    # 测试加密解密
    try:
        test_data = "Hello, World! 这是测试数据。"
        test_key = "test_key_32_bytes_long_for_aes!"
        
        # 加密
        encrypted, iv = service.encrypt_data(test_data, test_key)
        print(f"加密成功，数据长度: {len(encrypted)}")
        
        # 解密
        decrypted = service.decrypt_data(encrypted, test_key, iv)
        print(f"解密成功: {decrypted}")
        
        # 验证
        assert decrypted == test_data
        print("✓ 加密解密测试通过")
        
    except Exception as e:
        print(f"✗ 加密解密测试失败: {e}")
    
    # 测试签名
    try:
        test_data = "test signature data"
        test_key = "signature_key"
        
        # 生成签名
        signature = service.generate_signature(test_key, test_data)
        print(f"签名生成成功: {signature[:20]}...")
        
        # 验证签名
        is_valid = service.verify_signature(test_key, test_data, signature)
        assert is_valid
        print("✓ 签名验证测试通过")
        
    except Exception as e:
        print(f"✗ 签名测试失败: {e}")
    
    print("加密服务测试完成")