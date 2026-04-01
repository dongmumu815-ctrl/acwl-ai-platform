import pymysql
from typing import List, Dict, Any, Optional
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB


class MySQLConnector:
    """MySQL连接器 - 用于按需查询敏感词库 cpc_sensitive_word"""

    def __init__(self):
        self.connection = None

    def connect(self):
        """建立MySQL连接"""
        try:
            self.connection = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                charset='utf8mb4'
            )
            print(f"已连接到MySQL: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
        except Exception as e:
            print(f"MySQL连接失败: {e}")
            raise

    def disconnect(self):
        """关闭连接"""
        if self.connection and self.connection.open:
            self.connection.close()

    def ensure_connected(self):
        """确保连接有效（断线自动重连）"""
        try:
            if not self.connection or not self.connection.open:
                self.connect()
            else:
                self.connection.ping(reconnect=True)
        except Exception:
            self.connect()

    def query_sensitive_words(
        self,
        keyword: Optional[str] = None,
        word_type: Optional[str] = None,
        library_name: Optional[str] = None,
        level: Optional[str] = None,
        author_ident: Optional[str] = None,
        isbn: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        按条件查询敏感词库，各字段使用 LIKE 模糊匹配。
        支持字段：
          - keyword      : 匹配 word（主词）和 related_words（关联词）
          - word_type    : 敏感词类型
          - library_name : 所属库名称
          - level        : 敏感等级（S1-S5），取 level 字段
          - author_ident : 作者标识符（ORCID等）
          - isbn         : 关联ISBN
        """
        self.ensure_connected()

        conditions = []
        params = []

        if keyword:
            conditions.append("(word LIKE %s OR related_words LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if word_type:
            conditions.append("word_type LIKE %s")
            params.append(f"%{word_type}%")
        if library_name:
            conditions.append("library_name LIKE %s")
            params.append(f"%{library_name}%")
        if level:
            conditions.append("`level` = %s")
            params.append(level)
        if author_ident:
            conditions.append("(author_ident LIKE %s OR orcid LIKE %s)")
            params.extend([f"%{author_ident}%", f"%{author_ident}%"])
        if isbn:
            conditions.append("isbn LIKE %s")
            params.append(f"%{isbn}%")

        if not conditions:
            return [{"error": "至少需要提供一个查询条件"}]

        where_clause = " AND ".join(conditions)
        sql = f"""
            SELECT
                id, word, related_words, word_type, library_name,
                `level`,
                forbid_title_flag, china_related_flag,
                description, author_ident, orcid, isbn,
                erp_level, is_long_term
            FROM cpc_sensitive_word
            WHERE {where_clause}
            ORDER BY
                FIELD(`level`, 'S1','S2','S3','S4','S5'),
                id
            LIMIT {int(limit)}
        """

        try:
            cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute(sql, params)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"查询敏感词失败: {e}")
            return [{"error": str(e)}]

    def query_sensitive_words_by_text(
        self,
        text: str,
        level: Optional[str] = None,
        limit: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        批量获取敏感词供文本扫描使用（Python侧做正则匹配）。
        可按 level 字段过滤等级。
        """
        self.ensure_connected()

        level_filter = ""
        params: List[Any] = []
        if level:
            level_filter = "AND `level` <= %s"
            params.append(level)

        sql = f"""
            SELECT
                id, word, related_words, word_type, library_name,
                `level`, forbid_title_flag, china_related_flag, description
            FROM cpc_sensitive_word
            WHERE `level` IS NOT NULL
            {level_filter}
            ORDER BY FIELD(`level`, 'S1','S2','S3','S4','S5'), id
            LIMIT {int(limit)}
        """

        try:
            cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute(sql, params)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"批量获取敏感词失败: {e}")
            return []
