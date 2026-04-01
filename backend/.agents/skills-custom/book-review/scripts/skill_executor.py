import os
import re
from typing import Dict, Any, List, Optional

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from PIL import Image
except ImportError:
    Image = None

from doris_connector import DorisConnector
from mysql_connector import MySQLConnector

# library_name 字段值映射为中文
LIBRARY_NAME_MAP = {
    "0": "敏感词",
    "1": "敏感作者",
    "2": "敏感出版社",
    "3": "敏感书名",
    "4": "敏感领导人",
    "5": "高校",
    "6": "科研机构",
}

LEVEL_ORDER = ["S1", "S2", "S3", "S4", "S5"]


class SkillExecutor:
    """执行各种审读技能"""

    def __init__(self, mysql: MySQLConnector, doris: DorisConnector):
        """
        接收已初始化的数据库连接器（由 ContextManager 传入，复用连接）。
        """
        self.mysql = mysql
        self.doris = doris
        self._doris_connected = False

    # ------------------------------------------------------------------
    # 统一入口
    # ------------------------------------------------------------------
    def execute(self, skill_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        handlers = {
            "query_sensitive_words": self._query_sensitive_words,
            "sensitive_words_check": self._sensitive_words_check,
            "pdf_parse": self._pdf_parse,
            "image_analysis": self._image_analysis,
            "query_book_review": self._query_book_review,
        }
        handler = handlers.get(skill_name)
        if not handler:
            return {"error": f"未知的技能: {skill_name}"}
        return handler(input_data)

    # ------------------------------------------------------------------
    # 技能：按条件查询敏感词库
    # ------------------------------------------------------------------
    def _query_sensitive_words(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        keyword = input_data.get("keyword")
        word_type = input_data.get("word_type")
        library_name = input_data.get("library_name")
        level = input_data.get("level")
        author_ident = input_data.get("author_ident")
        isbn = input_data.get("isbn")
        use_tokenize = bool(input_data.get("use_tokenize", True))
        limit = min(int(input_data.get("limit", 100)), 500)

        print(f"查询敏感词库: keyword={keyword}, word_type={word_type}, "
              f"library_name={library_name}, level={level}, "
              f"author_ident={author_ident}, isbn={isbn}")

        if not any([keyword, word_type, library_name, level, author_ident, isbn]):
            return {"error": "至少需要提供一个查询条件"}

        if use_tokenize and keyword:
            return self._query_with_tokenize(
                keyword=keyword, word_type=word_type, library_name=library_name,
                level=level, author_ident=author_ident, isbn=isbn, limit=limit
            )

        rows = self.mysql.query_sensitive_words(
            keyword=keyword, word_type=word_type, library_name=library_name,
            level=level, author_ident=author_ident, isbn=isbn, limit=limit
        )
        return self._format_sw_result(rows)


    def _query_with_tokenize(
        self, keyword, word_type, library_name, level, author_ident, isbn, limit
    ):
        """对 keyword 分词后分别查询敏感词库，合并去重"""
        tokens = []
        try:
            import jieba
            tokens.extend([t.strip() for t in jieba.cut(keyword) if len(t.strip()) >= 2])
        except ImportError:
            pass
        import re as _re
        en_tokens = [
            t.strip() for t in _re.split(r'[\s,，.。;；\-_/]+', keyword)
            if len(t.strip()) >= 3
        ]
        tokens.extend(en_tokens)
        seen = set()
        unique_tokens = [t for t in tokens if not (t in seen or seen.add(t))]
        if not unique_tokens:
            unique_tokens = [keyword]
        print(f"  分词结果: {unique_tokens}")

        seen_ids = set()
        all_rows = []
        for token in unique_tokens:
            rows = self.mysql.query_sensitive_words(
                keyword=token, word_type=word_type, library_name=library_name,
                level=level, author_ident=author_ident, isbn=isbn, limit=limit
            )
            for row in rows:
                if "error" in row:
                    continue
                row_id = row.get("id")
                if row_id not in seen_ids:
                    seen_ids.add(row_id)
                    all_rows.append(row)

        result = self._format_sw_result(all_rows)
        result["tokens_used"] = unique_tokens
        return result

    def _format_sw_result(self, rows):
        """格式化敏感词查询结果"""
        records = []
        for row in rows:
            if "error" in row:
                return row
            related = row.get("related_words") or ""
            records.append({
                "id": row.get("id"),
                "word": row.get("word"),
                "related_words": [r.strip() for r in related.split(",") if r.strip()],
                "word_type": row.get("word_type"),
                "library_name": row.get("library_name"),
                "level": row.get("level"),
                "forbid_title": row.get("forbid_title_flag") == "1",
                "china_related": row.get("china_related_flag") == "1",
                "description": row.get("description"),
                "author_ident": row.get("author_ident"),
                "isbn": row.get("isbn"),
            })
        return {"status": "success", "total_returned": len(records), "records": records}
    # ------------------------------------------------------------------
    # 技能：对文本执行敏感词扫描
    # ------------------------------------------------------------------
    def _sensitive_words_check(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = input_data.get("text", "")
        min_level = input_data.get("min_level", "S5")
        print(f"执行文本敏感词扫描 (最低等级: {min_level}, 文本长度: {len(text)})...")

        if not text:
            return {"error": "text 不能为空"}

        # 从 MySQL 实时拉取候选词（按等级过滤）
        candidates = self.mysql.query_sensitive_words_by_text(
            text=text,
            level=min_level,
            limit=2000
        )
        print(f"  获取候选敏感词 {len(candidates)} 条，开始文本匹配...")

        try:
            threshold_idx = LEVEL_ORDER.index(min_level)
        except ValueError:
            threshold_idx = 4

        matches = []
        for row in candidates:
            level = row.get("level") or ""
            try:
                level_idx = LEVEL_ORDER.index(level)
            except ValueError:
                level_idx = 4
            if level_idx > threshold_idx:
                continue

            main_word = row.get("word") or ""
            related_raw = row.get("related_words") or ""
            related_words = [r.strip() for r in related_raw.split(",") if r.strip()]

            # 主词 + 关联词都参与匹配
            candidates_words = []
            if main_word:
                candidates_words.append((main_word, "主词"))
            for rw in related_words:
                candidates_words.append((rw, "关联词"))

            for candidate_word, match_type in candidates_words:
                # 跳过过短的关联词（少于4字符），避免 He/Liu 等英文单词误匹配
                if match_type == "关联词" and len(candidate_word) < 4:
                    continue
                pattern = re.compile(re.escape(candidate_word), re.IGNORECASE)
                for match in pattern.finditer(text):
                    start = match.start()
                    matches.append({
                        "word": candidate_word,
                        "main_word": main_word,
                        "match_type": match_type,
                        "level": level,
                        "word_type": row.get("word_type", ""),
                        "forbid_title": row.get("forbid_title_flag") == "1",
                        "china_related": row.get("china_related_flag") == "1",
                        "position": start,
                        "context": text[max(0, start - 30):start + len(candidate_word) + 30]
                    })

        matches.sort(
            key=lambda x: LEVEL_ORDER.index(x["level"]) if x["level"] in LEVEL_ORDER else 99
        )

        return {
            "status": "success",
            "total_matches": len(matches),
            "matches": matches[:300],
            "summary": f"扫描文本 {len(text)} 字符，命中 {len(matches)} 处敏感词"
        }

    # ------------------------------------------------------------------
    # 技能：PDF解析
    # ------------------------------------------------------------------
    def _pdf_parse(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pdf_path = input_data.get("pdf_path", "")
        extract_text = input_data.get("extract_text", True)
        extract_images = input_data.get("extract_images", True)
        print(f"解析PDF: {pdf_path}...")

        if not os.path.exists(pdf_path):
            return {"error": f"PDF文件不存在: {pdf_path}"}
        if PdfReader is None:
            return {"error": "pypdf 库未安装，请执行: pip install pypdf"}

        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            result: Dict[str, Any] = {
                "status": "success",
                "total_pages": total_pages,
                "text": "",
                "image_summary": {}
            }

            if extract_text:
                pages_text = []
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        pages_text.append(f"--- 第{i + 1}页 ---\n{page_text}")
                result["text"] = "\n".join(pages_text)

            if extract_images:
                image_count = 0
                for page in reader.pages:
                    resources = page.get("/Resources")
                    if resources:
                        xobject = resources.get("/XObject")
                        if xobject:
                            xobj = xobject.get_object()
                            for obj_key in xobj:
                                if xobj[obj_key].get("/Subtype") == "/Image":
                                    image_count += 1
                result["image_summary"] = {"total_images": image_count}

            return result
        except Exception as e:
            return {"error": f"PDF解析失败: {str(e)}"}

    # ------------------------------------------------------------------
    # 技能：插图分析
    # ------------------------------------------------------------------
    def _image_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        image_path = input_data.get("image_path", "")
        analysis_type = input_data.get("analysis_type", "content")
        print(f"分析图像: {image_path} (类型: {analysis_type})...")

        if not os.path.exists(image_path):
            return {"error": f"图像文件不存在: {image_path}"}
        if Image is None:
            return {"error": "Pillow 库未安装，请执行: pip install pillow"}

        try:
            img = Image.open(image_path)
            return {
                "status": "success",
                "file_path": image_path,
                "format": img.format,
                "size": {"width": img.size[0], "height": img.size[1]},
                "mode": img.mode,
                "analysis_type": analysis_type,
                "note": "基础属性已获取，深度内容分析需接入视觉模型"
            }
        except Exception as e:
            return {"error": f"图像分析失败: {str(e)}"}

    # ------------------------------------------------------------------
    # 技能：查询审读库
    # ------------------------------------------------------------------
    def _query_book_review(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        isbn = input_data.get("isbn")
        title = input_data.get("title")
        author = input_data.get("author")
        publisher = input_data.get("publisher")
        limit = min(int(input_data.get("limit", 20)), 100)

        print(f"查询审读库: isbn={isbn}, title={title}, author={author}, publisher={publisher}")

        if not any([isbn, title, author, publisher]):
            return {"error": "至少需要提供一个查询条件"}

        try:
            self._ensure_doris_connected()
            rows = self.doris.query_book_review(
                isbn=isbn,
                title=title,
                author=author,
                publisher=publisher,
                limit=limit
            )

            for row in rows:
                if isinstance(row, dict):
                    for k, v in row.items():
                        if hasattr(v, 'isoformat'):
                            row[k] = v.isoformat()

            return {
                "status": "success",
                "total_returned": len(rows),
                "records": rows
            }
        except Exception as e:
            return {"error": f"查询审读库失败: {str(e)}"}

    def _ensure_doris_connected(self):
        if not self._doris_connected:
            self.doris.connect()
            self._doris_connected = True
