#!/usr/bin/env python3
"""
创建测试标签数据的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.data_resource import DataResource, DataResourceTag, DataResourceTagRelation
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime

def create_test_tags():
    """创建测试标签数据"""
    # 直接创建数据库连接
    engine = create_engine('sqlite:///test.db')
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 检查是否已有标签数据
        existing_tags = db.query(DataResourceTag).count()
        print(f"当前数据库中有 {existing_tags} 个标签")
        
        # 创建测试标签
        test_tags = [
            {
                "name": "测试标签1",
                "color": "#FF5722",
                "description": "这是一个测试标签",
                "status": "active",
                "created_by": 5,
                "updated_by": 5
            },
            {
                "name": "数据分析",
                "color": "#2196F3", 
                "description": "用于数据分析的资源",
                "status": "active",
                "created_by": 5,
                "updated_by": 5
            },
            {
                "name": "机器学习",
                "color": "#4CAF50",
                "description": "机器学习相关资源",
                "status": "active", 
                "created_by": 5,
                "updated_by": 5
            }
        ]
        
        created_tags = []
        for tag_data in test_tags:
            # 检查标签是否已存在
            existing_tag = db.query(DataResourceTag).filter(
                DataResourceTag.name == tag_data["name"]
            ).first()
            
            if not existing_tag:
                tag = DataResourceTag(**tag_data)
                db.add(tag)
                db.flush()  # 获取ID
                created_tags.append(tag)
                print(f"创建标签: {tag.name} (ID: {tag.id})")
            else:
                created_tags.append(existing_tag)
                print(f"标签已存在: {existing_tag.name} (ID: {existing_tag.id})")
        
        # 获取第一个数据资源
        first_resource = db.query(DataResource).first()
        if first_resource:
            print(f"找到数据资源: {first_resource.name} (ID: {first_resource.id})")
            
            # 为第一个资源添加标签关联
            for i, tag in enumerate(created_tags[:2]):  # 只添加前两个标签
                # 检查关联是否已存在
                existing_relation = db.query(DataResourceTagRelation).filter(
                    DataResourceTagRelation.resource_id == first_resource.id,
                    DataResourceTagRelation.tag_id == tag.id
                ).first()
                
                if not existing_relation:
                    relation = DataResourceTagRelation(
                        resource_id=first_resource.id,
                        tag_id=tag.id,
                        created_by=5
                    )
                    db.add(relation)
                    print(f"创建标签关联: 资源 {first_resource.id} <-> 标签 {tag.id}")
                else:
                    print(f"标签关联已存在: 资源 {first_resource.id} <-> 标签 {tag.id}")
        else:
            print("未找到数据资源")
        
        # 提交事务
        db.commit()
        print("测试标签数据创建完成！")
        
        # 验证数据
        total_tags = db.query(DataResourceTag).count()
        total_relations = db.query(DataResourceTagRelation).count()
        print(f"总标签数: {total_tags}")
        print(f"总关联数: {total_relations}")
        
    except Exception as e:
        db.rollback()
        print(f"创建测试数据时出错: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_tags()