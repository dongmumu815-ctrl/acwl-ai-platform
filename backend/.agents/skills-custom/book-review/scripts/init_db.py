"""
Doris数据库初始化脚本

执行此脚本创建必要的表和导入示例数据
"""

import pymysql
from config import DORIS_HOST, DORIS_PORT, DORIS_USER, DORIS_PASSWORD, DORIS_DB

def init_database():
    """初始化数据库"""
    
    # 连接到Doris
    connection = pymysql.connect(
        host=DORIS_HOST,
        port=DORIS_PORT,
        user=DORIS_USER,
        password=DORIS_PASSWORD,
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    
    try:
        # 创建数据库
        print(f"创建数据库: {DORIS_DB}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DORIS_DB}")
        cursor.execute(f"USE {DORIS_DB}")
        
        # 创建敏感词表
        print("创建敏感词表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensitive_words (
                id BIGINT NOT NULL,
                word VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                severity VARCHAR(20),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            ) ENGINE=OLAP
            DUPLICATE KEY (id)
            DISTRIBUTED BY HASH(id) BUCKETS 10
            PROPERTIES (
                "replication_num" = "1"
            )
        """)
        
        # 创建审读规则表
        print("创建审读规则表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_rules (
                id BIGINT NOT NULL,
                rule_name VARCHAR(255) NOT NULL,
                description TEXT,
                rule_type VARCHAR(100),
                severity VARCHAR(20),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            ) ENGINE=OLAP
            DUPLICATE KEY (id)
            DISTRIBUTED BY HASH(id) BUCKETS 10
            PROPERTIES (
                "replication_num" = "1"
            )
        """)
        
        # 插入示例敏感词数据
        print("插入示例敏感词数据...")
        sample_words = [
            (1, "暴力", "内容安全", "high"),
            (2, "色情", "内容安全", "high"),
            (3, "歧视", "社会责任", "medium"),
            (4, "欺诈", "法律合规", "high"),
            (5, "毒品", "内容安全", "high"),
            (6, "自杀", "心理健康", "high"),
            (7, "恐怖", "内容安全", "medium"),
            (8, "仇恨", "社会责任", "medium"),
        ]
        
        for word_id, word, category, severity in sample_words:
            cursor.execute(
                "INSERT INTO sensitive_words (id, word, category, severity) VALUES (%s, %s, %s, %s)",
                (word_id, word, category, severity)
            )
        
        # 插入示例审读规则数据
        print("插入示例审读规则数据...")
        sample_rules = [
            (1, "暴力内容检查", "检查是否包含过度暴力描写", "内容审查", "high"),
            (2, "色情内容检查", "检查是否包含色情或不当内容", "内容审查", "high"),
            (3, "年龄适配性", "检查内容是否适合目标年龄段", "年龄分级", "medium"),
            (4, "语言规范", "检查是否使用不规范或冒犯性语言", "语言审查", "medium"),
            (5, "事实准确性", "检查是否包含明显的虚假信息", "事实核查", "medium"),
            (6, "版权合规", "检查是否尊重知识产权", "法律合规", "high"),
        ]
        
        for rule_id, name, desc, rule_type, severity in sample_rules:
            cursor.execute(
                "INSERT INTO review_rules (id, rule_name, description, rule_type, severity) VALUES (%s, %s, %s, %s, %s)",
                (rule_id, name, desc, rule_type, severity)
            )
        
        connection.commit()
        print("✓ 数据库初始化完成")
        
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    print("开始初始化Doris数据库...")
    print(f"连接信息: {DORIS_HOST}:{DORIS_PORT}")
    init_database()
