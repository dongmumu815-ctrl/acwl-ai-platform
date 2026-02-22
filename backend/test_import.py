try:
    import ms_agent
    print("ms_agent: FOUND")
except ImportError:
    print("ms_agent: NOT FOUND")

try:
    import modelscope_agent
    print(f"modelscope_agent: FOUND, version: {getattr(modelscope_agent, '__version__', 'unknown')}")
    # 尝试查找 Agent 和 Tool
    import inspect
    print("modelscope_agent contents:", dir(modelscope_agent))
except ImportError:
    print("modelscope_agent: NOT FOUND")
