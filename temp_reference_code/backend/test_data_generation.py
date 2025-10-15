#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据生成验证脚本

用于验证generate_test_data函数是否能正确生成指定数量的测试数据。
"""

import json
import time
from test_custom_api_encryption import CustomApiEncryptionTester


def test_data_generation():
    """
    测试数据生成功能
    """
    print("=== 测试数据生成功能 ===")
    
    # 创建测试器实例
    tester = CustomApiEncryptionTester()
    
    # 测试不同数量的数据生成
    test_counts = [10, 100, 1000, 10000]
    
    for count in test_counts:
        print(f"\n正在测试生成 {count} 条数据...")
        start_time = time.time()
        
        try:
            # 生成测试数据
            test_data = tester.generate_test_data(count)
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            # 验证数据
            if len(test_data) == count:
                print(f"✓ 成功生成 {len(test_data)} 条数据，耗时: {generation_time:.2f}秒")
                
                # 验证数据结构
                if test_data:
                    first_item = test_data[0]
                    required_fields = [
                        'isbn', 'title', 'author', 'press', 'publication_year',
                        'customer_name', 'order_code', 'batch_status'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in first_item]
                    if not missing_fields:
                        print(f"✓ 数据结构验证通过")
                        
                        # 显示第一条数据的示例
                        if count <= 100:  # 只在小数据量时显示详细信息
                            print(f"示例数据: {json.dumps(first_item, ensure_ascii=False)[:200]}...")
                    else:
                        print(f"✗ 数据结构验证失败，缺少字段: {missing_fields}")
                        
            else:
                print(f"✗ 数据生成失败，期望 {count} 条，实际生成 {len(test_data)} 条")
                
        except Exception as e:
            print(f"✗ 数据生成过程中发生错误: {e}")
    
    print("\n=== 数据生成测试完成 ===")


def test_data_uniqueness():
    """
    测试数据唯一性
    """
    print("\n=== 测试数据唯一性 ===")
    
    tester = CustomApiEncryptionTester()
    test_data = tester.generate_test_data(1000)
    
    # 检查ISBN唯一性
    isbns = [item['isbn'] for item in test_data]
    unique_isbns = set(isbns)
    
    if len(isbns) == len(unique_isbns):
        print(f"✓ ISBN唯一性验证通过，1000条数据中有 {len(unique_isbns)} 个唯一ISBN")
    else:
        print(f"✗ ISBN唯一性验证失败，1000条数据中只有 {len(unique_isbns)} 个唯一ISBN")
    
    # 检查订单号唯一性
    order_codes = [item['order_code'] for item in test_data]
    unique_order_codes = set(order_codes)
    
    if len(order_codes) == len(unique_order_codes):
        print(f"✓ 订单号唯一性验证通过，1000条数据中有 {len(unique_order_codes)} 个唯一订单号")
    else:
        print(f"✗ 订单号唯一性验证失败，1000条数据中只有 {len(unique_order_codes)} 个唯一订单号")


def test_data_variety():
    """
    测试数据多样性
    """
    print("\n=== 测试数据多样性 ===")
    
    tester = CustomApiEncryptionTester()
    test_data = tester.generate_test_data(1000)
    
    # 检查出版社多样性
    publishers = [item['press'] for item in test_data]
    unique_publishers = set(publishers)
    print(f"出版社种类: {len(unique_publishers)} 种 - {list(unique_publishers)}")
    
    # 检查作者多样性
    authors = [item['author'] for item in test_data]
    unique_authors = set(authors)
    print(f"作者种类: {len(unique_authors)} 种 - {list(unique_authors)}")
    
    # 检查客户多样性
    customers = [item['customer_name'] for item in test_data]
    unique_customers = set(customers)
    print(f"客户种类: {len(unique_customers)} 种 - {list(unique_customers)}")
    
    # 检查价格范围
    prices = [item['unit_price'] for item in test_data]
    min_price = min(prices)
    max_price = max(prices)
    print(f"价格范围: {min_price:.2f} - {max_price:.2f}")


if __name__ == "__main__":
    # 运行所有测试
    test_data_generation()
    test_data_uniqueness()
    test_data_variety()
    
    print("\n所有测试完成！")