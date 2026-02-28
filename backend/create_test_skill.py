import asyncio
import sys
import os

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.agent import AgentTool, ToolType

# 定义 Skill 代码
LOCAL_TIME_SKILL_CODE = """
from modelscope_agent.tools import BaseTool, register_tool
import datetime

@register_tool('local_time')
class LocalTimeTool(BaseTool):
    description = '获取当前的本地时间'
    name = 'local_time'
    parameters = []

    def call(self, params: str, **kwargs) -> str:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"Current local time is: {now}"
"""

async def create_skill():
    db_url = settings.database_url.replace("mysql+pymysql", "mysql+aiomysql")
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 检查是否已存在
        from sqlalchemy import select
        result = await session.execute(select(AgentTool).where(AgentTool.name == "local_time"))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("Updating existing skill 'local_time'...")
            existing.code = LOCAL_TIME_SKILL_CODE
            existing.description = "获取当前的本地时间"
            existing.tool_type = ToolType.CUSTOM
            existing.display_name = "本地时间"
        else:
            print("Creating new skill 'local_time'...")
            new_tool = AgentTool(
                name="local_time",
                display_name="本地时间",
                description="获取当前的本地时间",
                tool_type=ToolType.CUSTOM,
                code=LOCAL_TIME_SKILL_CODE,
                is_enabled=True,
                is_builtin=False
            )
            session.add(new_tool)
        
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(create_skill())
