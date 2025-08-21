#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据插入脚本
用于向ACWL-AI数据库插入基础测试数据
"""

import pymysql
import sys
import os
import time
import argparse
from pathlib import Path
from typing import Optional

# 导入本地配置
try:
    from db_config import db_config as settings
except ImportError:
    # 如果无法导入本地配置，尝试导入项目配置
    project_root = Path(__file__).parent.parent
    sys.path.append(str(project_root))
    sys.path.append(str(project_root / "backend"))
    
    try:
        from app.core.config import settings
    except ImportError:
        # 最后使用默认配置
        class DefaultSettings:
            DB_HOST = "10.20.1.200"
            DB_PORT = 3306
            DB_USER = "root"
            DB_PASSWORD = "2wsx1QAZaczt"
            DB_NAME = "acwl-ai"
            DB_CHARSET = "utf8mb4"
        
        settings = DefaultSettings()
        print("⚠️  无法导入配置文件，使用默认数据库配置")

def connect_database():
    """连接数据库"""
    try:
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset=settings.DB_CHARSET,
            autocommit=False
        )
        print(f"✅ 成功连接到数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        return connection
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def execute_sql_file(connection, sql_file_path):
    """执行SQL文件"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # 分割SQL语句（以分号分隔）
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        cursor = connection.cursor()
        
        for i, statement in enumerate(sql_statements):
            if statement.upper().startswith('SELECT'):
                # 执行查询语句并显示结果
                cursor.execute(statement)
                results = cursor.fetchall()
                if results:
                    print("\n📊 执行结果:")
                    for row in results:
                        print(f"  {row}")
            else:
                # 执行其他语句
                cursor.execute(statement)
                if cursor.rowcount > 0:
                    print(f"✅ 执行语句 {i+1}: 影响 {cursor.rowcount} 行")
        
        connection.commit()
        cursor.close()
        print("\n🎉 测试数据插入完成！")
        return True
        
    except Exception as e:
        print(f"❌ 执行SQL文件失败: {e}")
        connection.rollback()
        return False

def check_tables_exist(connection):
    """检查表是否存在"""
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        
        required_tables = [
            'acwl_users', 'acwl_models', 'acwl_deployments', 'acwl_servers',
            'acwl_gpu_resources', 'acwl_datasets', 'acwl_fine_tuning_jobs',
            'acwl_prompt_templates', 'acwl_knowledge_bases', 'acwl_api_keys'
        ]
        
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"⚠️  缺少以下表: {', '.join(missing_tables)}")
            print("请先执行 schema.sql 创建数据库表结构")
            return False
        else:
            print(f"✅ 数据库表结构检查通过，共找到 {len(tables)} 个表")
            return True
            
    except Exception as e:
        print(f"❌ 检查表结构失败: {e}")
        return False

