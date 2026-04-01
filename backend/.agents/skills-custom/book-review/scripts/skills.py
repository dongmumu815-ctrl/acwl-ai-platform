from typing import List, Dict, Any

# 技能定义列表
SKILLS = [
    {
        "name": "query_sensitive_words",
        "description": (
            "按条件从敏感词库（cpc_sensitive_word）中检索敏感词，返回命中的词条信息。"
            "支持按关键词、词类型、所属库、敏感等级、作者标识、ISBN等字段查询。"
            "在审读前，应先用书名/作者/ISBN等信息查询是否有直接命中的敏感词条。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "关键词，同时模糊匹配主敏感词（word）和关联词（related_words）"
                },
                "word_type": {
                    "type": "string",
                    "description": "敏感词类型，如：宗教人物、政治人物、地理敏感等"
                },
                "library_name": {
                    "type": "string",
                    "description": "所属库名称（library_name字段），模糊匹配"
                },
                "level": {
                    "type": "string",
                    "enum": ["S1", "S2", "S3", "S4", "S5"],
                    "description": "精确匹配指定等级（取 level 字段）：S1=绝对禁词、S2=禁词、S3=高敏感、S4=敏感、S5=辅助词"
                },
                "author_ident": {
                    "type": "string",
                    "description": "作者标识符（ORCID/Researcher ID/Scopus Author ID），模糊匹配"
                },
                "isbn": {
                    "type": "string",
                    "description": "关联ISBN，模糊匹配"
                },
                "use_tokenize": {
                    "type": "boolean",
                    "description": "是否对 keyword 进行分词后逐词查询（适用于书名、作者、机构等元数据）。默认 false"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回最大条数，默认100，最大500"
                }
            },
            "required": []
        }
    },
    {
        "name": "sensitive_words_check",
        "description": (
            "对给定文本执行敏感词扫描。需先调用 query_sensitive_words 获取候选词后，"
            "再调用本技能传入文本进行精确匹配，返回命中位置和上下文。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "需要扫描的文本内容"
                },
                "min_level": {
                    "type": "string",
                    "enum": ["S1", "S2", "S3", "S4", "S5"],
                    "description": "最低等级阈值（取 level 字段），只扫描 <= 该等级的词（S1最严重）。默认 S5 扫描全部"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "pdf_parse",
        "description": "解析本地PDF文件，提取各页文本和图像数量",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "PDF文件的本地路径"
                },
                "extract_text": {
                    "type": "boolean",
                    "description": "是否提取文本，默认 true"
                },
                "extract_images": {
                    "type": "boolean",
                    "description": "是否统计图像数量，默认 true"
                }
            },
            "required": ["pdf_path"]
        }
    },
    {
        "name": "image_analysis",
        "description": "分析本地图像文件的基本属性，用于插图内容审查",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图像文件的本地路径"
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["content", "style", "sensitivity"],
                    "description": "分析类型：content(内容)、style(风格)、sensitivity(敏感性)"
                }
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "query_book_review",
        "description": (
            "从Doris审读库（cpc_book_review，200万条历史记录）中查询图书的历史审读结论。"
            "核心评判字段为 review_lib_type（审读库类型，已翻译为中文，如：实物禁发、电子通过、实物限阅等）。"
            "可按 ISBN、书名、作者、出版社进行检索。至少提供一个条件。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "isbn": {
                    "type": "string",
                    "description": "ISBN（支持 ISBN10/ISBN13/EISBN/PISBN）"
                },
                "title": {
                    "type": "string",
                    "description": "书名关键词（模糊匹配）"
                },
                "author": {
                    "type": "string",
                    "description": "作者名关键词（模糊匹配）"
                },
                "publisher": {
                    "type": "string",
                    "description": "出版社名关键词（模糊匹配）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回最大条数，默认20，最大100"
                }
            },
            "required": []
        }
    }
]


def get_tools_definition() -> List[Dict]:
    """返回 OpenAI function calling 格式的工具定义列表"""
    return [
        {
            "name": skill["name"],
            "description": skill["description"],
            "input_schema": skill["input_schema"]
        }
        for skill in SKILLS
    ]
