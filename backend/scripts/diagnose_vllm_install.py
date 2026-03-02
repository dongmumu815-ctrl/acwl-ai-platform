import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance, AppDeployment, AppTemplate
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

async def main():
    print("🚀 开始诊断 vLLM 安装问题...")
    
    async with AsyncSessionLocal() as db:
        # 1. 查找最近的 vLLM 实例
        # 先找到 vLLM 模板 ID
        stmt = select(AppTemplate).where(AppTemplate.name == "vllm")
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()
        
        if not template:
            print("❌ 未找到 vLLM 模板")
            return

        print(f"✅ 找到 vLLM 模板: {template.name} (ID: {template.id})")
        
        # 查找该模板的所有实例
        stmt = select(AppInstance).where(
            AppInstance.template_id == template.id
        ).options(
            selectinload(AppInstance.deployments)
        ).order_by(desc(AppInstance.created_at)).limit(5)
        
        result = await db.execute(stmt)
        instances = result.scalars().all()
        
        if not instances:
            print("❌ 未找到 vLLM 实例")
            return
            
        print(f"🔍 找到 {len(instances)} 个最近的 vLLM 实例:")
        
        for instance in instances:
            print(f"\n--- 实例 ID: {instance.id} ---")
            print(f"名称: {instance.name}")
            print(f"状态: {instance.status}")
            print(f"配置: {instance.config}")
            print(f"创建时间: {instance.created_at}")
            
            if not instance.deployments:
                print("❌ 无部署记录")
                continue
                
            print(f"📦 包含 {len(instance.deployments)} 个部署:")
            for deploy in instance.deployments:
                print(f"  - 部署 ID: {deploy.id}")
                print(f"    服务器 ID: {deploy.server_id}")
                print(f"    状态: {deploy.status}")
                print(f"    容器 ID: {deploy.container_id}")
                # 注意：这里假设有一个 logs 字段或者关联的执行记录，如果模型里没有，可能无法直接查看日志
                # 如果有 script_execution_id 或类似关联，可以进一步查询
                
                # 尝试查询关联的 ScriptExecutionRecord (如果有的话)
                # 这需要知道 AppDeployment 和 ScriptExecutionRecord 的关联方式
                # 假设通常通过 tag 或 description 关联，或者只是查看最近的脚本执行记录
                
        # 2. 检查最近的脚本执行记录（可能是部署脚本）
        from app.models.script_execution import ScriptExecutionRecord
        stmt = select(ScriptExecutionRecord).order_by(
            desc(ScriptExecutionRecord.created_at)
        ).limit(5)
        result = await db.execute(stmt)
        scripts = result.scalars().all()
        
        print("\n📜 最近的 5 条脚本执行记录:")
        for script in scripts:
            print(f"  - ID: {script.id}, 类型: {script.script_type}, 状态: {script.status}, 创建时间: {script.created_at}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 发生错误: {e}")
