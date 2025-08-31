import asyncio
import sys
import os

# 添加后端路径到 Python 路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# 切换到后端目录
os.chdir(backend_path)

from app.services.ai_model_service import AIModelService
from app.core.database import AsyncSessionLocal
from app.models.model_service_config import ModelServiceConfig
from sqlalchemy.ext.asyncio import AsyncSession

async def test_ai_model_service():
    """
    直接测试 AI 模型服务，重现错误
    """
    db = None
    try:
        # 获取异步数据库会话
        db = AsyncSessionLocal()
        
        # 查询 Agent 32 的模型服务配置
        from sqlalchemy import select
        result = await db.execute(select(ModelServiceConfig).filter(ModelServiceConfig.id == 13))
        config = result.scalar_one_or_none()
        
        if not config:
            print("未找到模型服务配置 ID 13")
            return
            
        print(f"模型服务配置:")
        print(f"  ID: {config.id}")
        print(f"  提供商: {config.provider}")
        print(f"  模型名称: {config.model_name}")
        print(f"  API端点: {config.api_endpoint}")
        
        # 创建 AI 模型服务实例
        ai_service = AIModelService()
        
        # 准备聊天参数
        system_prompt = "你是一个有用的AI助手。"
        user_message = "你好，请介绍一下自己"
        
        print(f"\n开始调用 AI 模型服务...")
        print(f"系统提示: {system_prompt}")
        print(f"用户消息: {user_message}")
        
        # 调用模型服务
        result = await ai_service.chat_with_model(
            config=config,
            system_prompt=system_prompt,
            user_message=user_message,
            context=None,
            images=None
        )
        
        print(f"\n调用结果:")
        print(f"  类型: {type(result)}")
        print(f"  内容: {result}")
        
        # 检查结果结构
        if isinstance(result, dict):
            print(f"\n结果字段: {list(result.keys())}")
            for key, value in result.items():
                print(f"  {key}: {type(value)} = {value}")
        else:
            print(f"\n错误: 结果不是字典类型，而是 {type(result)}")
            
    except Exception as e:
        print(f"\n异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if db is not None:
            await db.close()

if __name__ == "__main__":
    asyncio.run(test_ai_model_service())