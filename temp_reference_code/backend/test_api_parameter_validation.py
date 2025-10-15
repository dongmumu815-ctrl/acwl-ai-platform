#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证API参数结构是否符合文档要求

检查数据上传接口的参数结构是否与API文档中定义的一致：
- timestamp: 时间戳
- nonce: 随机字符串
- data: 加密后的业务数据（Base64编码）
- iv: 初始化向量
- signature: 数据签名值
- needread: 是否需要读取确认

Author: System
Date: 2024
"""

import json
import inspect
from typing import get_type_hints
from pydantic import BaseModel

# 导入数据上传请求模型
try:
    from app.api.v1.endpoints.data import DataUploadRequest
except ImportError as e:
    print(f"❌ 无法导入DataUploadRequest: {e}")
    exit(1)

def validate_model_structure():
    """
    验证DataUploadRequest模型结构是否符合API文档要求
    """
    print("=== 验证数据上传请求模型结构 ===")
    
    # 期望的字段和类型
    expected_fields = {
        'timestamp': int,
        'nonce': str,
        'data': str,
        'iv': str,
        'signature': str,  # Optional[str]
        'needread': bool
    }
    
    print(f"\n📋 期望的字段结构:")
    for field, field_type in expected_fields.items():
        print(f"  - {field}: {field_type.__name__}")
    
    # 获取模型字段（使用Pydantic V2 API）
    model_fields = DataUploadRequest.model_fields
    
    print(f"\n🔍 实际模型字段:")
    for field_name, field_info in model_fields.items():
        field_type = field_info.annotation
        is_required = field_info.is_required()
        default = field_info.default
        description = field_info.description
        
        print(f"  - {field_name}: {field_type} (必填: {is_required}, 默认值: {default})")
        if description:
            print(f"    描述: {description}")
    
    # 验证字段完整性
    print(f"\n✅ 字段验证结果:")
    missing_fields = []
    extra_fields = []
    type_mismatches = []
    
    # 检查缺失字段
    for expected_field in expected_fields:
        if expected_field not in model_fields:
            missing_fields.append(expected_field)
    
    # 检查额外字段
    for actual_field in model_fields:
        if actual_field not in expected_fields:
            extra_fields.append(actual_field)
    
    # 检查类型匹配
    for field_name in expected_fields:
        if field_name in model_fields:
            expected_type = expected_fields[field_name]
            actual_type = model_fields[field_name].annotation
            
            # 处理Optional类型
            if hasattr(actual_type, '__origin__'):
                if actual_type.__origin__ is type(None) or str(actual_type).startswith('typing.Union'):
                    # 这是Optional类型，获取实际类型
                    if hasattr(actual_type, '__args__'):
                        actual_type = actual_type.__args__[0]
            
            if actual_type != expected_type:
                type_mismatches.append((field_name, expected_type, actual_type))
    
    if not missing_fields and not extra_fields and not type_mismatches:
        print("  ✅ 所有字段都符合API文档要求")
        return True
    else:
        if missing_fields:
            print(f"  ❌ 缺失字段: {missing_fields}")
        if extra_fields:
            print(f"  ⚠️ 额外字段: {extra_fields}")
        if type_mismatches:
            print(f"  ❌ 类型不匹配:")
            for field, expected, actual in type_mismatches:
                print(f"    - {field}: 期望 {expected}, 实际 {actual}")
        return False

def generate_sample_request():
    """
    生成符合文档要求的示例请求
    """
    print(f"\n=== 生成示例请求数据 ===")
    
    # 根据文档生成示例数据
    sample_request = {
        "timestamp": 1720980000,
        "nonce": "a1b2c3d4",
        "data": "base64_encoded_aes_gcm_ciphertext",
        "iv": "base64_encoded_initialization_vector",
        "signature": "HMAC_SHA256(data_key, encrypted_data)",
        "needread": True
    }
    
    print(f"📝 示例请求数据 (符合API文档):")
    print(json.dumps(sample_request, indent=2, ensure_ascii=False))
    
    # 验证示例数据是否能被模型接受
    try:
        model_instance = DataUploadRequest(**sample_request)
        print(f"\n✅ 示例数据验证通过")
        print(f"模型实例: {model_instance}")
        return True
    except Exception as e:
        print(f"\n❌ 示例数据验证失败: {e}")
        return False

def check_api_documentation_compliance():
    """
    检查API实现是否符合文档要求
    """
    print(f"\n=== API文档合规性检查 ===")
    
    # 文档中的示例数据
    doc_example = {
        "timestamp": 1720980000,
        "nonce": "a1b2c3d4",
        "data": "base64_encoded_aes_gcm_ciphertext",
        "iv": "base64_encoded_initialization_vector",
        "signature": "HMAC_SHA256(data_key, encrypted_data)",
        "needread": True
    }
    
    print(f"📖 API文档示例数据:")
    print(json.dumps(doc_example, indent=2, ensure_ascii=False))
    
    # 检查字段说明
    field_descriptions = {
        "timestamp": "当前时间戳（单位：秒），用于防重放攻击",
        "nonce": "随机字符串（如 8~16 位），用于增强请求唯一性",
        "data": "使用 data_key 加密后的业务数据（Base64 编码）",
        "iv": "初始化向量（IV），用于 AES 解密",
        "signature": "使用 data_key 对加密数据做的签名值（若启用签名验证则为必填）",
        "needread": "是否需要读取确认"
    }
    
    print(f"\n📋 字段说明对照:")
    model_fields = DataUploadRequest.model_fields
    
    for field_name, expected_desc in field_descriptions.items():
        if field_name in model_fields:
            actual_desc = model_fields[field_name].description
            print(f"\n  {field_name}:")
            print(f"    文档说明: {expected_desc}")
            print(f"    代码说明: {actual_desc}")
            
            if actual_desc and expected_desc.lower() in actual_desc.lower():
                print(f"    ✅ 说明匹配")
            else:
                print(f"    ⚠️ 说明可能需要更新")
        else:
            print(f"\n  ❌ 字段 {field_name} 在模型中不存在")

def main():
    """
    主函数
    """
    print("🔍 开始验证API参数结构...\n")
    
    # 1. 验证模型结构
    structure_valid = validate_model_structure()
    
    # 2. 生成示例请求
    sample_valid = generate_sample_request()
    
    # 3. 检查文档合规性
    check_api_documentation_compliance()
    
    # 总结
    print(f"\n=== 验证总结 ===")
    if structure_valid and sample_valid:
        print(f"✅ API参数结构完全符合文档要求")
        print(f"\n💡 接口已按照文档要求实现:")
        print(f"  - 支持加密数据上传")
        print(f"  - 包含所有必需的安全字段")
        print(f"  - 参数类型和结构正确")
        print(f"\n🎯 原始数据示例: [{{\"test\":\"test\",\"test2\":\"test\"}},{{\"test\":\"test2\",\"test2\":\"test3\"}}]")
        print(f"📦 加密后放入data字段，符合API文档要求")
    else:
        print(f"❌ API参数结构需要调整以符合文档要求")
        if not structure_valid:
            print(f"  - 模型结构不完整")
        if not sample_valid:
            print(f"  - 示例数据验证失败")

if __name__ == "__main__":
    main()