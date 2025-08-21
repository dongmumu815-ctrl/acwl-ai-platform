import mysql.connector
import sys

def fix_database_enum_values():
    """
    直接修改数据库中的模型类型值，将旧格式改为新格式
    """
    # 数据库配置
    DB_CONFIG = {
        'host': '10.20.1.200',
        'user': 'root',
        'password': '2wsx1QAZaczt',
        'database': 'acwl-ai',
        'charset': 'utf8mb4'
    }
    
    connection = None
    cursor = None
    
    try:
        # 连接数据库
        print("正在连接数据库...")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 首先查看当前的模型类型分布
        print("\n查看当前模型类型分布:")
        cursor.execute("SELECT model_type, COUNT(*) FROM acwl_models GROUP BY model_type")
        results = cursor.fetchall()
        for model_type, count in results:
            print(f"  {model_type}: {count} 个模型")
        
        # 直接修改枚举定义为包含所有可能的值
        print("\n步骤1: 修改枚举定义...")
        alter_sql = """
        ALTER TABLE acwl_models 
        MODIFY COLUMN model_type ENUM('LLM', 'Embedding', 'Multimodal', 'Other', 'EMBEDDING', 'MULTIMODAL', 'OTHER')
        """
        try:
            cursor.execute(alter_sql)
            print("✓ 枚举定义已修改")
        except mysql.connector.Error as e:
            if "duplicated value" in str(e):
                print("⚠️ 枚举值已存在，跳过枚举修改步骤")
            else:
                raise e
        
        # 更新数据
        print("\n步骤2: 更新模型类型值...")
        
        # 更新 Embedding -> EMBEDDING
        cursor.execute("UPDATE acwl_models SET model_type = 'EMBEDDING' WHERE model_type = 'Embedding'")
        embedding_updated = cursor.rowcount
        print(f"✓ 更新了 {embedding_updated} 个 Embedding 模型")
        
        # 更新 Multimodal -> MULTIMODAL
        cursor.execute("UPDATE acwl_models SET model_type = 'MULTIMODAL' WHERE model_type = 'Multimodal'")
        multimodal_updated = cursor.rowcount
        print(f"✓ 更新了 {multimodal_updated} 个 Multimodal 模型")
        
        # 更新 Other -> OTHER
        cursor.execute("UPDATE acwl_models SET model_type = 'OTHER' WHERE model_type = 'Other'")
        other_updated = cursor.rowcount
        print(f"✓ 更新了 {other_updated} 个 Other 模型")
        
        # 提交更改
        connection.commit()
        
        # 最终修改枚举定义，只保留新格式
        print("\n步骤3: 更新枚举定义为最终格式...")
        final_alter_sql = """
        ALTER TABLE acwl_models 
        MODIFY COLUMN model_type ENUM('LLM', 'EMBEDDING', 'MULTIMODAL', 'OTHER')
        """
        cursor.execute(final_alter_sql)
        connection.commit()
        print("✓ 枚举定义已更新为最终格式")
        
        # 验证结果
        print("\n验证更新结果:")
        cursor.execute("SELECT model_type, COUNT(*) FROM acwl_models GROUP BY model_type")
        results = cursor.fetchall()
        for model_type, count in results:
            print(f"  {model_type}: {count} 个模型")
        
        # 显示具体的模型信息
        print("\n所有模型的类型信息:")
        cursor.execute("SELECT id, name, model_type FROM acwl_models ORDER BY id")
        models = cursor.fetchall()
        for model_id, model_name, model_type in models:
            print(f"  ID {model_id}: {model_name} - {model_type}")
        
        print("\n✅ 数据库修复完成！")
        
    except mysql.connector.Error as e:
        print(f"❌ 数据库错误: {e}")
        if connection:
            connection.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        if connection:
            connection.rollback()
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    fix_database_enum_values()