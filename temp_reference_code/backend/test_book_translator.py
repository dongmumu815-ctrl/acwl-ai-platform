#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图书标题翻译服务测试脚本

用于测试与外部数据服务的连接和图书标题翻译功能

Usage:
    python test_book_translator.py [task_id]

Args:
    task_id: 可选参数，指定要获取的任务ID，默认为"0"(获取所有任务)
"""

import sys
import logging
from app.services.external_data import DataLink

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """主函数"""
    # 获取命令行参数
    task_id = sys.argv[1] if len(sys.argv) > 1 else "0"
    
    print(f"正在获取任务ID为 {task_id} 的未翻译标题...")
    
    # 创建翻译服务实例
    dataLink = DataLink()
    
    try:
        # 获取未翻译的标题
        result = dataLink.get_link_menu_types()
        
        if result['success']:
            titles = result['data']
            print(f"成功获取 {len(titles)} 条未翻译标题:")
            
            # # 显示前10条记录
            # for i, record in enumerate(titles[:10]):
            #     print(f"{i+1}. ID: {record[0]}, 标题: {record[1]}")
                
            # if len(titles) > 10:
                # print(f"...还有 {len(titles) - 10} 条记录未显示")
            print(titles)
                
            # 这里可以添加调用翻译API的代码
            # 然后使用 translator.update_translated_titles() 更新翻译结果
        else:
            print(f"获取未翻译标题失败: {result['error']}")
    
    except ConnectionError as e:
        print(f"连接错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()