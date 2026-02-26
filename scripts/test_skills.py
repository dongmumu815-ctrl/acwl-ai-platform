import asyncio
import os
import sys
import json
from pathlib import Path

# 添加 backend 到 path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.services.agent_skills import agent_skill_service

async def test_skills():
    print("=== Testing Agent Skills Service ===")
    
    # 1. 检查技能加载
    skills = agent_skill_service.get_skill_tools()
    print(f"Loaded Skills ({len(skills)}):")
    
    # Check SkillAdapter directly to verify metadata
    adapter_skills = agent_skill_service.skill_adapter.list_skills()
    print(f"\nMetadata check from SkillAdapter ({len(adapter_skills)} skills):")
    for s in adapter_skills:
        name = s.get('name')
        tool_type = s.get('tool_type')
        is_builtin = s.get('is_builtin')
        print(f" - {name}: type={tool_type}, builtin={is_builtin}")

    print(f"\nTool instances:")
    for s in skills:
        print(f" - {s.name}: {s.description[:50]}...")
        
    if not skills:
        print("Error: No skills loaded!")
        return

    # 2. 尝试调用 skill-creator 技能 (如果存在)
    # 注意：skill-creator 是一个指南型 Skill，可能没有 Python 执行逻辑，或者只是文档
    # 我们检查是否有可执行的 skill
    
    target_skill = "skill-creator"
    # 如果 skill-creator 没有注册为 tool (因为它可能只是文档)，我们找一个别的
    
    print("\n=== Verifying Skill Availability ===")
    # 检查 skill-creator 是否在 available_skills 中
    if target_skill in agent_skill_service.available_skills:
        print(f"Skill '{target_skill}' is loaded as a tool.")
        tool = agent_skill_service.available_skills[target_skill]
        print(f"Tool class: {tool.__class__.__name__}")
        
        # Test 1: Standard call
        print(f"\nTesting standard execution of '{target_skill}'...")
        try:
            result = tool.call(params="{}")
            print(f"Result: {result[:100]}...")
        except Exception as e:
            print(f"Standard execution failed: {e}")

        # Test 2: Script execution (if supported)
        print(f"\nTesting script execution of '{target_skill}'...")
        if "Available executable scripts" in tool.description:
            print("Script execution supported detected in description.")
            try:
                # Try running init_skill.py with --help
                params = json.dumps({
                    "run_script": "init_skill.py",
                    "args": "--help"
                })
                result = tool.call(params=params)
                print(f"Script Result:\n{result}")
            except Exception as e:
                print(f"Script execution failed: {e}")
        else:
            print("Script execution NOT detected in description.")

    else:
        print(f"Skill '{target_skill}' is NOT loaded as a tool (might be documentation only).")
        
    # 3. Test RolePlay Integration (verify registration fix)
    print("\n=== Testing RolePlay Integration ===")
    try:
        # Dummy model config - we just want to test initialization
        model_config = {
            'model_name': 'qwen-max',
            'api_key': 'dummy',
            'provider': 'dashscope'
        }
        # We don't actually run it because we don't have API key here, 
        # but we can try to initialize. 
        # Actually execute_skill_task runs it immediately.
        # But if we get past initialization, the NotImplementedError is gone.
        
        # We can mock RolePlay if needed, but let's just try to run and catch the expected LLM error
        # The NotImplementedError happens during __init__, so if we catch an LLM error (like 401), we are good.
        
        print("Attempting to initialize RolePlay with skill...")
        # Just use a simple prompt
        result = await agent_skill_service.execute_skill_task(
            prompt="Test prompt",
            model_config=model_config,
            enabled_skills=[target_skill]
        )
        print(f"RolePlay Execution Result (might be error string): {result[:100]}...")
        
        if "NotImplementedError" not in result:
             print("SUCCESS: RolePlay initialized without NotImplementedError.")
        else:
             print("FAILURE: NotImplementedError still present.")
             
    except Exception as e:
        print(f"RolePlay Integration Test Failed: {e}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_skills())
