#!/usr/bin/env python3
"""
Book Review Agent - 主入口

使用方式:
  python main.py review <content> [--title title]  # 审读文本
  python main.py pdf <pdf_path>                     # 审读PDF
  python main.py interactive                        # 交互模式
  python main.py init-db                            # 初始化数据库
"""

import re
import sys
import io
import argparse
from contextlib import redirect_stdout, redirect_stderr
from agent import BookReviewAgent
from init_db import init_database

# 字段名映射（用户输入的中文字段名 -> 标准key）
FIELD_MAP = {
    'isbn': 'isbn',
    'ISBN': 'isbn',
    '正题名': 'title',
    '书名': 'title',
    '题名': 'title',
    '作者': 'author',
    '著者': 'author',
    '出版社': 'publisher',
    '出版者': 'publisher',
}


def parse_metadata(raw: str):
    """
    解析结构化元数据字符串，例如：
      "ISBN:9781760763992,正题名:About Face，作者:Amber Creswell Bell，出版社：Thames & Hudson Australia"
    返回 (structured_content, title)
    - structured_content: 传给 agent 的结构化描述文本
    - title: 从元数据中提取的书名（用于报告文件名）
    """
    # 按中英文逗号切分
    parts = re.split(r'[,，]', raw)
    fields = {}
    for part in parts:
        # 按第一个冒号（中英文）切分
        m = re.split(r'[:：]', part.strip(), maxsplit=1)
        if len(m) == 2:
            key_raw = m[0].strip()
            val = m[1].strip()
            key = FIELD_MAP.get(key_raw)
            if key:
                fields[key] = val

    # 如果没有解析到任何字段，直接原样返回
    if not fields:
        return raw, '未命名'

    title = fields.get('title', '未命名')

    # 构建给大模型的结构化描述
    lines = ['请对以下图书元数据进行审读：', '']
    if fields.get('isbn'):
        lines.append(f'ISBN: {fields["isbn"]}')
    if fields.get('title'):
        lines.append(f'书名: {fields["title"]}')
    if fields.get('author'):
        lines.append(f'作者: {fields["author"]}')
    if fields.get('publisher'):
        lines.append(f'出版社: {fields["publisher"]}')
    lines.append('')
    lines.append('请分别对 ISBN、书名、作者、出版社逐一查询敏感词库，并查询历史审读记录，生成审读报告。')

    print(f"解析元数据: {fields}")
    return '\n'.join(lines), title


def main():
    parser = argparse.ArgumentParser(
        description="图书审读Agent系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python main.py review "ISBN:9781760763992,正题名:About Face，作者:Amber Creswell Bell，出版社：Thames & Hudson Australia"
  python main.py review "这是一部关于冒险的故事" --title "冒险故事"
  python main.py pdf /path/to/book.pdf
  python main.py interactive
  python main.py init-db
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    review_parser = subparsers.add_parser('review', help='审读文本内容')
    review_parser.add_argument('content', help='要审读的文本内容或元数据（字段名:值，逗号分隔）')
    review_parser.add_argument('--title', '-t', default='未命名', help='图书标题（可选，自动从元数据中提取）')

    pdf_parser = subparsers.add_parser('pdf', help='审读PDF文件')
    pdf_parser.add_argument('pdf_path', help='PDF文件路径')

    subparsers.add_parser('interactive', help='进入交互式审读模式')
    subparsers.add_parser('init-db', help='初始化Doris数据库')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'init-db':
        print("初始化Doris数据库...")
        init_database()

    elif args.command == 'review':
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            agent = BookReviewAgent()
            agent.initialize()
            content, title = parse_metadata(args.content)
            if args.title != '未命名':
                title = args.title
            result = agent.review_book(content, title)
        print(result['response'])

    elif args.command == 'pdf':
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            agent = BookReviewAgent()
            agent.initialize()
            content = f"请审读以下PDF文件: {args.pdf_path}"
            result = agent.review_book(content, f"PDF: {args.pdf_path}")
        print(result['response'])

    elif args.command == 'interactive':
        print("启动图书审读Agent...")
        agent = BookReviewAgent()
        agent.initialize()
        agent.interactive_review()


if __name__ == '__main__':
    main()
