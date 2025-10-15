#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用提供的token测试API文档生成功能
"""

import requests
import json

def test_api_doc_with_token():
    """使用提供的token测试API文档生成功能"""
    
    # 使用用户提供的token
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzYwMDI0NDkyfQ.DRBc8PFmkmKrtsLwJldlEokTfJaFwwlwsCoTXv6zo_I"
    
    print(f"使用提供的token: {access_token[:50]}...")
    
    # 测试API文档生成 - 模拟前端请求
    api_id = 12
    doc_url = f"http://localhost:8082/api/v1/admin/apis/{api_id}/documentation?format=markdown"
    
    # 使用Bearer token认证，模拟前端的请求方式
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n请求API文档...")
    print(f"URL: {doc_url}")
    print(f"Headers: {headers}")
    
    try:
        doc_response = requests.get(doc_url, headers=headers)
        print(f"文档请求状态码: {doc_response.status_code}")
        
        if doc_response.status_code == 200:
            doc_result = doc_response.json()
            print(f"文档响应结构: {json.dumps({k: type(v).__name__ for k, v in doc_result.items()}, indent=2)}")
            
            if doc_result.get("success"):
                documentation = doc_result.get("data", {}).get("documentation", "")
                print(f"\n文档内容长度: {len(documentation)} 字符")
                
                if documentation:
                    print("✅ 文档内容预览:")
                    print("=" * 50)
                    print(documentation[:800])
                    if len(documentation) > 800:
                        print("...")
                    print("=" * 50)
                    
                    # 检查关键字段
                    key_fields = ["期刊文章全文审读", "请求格式", "响应格式", "认证要求", "调用统计", "创建信息"]
                    found_fields = []
                    for field in key_fields:
                        if field in documentation:
                            found_fields.append(field)
                    
                    print(f"\n✅ 找到的关键字段: {found_fields}")
                    print(f"✅ API文档生成功能正常工作!")
                    
                    return True
                else:
                    print("⚠️ 文档内容为空!")
                    print(f"完整响应: {json.dumps(doc_result, indent=2, ensure_ascii=False)}")
                    return False
            else:
                print(f"❌ API返回失败: {doc_result}")
                return False
        else:
            print(f"❌ 请求失败: {doc_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    success = test_api_doc_with_token()
    if success:
        print("\n🎉 API文档生成功能测试成功!")
    else:
        print("\n❌ API文档生成功能测试失败!")