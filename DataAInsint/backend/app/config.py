import os
from pathlib import Path

def load_env_file(env_file_path: str = None):
    """加载.env文件中的环境变量"""
    if env_file_path is None:
        # 默认查找项目根目录下的.env文件
        current_dir = Path(__file__).parent.parent
        env_file_path = current_dir / ".env"
    
    if not os.path.exists(env_file_path):
        print(f"环境变量文件 {env_file_path} 不存在，使用默认配置")
        return
    
    try:
        with open(env_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释行
                if not line or line.startswith('#'):
                    continue
                
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 移除值两端的引号（如果有）
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # 设置环境变量
                    os.environ[key] = value
        
        print(f"已加载环境变量文件: {env_file_path}")
    except Exception as e:
        print(f"加载环境变量文件失败: {e}")

# 在模块导入时自动加载.env文件
load_env_file()