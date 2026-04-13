---
name: book-pdf-meta-parser
description: 通过下载 PDF、提取元数据和文本内容来解析图书信息，支持标题、作者、主题等关键信息提取。
---

# 图书 PDF 元数据解析技能

## 功能概述
该技能能够从 PDF 文档中提取关键元数据和文本内容，包括：
1. **下载 PDF**：从指定 URL 获取 PDF 文件
2. **提取元数据**：获取标题、作者、主题、创建者等信息
3. **文本提取**：从前 3 页提取文本内容（前 500 字符）
4. **页数统计**：获取 PDF 总页数

## 工作流程
1. **输入**：用户提供 PDF URL
2. **下载**：脚本从 URL 下载 PDF 文件
3. **解析**：使用 `pdfplumber` 或 `PyPDF2` 提取元数据
4. **输出**：返回结构化的元数据和文本内容（JSON 格式）

## 环境要求
- Python 3.8+
- 依赖库：`requests`、`pdfplumber` 或 `PyPDF2`、`Pillow`
- **无需系统级依赖**（不需要 poppler）

## 使用示例

### 通过技能测试页面
```json
{
  "url": "http://example.com/book.pdf"
}
```

或

```json
{
  "pdf_url": "http://example.com/book.pdf"
}
```

### 命令行调用
```bash
python book_pdf_parser.py "http://example.com/book.pdf"
```

## 返回结果示例
```json
{
  "status": "success",
  "metadata": {
    "title": "图书标题",
    "author": "作者名称",
    "subject": "主题",
    "creator": "创建工具",
    "producer": "生成工具",
    "pages": 250
  },
  "extracted_text": "提取的前 500 字符文本内容..."
}
```

## 注意事项
- 支持内网地址访问，直接请求用户的内网地址即可
- 支持 HTTP 和 HTTPS 协议
- 文本提取准确度取决于 PDF 的编码方式
- 大型 PDF 文件可能需要较长处理时间
