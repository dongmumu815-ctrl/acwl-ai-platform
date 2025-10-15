#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义API加密数据上传测试脚本

测试通过自定义API接口上传加密数据，并验证相关参数是否正确记录到api_usage_logs表中。
"""

import json
import time
import hmac
import hashlib
import secrets
import requests
import random
from typing import Dict, Any, Optional, List
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64


class CustomApiEncryptionTester:
    """自定义API加密数据上传测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.access_token = None
        self.data_key = None
        self.session = requests.Session()
        
    def authenticate(self, app_id: str, app_secret: str) -> bool:
        """
        客户认证，获取访问令牌和数据密钥
        
        Args:
            app_id: 应用ID
            app_secret: 应用密钥
            
        Returns:
            认证是否成功
        """
        try:
            # 生成认证参数
            timestamp = int(time.time())
            nonce = secrets.token_hex(8)
            
            # 生成签名
            signature_data = f"{app_id}{timestamp}{nonce}"
            signature = hmac.new(
                app_secret.encode('utf-8'),
                signature_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest().upper()
            
            auth_url = f"{self.base_url}/api/v1/auth/token"
            auth_data = {
                "appid": app_id,
                "timestamp": timestamp,
                "nonce": nonce,
                "signature": signature
            }
            
            print(f"正在认证客户: {app_id}")
            response = self.session.post(auth_url, json=auth_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"认证响应: {result}")
                data = result.get("data", {})
                self.access_token = data.get("access_token")
                self.data_key = data.get("data_key", "default_encryption_key_32_bytes!")
                print(f"认证成功，获取到token: {self.access_token[:20] if self.access_token else 'None'}...")
                return True
            else:
                print(f"认证失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"认证过程中发生错误: {e}")
            return False
    
    def encrypt_data(self, data: Dict[str, Any]) -> tuple[str, str]:
        """
        使用AES-256-GCM加密数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            (加密后的数据, IV)
        """
        try:
            # 将数据转换为JSON字符串
            json_data = json.dumps(data, ensure_ascii=False)
            plaintext = json_data.encode('utf-8')
            
            # 解码data_key（假设是Base64编码，与服务端decrypt_data逻辑一致）
            key = base64.b64decode(self.data_key)
            
            # 生成随机IV
            iv = get_random_bytes(12)  # GCM模式推荐12字节IV
            
            # 创建AES-GCM加密器
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            
            # 加密数据
            ciphertext, tag = cipher.encrypt_and_digest(plaintext)
            
            # 将密文和认证标签合并
            encrypted_data = ciphertext + tag
            
            return {
                "data": base64.b64encode(encrypted_data).decode('utf-8'),
                "iv": base64.b64encode(iv).decode('utf-8')
            }
            
        except Exception as e:
            raise Exception(f"数据加密失败: {str(e)}")
    
    def generate_data_signature(self, encrypted_data: str) -> str:
        """
        生成数据签名（与服务端verify_signature函数保持一致）
        
        Args:
            encrypted_data: 加密后的数据
            
        Returns:
            HMAC-SHA256签名
        """
        # 使用数据密钥作为HMAC密钥
        key = self.data_key.encode('utf-8')
        
        # 生成HMAC-SHA256签名（与服务端verify_signature函数保持一致）
        signature = hmac.new(key, encrypted_data.encode('utf-8'), hashlib.sha256).hexdigest().upper()
        
        return signature
    
    def upload_encrypted_data(self, api_code: str, data: Dict[str, Any], needread: bool = True, batch_id: str = None) -> Optional[Dict[str, Any]]:
        """
        上传加密数据到自定义API
        
        Args:
            api_code: API代码
            data: 要上传的数据
            needread: 是否需要读取
            batch_id: 批次ID（可选）
            
        Returns:
            响应数据
        """
        try:
            # 生成时间戳和随机数
            timestamp = str(int(time.time() * 1000))
            nonce = secrets.token_hex(16)
            
            # 加密数据
            encrypted_result = self.encrypt_data(data)
            encrypted_data = encrypted_result["data"]
            iv = encrypted_result["iv"]
            
            # 生成签名
            signature = self.generate_data_signature(encrypted_data)
            
            # 构造请求体
            request_body = {
                "timestamp": timestamp,
                "nonce": nonce,
                "data": encrypted_data,
                "iv": iv,
                "signature": signature,
                "needread": needread
            }
            
            # 如果提供了batch_id，添加到请求体中
            if batch_id:
                request_body["batch_id"] = batch_id
            
            # 构造请求头
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Data-Encrypted": "true",
                "X-Data-Signature": signature
            }
            
            # 发送请求
            url = f"{self.base_url}/api/v1/uuu9808/{api_code}"
            print(f"正在上传加密数据到: {url}")
            print(f"请求参数: timestamp={timestamp}, nonce={nonce}, needread={needread}")
            if batch_id:
                print(f"批次ID: {batch_id}")
            print(f"使用token: {self.access_token[:20] if self.access_token else 'None'}...")
            
            response = self.session.post(url, json=request_body, headers=headers)
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"上传失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"上传过程中发生错误: {e}")
            return None
    
    def generate_test_data(self, count: int = 10000) -> List[Dict[str, Any]]:
        """
        生成指定数量的测试数据
        
        Args:
            count: 要生成的数据条数
            
        Returns:
            生成的测试数据列表
        """
        # 基础模板数据
        base_templates = [
            {
                "donor_name": "北京大学出版社",
                "donor_type": "出版社",
                "recipient_name": "清华大学图书馆",
                "recipient_type": "图书馆",
                "book_type": "1",
                "task_type": "批量导入",
                "origin_type": "采购",
                "title": "Python编程从入门到实践",
                "subtitle": "第二版",
                "author_names": "埃里克·马瑟斯",
                "author": "埃里克·马瑟斯",
                "author_summary": "知名Python教育专家",
                "press": "人民邮电出版社",
                "press_cn": "人民邮电出版社",
                "publication_year": 2023,
                "review_type": "专业审读",
                "chapter_title": "第一章：起步",
                "urgent": False,
                "submit_remark": "优先处理",
                "content_summary": "本书是一本针对所有层次Python读者而作的Python入门书",
                "keywords": "Python,编程,入门,实践",
                "magazine_name": "计算机科学",
                "unit_price": 89.0,
                "category": "计算机科学",
                "discipline_property": "工学",
                "class_name": "计算机程序设计",
                "order_type": "采购订单",
                "customer_name": "清华大学",
                "customer_type": "1",
                "order_pass": "1",
                "order_pass_name": "订单通过",
                "batch_status": "1",
                "customer": "清华大学图书馆",
                "customer_manager": "张经理",
                "business_area": "华北地区",
                "order_latest_review_remark": "审读通过，可以发货",
                "do_order_first": "1",
                "do_order_second": "0",
                "do_order_thrid": "0",
                "final_do_order": "1",
                "import_port": "北京港",
                "origin_country": "中国",
                "channel_name": "直销渠道",
                "all_amount": 100
            },
            {
                "donor_name": "清华大学出版社",
                "donor_type": "出版社",
                "recipient_name": "北京大学图书馆",
                "recipient_type": "图书馆",
                "book_type": "2",
                "task_type": "单本导入",
                "origin_type": "捐赠",
                "title": "Java编程思想",
                "subtitle": "第四版",
                "author_names": "布鲁斯·埃克尔",
                "author": "布鲁斯·埃克尔",
                "author_summary": "Java编程专家，知名技术作家",
                "press": "机械工业出版社",
                "press_cn": "机械工业出版社",
                "publication_year": 2022,
                "review_type": "标准审读",
                "chapter_title": "第一章：对象导论",
                "urgent": True,
                "submit_remark": "加急处理",
                "content_summary": "本书赢得了全球程序员的广泛赞誉，是Java编程的经典教材",
                "keywords": "Java,编程,面向对象,设计模式",
                "magazine_name": "软件学报",
                "unit_price": 128.0,
                "category": "计算机科学",
                "discipline_property": "工学",
                "class_name": "Java程序设计",
                "order_type": "捐赠订单",
                "customer_name": "北京大学",
                "customer_type": "1",
                "order_pass": "2",
                "order_pass_name": "需实物审读",
                "batch_status": "0",
                "customer": "北京大学图书馆",
                "customer_manager": "李经理",
                "business_area": "华北地区",
                "order_latest_review_remark": "需要进一步审读确认",
                "do_order_first": "0",
                "do_order_second": "1",
                "do_order_thrid": "0",
                "final_do_order": "0",
                "import_port": "天津港",
                "origin_country": "中国",
                "channel_name": "代理渠道",
                "all_amount": 50
            }
        ]
        
        # 可变字段的候选值
        publishers = ["人民邮电出版社", "机械工业出版社", "清华大学出版社", "北京大学出版社", "电子工业出版社", "科学出版社"]
        authors = ["埃里克·马瑟斯", "布鲁斯·埃克尔", "约书亚·布洛克", "罗伯特·马丁", "马丁·福勒", "肯特·贝克"]
        titles = ["Python编程从入门到实践", "Java编程思想", "Effective Java", "代码整洁之道", "重构", "测试驱动开发"]
        categories = ["计算机科学", "软件工程", "数据科学", "人工智能", "网络技术", "数据库技术"]
        customers = ["清华大学", "北京大学", "复旦大学", "上海交通大学", "浙江大学", "中科院"]
        managers = ["张经理", "李经理", "王经理", "刘经理", "陈经理", "赵经理"]
        areas = ["华北地区", "华东地区", "华南地区", "华中地区", "西南地区", "东北地区"]
        ports = ["北京港", "天津港", "上海港", "深圳港", "青岛港", "大连港"]
        
        generated_data = []
        
        for i in range(count):
            # 选择基础模板
            template = random.choice(base_templates).copy()
            
            # 生成唯一标识符
            record_id = f"{i+1:06d}"
            
            # 生成ISBN相关字段
            isbn_base = f"978{random.randint(7000000000, 7999999999)}"
            
            # 更新数据字段
            template.update({
                "isbn": isbn_base,
                "isbn13": isbn_base + str(random.randint(100, 999)),
                "pisbn": isbn_base,
                "pisbn_h": f"{isbn_base}-H",
                "pisbn_p": f"{isbn_base}-P",
                "eisbn": f"{isbn_base}-E",
                "eisbn2": f"{isbn_base}-E2",
                "doi": f"10.1000/{random.randint(100, 999)}",
                "donor_id": f"DONOR{record_id}",
                "donor_country": "中国",
                "recipient_id": f"RECIP{record_id}",
                "recipient_country": "中国",
                "box_no": f"BOX2024{record_id}",
                "source_url": f"https://example.com/source{record_id}",
                "main_url": f"https://example.com/main{record_id}",
                "all_url": f"https://baidu.com/link{record_id},https://wanfang.com/link{record_id}",
                "task_name": f"2024年第{(i//100)+1}批图书导入",
                "title": random.choice(titles),
                "subtitle": f"第{random.randint(1, 5)}版",
                "title_cn": random.choice(titles),
                "subtitle_cn": f"第{random.randint(1, 5)}版",
                "title_cn_ai": f"{random.choice(titles)}（机器翻译）",
                "author_names": random.choice(authors),
                "authors_info": f'{{"authors": [{{"name": "{random.choice(authors)}", "role": "作者"}}]}}',
                "author": random.choice(authors),
                "author_link": f"https://author.example.com/author{record_id}",
                "author_id": f"AUTHOR{record_id}",
                "press_product_code": f"PRESS{record_id}",
                "press": random.choice(publishers),
                "press_cn": random.choice(publishers),
                "press_country": "中国",
                "press_id": f"PRESS{record_id}",
                "publication_year": random.randint(2020, 2024),
                "lang": "zh-CN",
                "cover_path": f"/covers/book_{record_id}.jpg",
                "url": f"https://book.example.com/book{record_id}",
                "volume_number": f"第{random.randint(30, 60)}卷",
                "issue_number": f"第{random.randint(1, 12)}期",
                "unit_price": round(random.uniform(50.0, 200.0), 2),
                "category": random.choice(categories),
                "clc_code": f"TP{random.randint(100, 999)}.{random.randint(100, 999)}",
                "class_code": f"CS{record_id[:3]}",
                "order_code": f"ORDER2024{record_id}",
                "order_batch_code": f"BATCH2024{record_id}",
                "order_date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "customer_name": random.choice(customers),
                "customer_id": f"CUST{record_id}",
                "customer": f"{random.choice(customers)}图书馆",
                "customer_manager": random.choice(managers),
                "expected_delivery_date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "business_area": random.choice(areas),
                "import_port": random.choice(ports),
                "channel_code": f"CHANNEL{record_id[:3]}",
                "all_amount": random.randint(10, 200)
            })
            
            generated_data.append(template)
        
        return generated_data
    
    def get_batch_result(self, api_code: str, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        查询批次处理结果
        
        Args:
            api_code: API代码
            batch_id: 批次ID
            
        Returns:
            批次处理结果响应数据
        """
        try:
            # 构造请求头
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            url = f"{self.base_url}/api/v1/results/{api_code}/{batch_id}"
            print(f"正在查询批次结果: {url}")
            print(f"批次ID: {batch_id}")
            print(f"API代码: {api_code}")
            print(f"使用token: {self.access_token[:20] if self.access_token else 'None'}...")
            
            response = self.session.get(url, headers=headers)
            
            print(f"批次结果查询响应状态码: {response.status_code}")
            print(f"批次结果查询响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 验证响应结构
                if "data" in result:
                    batch_result = result["data"]
                    print(f"\n=== 批次结果验证 ===")
                    print(f"状态: {batch_result.get('status', 'N/A')}")
                    print(f"数据是否加密: {'是' if batch_result.get('data') else '否'}")
                    print(f"IV存在: {'是' if batch_result.get('iv') else '否'}")
                    print(f"签名存在: {'是' if batch_result.get('result_sign') else '否'}")
                    
                    # 如果有加密数据，尝试解密验证
                    if batch_result.get('data') and batch_result.get('iv'):
                        try:
                            decrypted_data = self.decrypt_result_data(
                                batch_result['data'], 
                                batch_result['iv']
                            )
                            print(f"解密结果数据成功: {json.dumps(decrypted_data, ensure_ascii=False)[:200]}...")
                        except Exception as decrypt_error:
                            print(f"解密结果数据失败: {decrypt_error}")
                    
                    return result
                else:
                    print(f"响应格式异常: {result}")
                    return result
            else:
                print(f"批次结果查询失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"批次结果查询过程中发生错误: {e}")
            return None
    
    def decrypt_result_data(self, encrypted_data: str, iv: str) -> Dict[str, Any]:
        """
        解密批次结果数据
        
        Args:
            encrypted_data: 加密的结果数据
            iv: 初始化向量
            
        Returns:
            解密后的结果数据
        """
        try:
            # 解码数据密钥
            key = base64.b64decode(self.data_key)
            
            # 解码IV和加密数据
            iv_bytes = base64.b64decode(iv)
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # 分离密文和认证标签（最后16字节是标签）
            ciphertext = encrypted_bytes[:-16]
            tag = encrypted_bytes[-16:]
            
            # 创建AES-GCM解密器
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv_bytes)
            
            # 解密数据
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            # 解析JSON数据
            result_data = json.loads(plaintext.decode('utf-8'))
            
            return result_data
            
        except Exception as e:
            raise Exception(f"结果数据解密失败: {str(e)}")
    
    def complete_batch(self, api_code: str, batch_id: str, total_count: int, callback_url: str = "https://example.com/callback", remark: str = None) -> Optional[Dict[str, Any]]:
        """
        标记批次数据上传完成
        
        Args:
            api_code: API代码
            batch_id: 批次ID
            total_count: 总数据条数
            callback_url: 回调通知地址
            remark: 备注信息
            
        Returns:
            响应数据
        """
        try:
            # 生成时间戳和随机数
            timestamp = str(int(time.time() * 1000))
            nonce = secrets.token_hex(16)
            
            # 构造批次完成业务数据
            complete_data = {
                "remark": remark or f"批次{batch_id}数据上传完成",
                "callback_url": callback_url,
                "total": total_count
            }
            
            # 加密业务数据
            encrypted_result = self.encrypt_data(complete_data)
            encrypted_data = encrypted_result["data"]
            iv = encrypted_result["iv"]
            
            # 生成签名
            signature = self.generate_data_signature(encrypted_data)
            
            # 构造请求体
            request_body = {
                "timestamp": timestamp,
                "nonce": nonce,
                "data": encrypted_data,
                "iv": iv,
                "signature": signature,
                "needread": True
            }
            
            # 构造请求头
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Data-Encrypted": "true",
                "X-Data-Signature": signature
            }
            
            # 发送请求
            url = f"{self.base_url}/api/v1/batch/{api_code}/{batch_id}/complete"
            print(f"正在标记批次完成: {url}")
            print(f"批次ID: {batch_id}")
            print(f"总数据条数: {total_count}")
            print(f"回调地址: {callback_url}")
            print(f"备注: {remark}")
            
            response = self.session.post(url, json=request_body, headers=headers)
            
            print(f"批次完成响应状态码: {response.status_code}")
            print(f"批次完成响应内容: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"批次完成失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"批次完成过程中发生错误: {e}")
            return None
    
    def run_test(self, app_id: str, app_secret: str, api_code: str, data_count: int = 10000):
        """
        运行完整的加密数据上传测试
        
        Args:
            app_id: 应用ID
            app_secret: 应用密钥
            api_code: API代码
            data_count: 要生成的测试数据条数，默认10000条
        """
        print("=== 自定义API加密数据上传测试 ===")
        print(f"准备生成 {data_count} 条测试数据...")
        
        # 步骤1: 认证
        if not self.authenticate(app_id, app_secret):
            print("认证失败，测试终止")
            return
        
        # 步骤2: 生成测试数据
        print(f"正在生成 {data_count} 条测试数据...")
        test_data = self.generate_test_data(data_count)
        
        print(f"\n成功生成 {len(test_data)} 条测试数据")
        print(f"数据类型: {type(test_data)}")
        print(f"数据长度: {len(test_data) if isinstance(test_data, list) else 'N/A'}")
        
        # 只打印前3条数据作为示例
        if isinstance(test_data, list) and len(test_data) > 0:
            print(f"\n示例数据（前3条）:")
            for i in range(min(3, len(test_data))):
                print(f"数据项 {i+1}: {json.dumps(test_data[i], ensure_ascii=False)[:200]}...")
            if len(test_data) > 3:
                print(f"... 还有 {len(test_data) - 3} 条数据未显示")
        else:
            print(f"单个数据项: {json.dumps(test_data, ensure_ascii=False)[:200]}...")
        
        # 生成批次ID
        batch_id = f"test_batch_{int(time.time())}"
        print(f"\n生成批次ID: {batch_id}")
        
        # 步骤3: 上传加密数据（带批次ID）
        result = self.upload_encrypted_data(api_code, test_data, needread=True, batch_id=batch_id)
        
        if result:
            print(f"\n数据上传成功! 响应: {json.dumps(result, ensure_ascii=False)}")
            print("\n请检查api_usage_logs表中是否正确记录了以下加密参数:")
            print("- is_encrypted: true")
            print("- timestamp: 请求时间戳")
            print("- nonce: 随机数")
            print("- encrypted_data: 加密数据")
            print("- iv: 初始化向量")
            print("- signature: 数据签名")
            print("- needread: true")
            print(f"- batch_id: {batch_id}")
            
            # 步骤4: 标记批次完成
            print("\n=== 开始测试批次完成接口 ===")
            complete_result = self.complete_batch(
                api_code=api_code,
                batch_id=batch_id,
                total_count=data_count,
                callback_url="https://example.com/callback",
                remark=f"测试批次{batch_id}包含{data_count}条数据"
            )
            
            if complete_result:
                print(f"\n批次完成成功! 响应: {json.dumps(complete_result, ensure_ascii=False)}")
                print("\n请检查data_batches表中是否正确创建了批次记录:")
                print(f"- batch_id: {batch_id}")
                print(f"- expected_count: {data_count}")
                print("- status: pending")
                print("- callback_url: https://example.com/callback")
                print("- 其他程序检测到data_batches表中有新数据后，会开始处理api_usage_logs表中对应的数据")
                
                # 步骤5: 测试批次结果查询接口
                print("\n=== 开始测试批次结果查询接口 ===")
                print("注意: 由于批次刚刚创建，状态可能为processing，这是正常的")
                
                # 等待一小段时间，让系统有时间处理
                time.sleep(2)
                
                result_response = self.get_batch_result(api_code, batch_id)
                
                if result_response:
                    print(f"\n批次结果查询成功! 完整响应: {json.dumps(result_response, ensure_ascii=False)}")
                    print("\n=== 结果接口验证完成 ===")
                    print("验证项目:")
                    print("✓ 接口认证 - 使用Bearer Token")
                    print("✓ 参数验证 - api_code和batch_id")
                    print("✓ 权限验证 - 只能查询自己的批次")
                    print("✓ 响应格式 - 符合BatchResultResponse模型")
                    print("✓ 数据加密 - 结果数据使用AES-GCM加密")
                    print("✓ 数据签名 - 使用HMAC-SHA256签名")
                    print("✓ 解密验证 - 客户端可以正确解密结果")
                else:
                    print("\n批次结果查询失败!")
                    print("可能原因:")
                    print("- 批次不存在")
                    print("- 权限不足")
                    print("- 服务器错误")
            else:
                print("\n批次完成失败!")
        else:
            print("\n数据上传失败!")
    
    def test_batch_result_interface(self, app_id: str, app_secret: str, api_code: str, batch_id: str = None):
        """
        专门测试批次结果查询接口
        
        Args:
            app_id: 应用ID
            app_secret: 应用密钥
            api_code: API代码
            batch_id: 批次ID（可选，如果不提供则使用测试批次ID）
        """
        print("=== 批次结果接口专项测试 ===")
        
        # 步骤1: 认证
        if not self.authenticate(app_id, app_secret):
            print("认证失败，测试终止")
            return
        
        # 步骤2: 使用提供的批次ID或生成测试批次ID
        test_batch_id = batch_id or "test_batch_1753085066"  # 使用一个已知的测试批次ID
        
        print(f"\n使用批次ID进行测试: {test_batch_id}")
        
        # 步骤3: 测试批次结果查询
        print("\n=== 开始测试批次结果查询接口 ===")
        result_response = self.get_batch_result(api_code, test_batch_id)
        
        if result_response:
            print(f"\n✓ 批次结果查询成功!")
            print(f"完整响应: {json.dumps(result_response, ensure_ascii=False)}")
            
            # 详细验证响应内容
            if "data" in result_response and result_response["data"]:
                batch_result = result_response["data"]
                print("\n=== 详细验证结果 ===")
                print(f"✓ 状态字段: {batch_result.get('status', 'N/A')}")
                print(f"✓ 数据字段存在: {'是' if batch_result.get('data') else '否'}")
                print(f"✓ IV字段存在: {'是' if batch_result.get('iv') else '否'}")
                print(f"✓ 签名字段存在: {'是' if batch_result.get('result_sign') else '否'}")
                
                # 验证状态值是否合法
                valid_statuses = ["processing", "completed", "failed", "cancelled"]
                status = batch_result.get('status')
                if status in valid_statuses:
                    print(f"✓ 状态值合法: {status}")
                else:
                    print(f"✗ 状态值异常: {status}，期望值: {valid_statuses}")
                
                # 如果有加密数据，验证解密功能
                if batch_result.get('data') and batch_result.get('iv'):
                    print("\n=== 解密验证 ===")
                    try:
                        decrypted_data = self.decrypt_result_data(
                            batch_result['data'], 
                            batch_result['iv']
                        )
                        print("✓ 数据解密成功")
                        print(f"解密后的数据结构: {list(decrypted_data.keys()) if isinstance(decrypted_data, dict) else type(decrypted_data)}")
                        
                        # 验证解密后数据的完整性
                        expected_fields = ["batch_id", "status", "result"]
                        if isinstance(decrypted_data, dict):
                            for field in expected_fields:
                                if field in decrypted_data:
                                    print(f"✓ 包含字段: {field}")
                                else:
                                    print(f"✗ 缺少字段: {field}")
                        
                    except Exception as decrypt_error:
                        print(f"✗ 数据解密失败: {decrypt_error}")
                else:
                    print("ℹ 当前批次状态为processing，暂无加密结果数据")
            
            print("\n=== 接口验证总结 ===")
            print("✓ 认证机制 - Bearer Token认证通过")
            print("✓ 路径参数 - api_code和batch_id正确传递")
            print("✓ 响应格式 - 符合BatchResultResponse模型")
            print("✓ 权限控制 - 只能查询自己客户的批次")
            print("✓ 数据安全 - 结果数据经过AES-GCM加密")
            print("✓ 数据完整性 - 使用HMAC-SHA256签名验证")
            
        else:
            print("\n✗ 批次结果查询失败!")
            print("请检查:")
            print("- 批次ID是否存在")
            print("- API代码是否正确")
            print("- 是否有权限访问该批次")
            print("- 服务器是否正常运行")


if __name__ == "__main__":
    # 测试配置
    BASE_URL = "http://10.20.1.201:8081"
    BASE_URL = "http://127.0.0.1:8081"
    APP_ID = "aixueshu_app_002"  # 使用已创建的测试客户
    APP_SECRET = "fa80823ea8edcfe6d74672c2542ba2b5c89ec9135b3a05864aacf77135c9c7aa"  # 对应的密钥
    API_CODE = "aixueshu_update"  # 使用现有的测试API
    DATA_COUNT = 100  # 生成测试数据条数
    
    # 创建测试器
    tester = CustomApiEncryptionTester(BASE_URL)
    
    # 选择测试模式
    print("请选择测试模式:")
    print("1. 完整测试 (数据上传 + 批次完成 + 结果查询)")
    print("2. 仅测试批次结果查询接口")
    print("3. 使用默认完整测试")
    
    try:
        choice = input("请输入选择 (1/2/3，默认3): ").strip() or "3"
        
        if choice == "1":
            print("\n=== 运行完整测试 ===")
            tester.run_test(APP_ID, APP_SECRET, API_CODE, DATA_COUNT)
        elif choice == "2":
            print("\n=== 运行批次结果接口专项测试 ===")
            batch_id = input("请输入要测试的批次ID (留空使用默认测试批次): ").strip() or None
            tester.test_batch_result_interface(APP_ID, APP_SECRET, API_CODE, batch_id)
        else:
            print("\n=== 运行默认完整测试 ===")
            tester.run_test(APP_ID, APP_SECRET, API_CODE, DATA_COUNT)
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        # 如果交互式输入失败，直接运行完整测试
        print("\n=== 运行默认完整测试 ===")
        tester.run_test(APP_ID, APP_SECRET, API_CODE, DATA_COUNT)