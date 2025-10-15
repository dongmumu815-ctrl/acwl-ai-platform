#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置 acwl_api_system 数据库

创建数据库、表结构和示例数据
"""

import asyncio
import aiomysql
import sys
from datetime import datetime

async def setup_api_system_database():
    """设置 acwl_api_system 数据库"""
    
    print("🚀 开始设置 acwl_api_system 数据库")
    print("=" * 50)
    
    # 数据库连接配置
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '2wsx1QAZaczt',
        'charset': 'utf8mb4'
    }
    
    try:
        # 连接到MySQL服务器（不指定数据库）
        print("📡 连接到MySQL服务器...")
        connection = await aiomysql.connect(**config)
        cursor = await connection.cursor()
        
        # 创建数据库
        print("🗄️ 创建 acwl_api_system 数据库...")
        await cursor.execute("CREATE DATABASE IF NOT EXISTS acwl_api_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ 数据库创建成功")
        
        # 选择数据库
        await cursor.execute("USE acwl_api_system")
        
        # 创建客户表
        print("📋 创建 customers 表...")
        customers_sql = """
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL COMMENT '客户名称',
            email VARCHAR(255) NOT NULL UNIQUE COMMENT '邮箱地址',
            phone VARCHAR(20) COMMENT '电话号码',
            company VARCHAR(200) COMMENT '公司名称',
            app_id VARCHAR(32) NOT NULL UNIQUE COMMENT '应用ID',
            app_secret VARCHAR(64) NOT NULL COMMENT '应用密钥',
            rate_limit INT DEFAULT 100 COMMENT '每分钟调用限制',
            max_apis INT DEFAULT 10 COMMENT '最大API数量',
            total_api_calls INT DEFAULT 0 COMMENT '总调用次数',
            last_api_call_at DATETIME COMMENT '最后调用时间',
            is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户表'
        """
        await cursor.execute(customers_sql)
        print("✅ customers 表创建成功")
        
        # 创建自定义API表
        print("📋 创建 custom_apis 表...")
        apis_sql = """
        CREATE TABLE IF NOT EXISTS custom_apis (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL COMMENT '客户ID',
            api_name VARCHAR(100) NOT NULL COMMENT 'API名称',
            api_code VARCHAR(50) NOT NULL COMMENT 'API代码',
            description TEXT COMMENT 'API描述',
            endpoint_url VARCHAR(255) NOT NULL COMMENT '接口地址',
            http_method VARCHAR(10) DEFAULT 'POST' COMMENT 'HTTP方法',
            request_format VARCHAR(20) DEFAULT 'json' COMMENT '请求格式',
            response_format VARCHAR(20) DEFAULT 'json' COMMENT '响应格式',
            is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
            total_calls INT DEFAULT 0 COMMENT '总调用次数',
            last_called_at DATETIME COMMENT '最后调用时间',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自定义API表'
        """
        await cursor.execute(apis_sql)
        print("✅ custom_apis 表创建成功")
        
        # 创建数据批次表
        print("📋 创建 data_batches 表...")
        batches_sql = """
        CREATE TABLE IF NOT EXISTS data_batches (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL COMMENT '客户ID',
            batch_name VARCHAR(100) NOT NULL COMMENT '批次名称',
            description TEXT COMMENT '批次描述',
            status VARCHAR(20) DEFAULT 'pending' COMMENT '处理状态',
            total_records INT DEFAULT 0 COMMENT '总记录数',
            processed_records INT DEFAULT 0 COMMENT '已处理记录数',
            failed_records INT DEFAULT 0 COMMENT '失败记录数',
            file_path VARCHAR(500) COMMENT '文件路径',
            result_file_path VARCHAR(500) COMMENT '结果文件路径',
            error_message TEXT COMMENT '错误信息',
            started_at DATETIME COMMENT '开始时间',
            completed_at DATETIME COMMENT '完成时间',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据批次表'
        """
        await cursor.execute(batches_sql)
        print("✅ data_batches 表创建成功")
        
        # 插入示例客户数据
        print("📊 插入示例客户数据...")
        customers_data = [
            ('ACWL科技有限公司', 'contact@acwl.tech', '021-12345678', 'ACWL科技有限公司', 'acwl_tech_001', 'secret_acwl_001', 200, 20, 5680),
            ('智能数据公司', 'info@smartdata.com', '010-87654321', '智能数据公司', 'smart_data_002', 'secret_smart_002', 150, 15, 3420),
            ('云端解决方案', 'support@cloudsol.net', '0755-11223344', '云端解决方案有限公司', 'cloud_sol_003', 'secret_cloud_003', 300, 25, 8950),
        ]
        
        for customer in customers_data:
            insert_sql = """
            INSERT INTO customers (name, email, phone, company, app_id, app_secret, rate_limit, max_apis, total_api_calls)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            name = VALUES(name), phone = VALUES(phone), company = VALUES(company)
            """
            await cursor.execute(insert_sql, customer)
        
        print("✅ 示例客户数据插入成功")
        
        # 插入示例API数据
        print("📊 插入示例API数据...")
        apis_data = [
            (1, '用户信息查询API', 'user_info_query', '根据用户ID查询用户详细信息', '/api/user/info', 'POST', 'json', 'json', 1, 2340),
            (1, '订单状态查询API', 'order_status_query', '查询订单的当前状态和物流信息', '/api/order/status', 'GET', 'json', 'json', 1, 1890),
            (2, '数据分析API', 'data_analysis', '对上传的数据进行智能分析', '/api/data/analyze', 'POST', 'json', 'json', 1, 1560),
            (3, '文件处理API', 'file_processing', '批量处理上传的文件', '/api/file/process', 'POST', 'multipart', 'json', 1, 3210),
        ]
        
        for api in apis_data:
            insert_sql = """
            INSERT INTO custom_apis (customer_id, api_name, api_code, description, endpoint_url, http_method, request_format, response_format, is_active, total_calls)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            await cursor.execute(insert_sql, api)
        
        print("✅ 示例API数据插入成功")
        
        # 插入示例批次数据
        print("📊 插入示例批次数据...")
        batches_data = [
            (1, '用户数据导入批次', '导入新用户数据到系统', 'completed', 1000, 980, 20, '/uploads/users_batch_1.csv', '/results/users_result_1.json'),
            (2, '订单数据处理批次', '处理历史订单数据', 'processing', 500, 350, 0, '/uploads/orders_batch_2.xlsx', None),
            (3, '文件转换批次', '批量转换文档格式', 'pending', 200, 0, 0, '/uploads/docs_batch_3.zip', None),
        ]
        
        for batch in batches_data:
            insert_sql = """
            INSERT INTO data_batches (customer_id, batch_name, description, status, total_records, processed_records, failed_records, file_path, result_file_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            await cursor.execute(insert_sql, batch)
        
        print("✅ 示例批次数据插入成功")
        
        # 提交事务
        await connection.commit()
        
        # 验证数据
        print("\n🔍 验证数据...")
        await cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = (await cursor.fetchone())[0]
        print(f"   客户数量: {customer_count}")
        
        await cursor.execute("SELECT COUNT(*) FROM custom_apis")
        api_count = (await cursor.fetchone())[0]
        print(f"   API数量: {api_count}")
        
        await cursor.execute("SELECT COUNT(*) FROM data_batches")
        batch_count = (await cursor.fetchone())[0]
        print(f"   批次数量: {batch_count}")
        
        # 关闭连接
        await cursor.close()
        connection.close()
        
        print("\n" + "=" * 50)
        print("🎉 acwl_api_system 数据库设置完成！")
        print("✅ 数据库已创建")
        print("✅ 表结构已创建")
        print("✅ 示例数据已插入")
        print("\n现在API管理功能应该能够从真实数据库获取数据了！")
        
        return True
        
    except Exception as e:
        print(f"❌ 设置数据库时发生错误: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(setup_api_system_database())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n设置被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n设置过程中发生错误: {e}")
        sys.exit(1)