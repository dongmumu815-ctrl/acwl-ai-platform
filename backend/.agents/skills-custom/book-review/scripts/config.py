import os
from dotenv import load_dotenv

load_dotenv()

# Doris数据库配置（审读库）
DORIS_HOST = os.getenv("DORIS_HOST", "10.20.1.201")
DORIS_PORT = int(os.getenv("DORIS_PORT", 9030))
DORIS_USER = os.getenv("DORIS_USER", "root")
DORIS_PASSWORD = os.getenv("DORIS_PASSWORD", "2wsx1QAZaczt")
DORIS_DB = os.getenv("DORIS_DB", "cepiec_test")

# MySQL数据库配置（敏感词库）
MYSQL_HOST = os.getenv("MYSQL_HOST", "10.20.1.200")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "2wsx1QAZaczt")
MYSQL_DB = os.getenv("MYSQL_DB", "acwl-baselib")

# 本地大模型配置（SGLang，兼容 OpenAI 接口）
LLM_BASE_URL = os.getenv("LLM_BASE_URL","http://10.20.1.221:8002/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY","vllm")
LLM_MODEL = os.getenv("LLM_MODEL","qwen3.5-35b-fp8")

# MinIO 对象存储配置
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "10.20.1.212:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadminUd1vFqj5L4QxAWtI")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "actable")
MINIO_FOLDER = os.getenv("MINIO_FOLDER", "ai_read_reports")

# 上下文配置
MAX_CONTEXT_TOKENS = 100000        # 保留给上下文的token数
SENSITIVE_WORDS_BATCH_SIZE = 1000  # 每批加载的敏感词数量
BOOK_REVIEW_QUERY_LIMIT = 20       # 审读库单次查询返回最大条数