def clear_existing_data(connection):
    """清空现有测试数据（可选）"""
    try:
        cursor = connection.cursor()
        
        # 按依赖关系顺序删除数据
        tables_to_clear = [
            'acwl_usage_logs',
            'acwl_deployment_metrics',
            'acwl_deployment_gpus',
            'acwl_deployment_resources',
            'acwl_model_evaluations',
            'acwl_knowledge_documents',
            'acwl_fine_tuning_jobs',
            'acwl_deployments',
            'acwl_agents',
            'acwl_api_keys',
            'acwl_workflows',
            'acwl_scripts',
            'acwl_prompt_templates',
            'acwl_knowledge_bases',
            'acwl_datasets',
            'acwl_gpu_resources',
            'acwl_deployment_templates',
            'acwl_servers',
            'acwl_models',
            'acwl_users',
            'acwl_system_settings',
            'acwl_resources'
        ]
        
        # 禁用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"🧹 清空表: {table}")
            except Exception as e:
                print(f"⚠️  清空表 {table} 失败: {e}")
        
        # 重新启用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        connection.commit()
        cursor.close()
        print("✅ 现有数据清理完成")
        return True
        
    except Exception as e:
        print(f"❌ 清理数据失败: {e}")
        connection.rollback()
        return False

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='ACWL-AI 测试数据插入工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python insert_test_data.py                    # 交互式插入
  python insert_test_data.py --clear            # 清空现有数据后插入
  python insert_test_data.py --force            # 强制插入，不询问确认
  python insert_test_data.py --check-only       # 仅检查数据库连接和表结构
  python insert_test_data.py --sql-file custom.sql  # 使用自定义SQL文件
        """
    )
    
    parser.add_argument(
        '--clear', 
        action='store_true',
        help='清空现有测试数据后插入新数据'
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='强制执行，不询问用户确认'
    )
    
    parser.add_argument(
        '--check-only', 
        action='store_true',
        help='仅检查数据库连接和表结构，不插入数据'
    )
    
    parser.add_argument(
        '--sql-file', 
        type=str,
        help='指定自定义SQL文件路径'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )
    
    return parser.parse_args()

def show_database_info(connection):
    """显示数据库信息"""
    try:
        cursor = connection.cursor()
        
        # 显示数据库版本
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"📊 数据库版本: {version}")
        
        # 显示当前数据库
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()[0]
        print(f"📊 当前数据库: {current_db}")
        
        # 显示表数量
        cursor.execute("SHOW TABLES")
        table_count = len(cursor.fetchall())
        print(f"📊 表数量: {table_count}")
        
        cursor.close()
        
    except Exception as e:
        print(f"⚠️  获取数据库信息失败: {e}")

def validate_sql_file(sql_file_path: Path) -> bool:
    """验证SQL文件"""
    if not sql_file_path.exists():
        print(f"❌ SQL文件不存在: {sql_file_path}")
        return False
    
    if sql_file_path.stat().st_size == 0:
        print(f"❌ SQL文件为空: {sql_file_path}")
        return False
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            if 'INSERT INTO' not in content.upper():
                print(f"⚠️  SQL文件中未找到INSERT语句: {sql_file_path}")
                return False
    except Exception as e:
        print(f"❌ 读取SQL文件失败: {e}")
        return False
    
    print(f"✅ SQL文件验证通过: {sql_file_path}")
    return True

def main():
    """主函数"""
    args = parse_arguments()
    
    print("🚀 ACWL-AI 测试数据插入工具")
    print("=" * 50)
    
    # 显示配置信息
    if hasattr(settings, 'display_config'):
        settings.display_config()
    else:
        print(f"📋 数据库配置: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    
    # 确定SQL文件路径
    if args.sql_file:
        sql_file_path = Path(args.sql_file)
    else:
        sql_file_path = Path(__file__).parent / "test_data.sql"
    
    # 验证SQL文件
    if not validate_sql_file(sql_file_path):
        return False
    
    # 连接数据库
    print("\n🔌 正在连接数据库...")
    connection = connect_database()
    if not connection:
        return False
    
    try:
        # 显示数据库信息
        if args.verbose:
            show_database_info(connection)
        
        # 检查表结构
        print("\n🔍 检查数据库表结构...")
        if not check_tables_exist(connection):
            return False
        
        # 如果只是检查，则退出
        if args.check_only:
            print("\n✅ 数据库连接和表结构检查完成")
            return True
        
        # 处理数据清理
        should_clear = args.clear
        if not args.force and not args.clear:
            clear_data = input("\n是否清空现有测试数据？(y/N): ").lower().strip()
            should_clear = clear_data in ['y', 'yes']
        
        if should_clear:
            print("\n🧹 清空现有数据...")
            if not clear_existing_data(connection):
                return False
        
        # 确认插入操作
        if not args.force:
            confirm = input("\n确认插入测试数据？(Y/n): ").lower().strip()
            if confirm in ['n', 'no']:
                print("❌ 操作已取消")
                return False
        
        # 执行测试数据插入
        print("\n📥 开始插入测试数据...")
        start_time = time.time()
        
        success = execute_sql_file(connection, sql_file_path)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            print(f"\n🎊 测试数据插入成功！耗时: {duration:.2f}秒")
            print("\n📋 默认测试账号:")
            print("  管理员: admin@acwl.ai / password")
            print("  开发者: dev@acwl.ai / password")
            print("  研究员: research@acwl.ai / password")
            print("  测试员: test@acwl.ai / password")
            print("\n🔑 API密钥已创建，可在数据库中查看")
            print("\n💡 提示: 生产环境请务必修改默认密码和API密钥")
            return True
        else:
            print(f"\n❌ 测试数据插入失败！耗时: {duration:.2f}秒")
            return False
            
    finally:
        connection.close()
        print("\n🔌 数据库连接已关闭")

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        sys.exit(1)