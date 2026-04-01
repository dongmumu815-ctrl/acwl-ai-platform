import pymysql
from typing import List, Dict, Any, Optional
from config import DORIS_HOST, DORIS_PORT, DORIS_USER, DORIS_PASSWORD, DORIS_DB, BOOK_REVIEW_QUERY_LIMIT

# review_lib_type 字段值映射为中文
REVIEW_LIB_TYPE_MAP = {
    "review_book_paper_banned":      "实物禁发",
    "review_book_electronic_banned": "电子禁发",
    "review_book_paper_pass":        "实物通过",
    "review_book_electronic_pass":   "电子通过",
    "review_book_paper_limited":     "实物限阅",
    "review_book_electronic_problem":"电子问题",
    "review_book_order_pass":        "订单通过",
    "review_book_order_cancel":      "订单撤订",
    "review_article_sensitive":      "敏感文章",
    "review_article_pass":           "文章通过",
    "collect_banned":                "采集禁发",
    "collect_limited":               "采集限阅",
    "customer_banned":               "客户禁发",
    "customer_limited":              "客户限阅",
}


class DorisConnector:
    """Doris连接器 - 用于按需查询审读库 cpc_book_review（200万条，不全量加载）"""

    def __init__(self):
        self.connection = None

    def connect(self):
        """建立Doris连接"""
        try:
            self.connection = pymysql.connect(
                host=DORIS_HOST,
                port=DORIS_PORT,
                user=DORIS_USER,
                password=DORIS_PASSWORD,
                database=DORIS_DB,
                charset='utf8mb4'
            )
            print(f"已连接到Doris: {DORIS_HOST}:{DORIS_PORT}/{DORIS_DB}")
        except Exception as e:
            print(f"Doris连接失败: {e}")
            raise

    def disconnect(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()

    def query_book_review(
        self,
        isbn: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        publisher: Optional[str] = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        按条件检索审读记录，返回 review_lib_type（评判标准）作为核心字段。
        至少需要提供一个查询条件。
        """
        if not any([isbn, title, author, publisher]):
            return [{"error": "至少需要提供一个查询条件"}]

        if limit is None:
            limit = BOOK_REVIEW_QUERY_LIMIT

        conditions = []
        params = []

        if isbn:
            conditions.append("(isbn = %s OR eisbn = %s OR pisbn = %s OR isbn10 = %s OR isbn13 = %s)")
            params.extend([isbn, isbn, isbn, isbn, isbn])
        if title:
            conditions.append("title LIKE %s")
            params.append(f"%{title}%")
        if author:
            conditions.append("author LIKE %s")
            params.append(f"%{author}%")
        if publisher:
            conditions.append("publisher LIKE %s")
            params.append(f"%{publisher}%")

        where_clause = " AND ".join(conditions)

        try:
            cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            query = f"""
                SELECT
                    id, isbn, eisbn, pisbn,
                    title, title_cn,
                    author, publisher,
                    review_lib_type,
                    review_remark,
                    limitread_mode,
                    content_summary,
                    read_standard_rules,
                    create_time
                FROM cpc_book_review
                WHERE {where_clause}
                ORDER BY create_time DESC
                LIMIT {limit}
            """
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()

            # 将 review_lib_type 翻译为中文，追加 review_lib_type_cn 字段
            for row in rows:
                raw = row.get("review_lib_type") or ""
                row["review_lib_type_cn"] = REVIEW_LIB_TYPE_MAP.get(raw.strip(), raw)

            return rows
        except Exception as e:
            print(f"查询审读库失败: {e}")
            return [{"error": str(e)}]
