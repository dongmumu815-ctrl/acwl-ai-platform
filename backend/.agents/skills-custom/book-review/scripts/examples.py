"""
示例脚本：演示如何使用Book Review Agent

使用前需要：
1. 配置 .env 文件中的数据库和API密钥
2. 在Doris中创建必要的表
3. 导入示例数据
"""

from agent import BookReviewAgent
import json

def example_1_simple_review():
    """示例1：简单的文本审读"""
    print("\n" + "="*60)
    print("示例1: 简单的文本审读")
    print("="*60)
    
    agent = BookReviewAgent()
    agent.initialize()
    
    book_content = """
    这是一部关于冒险的故事。主人公踏上了一段充满挑战的旅程。
    他遇到了许多有趣的人物，学到了宝贵的人生经验。
    """
    
    result = agent.review_book(book_content, "冒险故事")
    print("\n📋 审读结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

def example_2_pdf_review():
    """示例2：PDF文件审读"""
    print("\n" + "="*60)
    print("示例2: PDF文件审读")
    print("="*60)
    
    agent = BookReviewAgent()
    agent.initialize()
    
    book_content = """
    请审读以下PDF文件中的内容。
    PDF路径: /path/to/book.pdf
    """
    
    result = agent.review_book(book_content, "PDF图书")
    print("\n📋 审读结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

def example_3_interactive():
    """示例3：交互式审读"""
    print("\n" + "="*60)
    print("示例3: 交互式审读模式")
    print("="*60)
    
    agent = BookReviewAgent()
    agent.initialize()
    agent.interactive_review()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num == "1":
            example_1_simple_review()
        elif example_num == "2":
            example_2_pdf_review()
        elif example_num == "3":
            example_3_interactive()
        else:
            print("未知的示例编号")
    else:
        print("用法: python examples.py [1|2|3]")
        print("  1 - 简单的文本审读")
        print("  2 - PDF文件审读")
        print("  3 - 交互式审读模式")
