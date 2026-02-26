import modelscope_agent
import inspect

print("Checking RolePlay...")
try:
    from modelscope_agent.agents import RolePlay
    print("RolePlay found in modelscope_agent.agents")
except ImportError:
    print("RolePlay NOT found in modelscope_agent.agents")
    try:
        from modelscope_agent.agent import RolePlay
        print("RolePlay found in modelscope_agent.agent")
    except ImportError:
        print("RolePlay NOT found in modelscope_agent.agent")
        # List attributes of modelscope_agent.agent
        try:
            import modelscope_agent.agent
            print("Attributes of modelscope_agent.agent:", dir(modelscope_agent.agent))
        except:
            pass

print("\nChecking Tools...")
try:
    from modelscope_agent.tools.contrib.demo.agent_skills import ComputerTool
    print("ComputerTool found in contrib.demo.agent_skills")
except ImportError:
    print("ComputerTool NOT found in contrib.demo.agent_skills")
    # Try to find where tools are
    try:
        import modelscope_agent.tools
        print("Attributes of modelscope_agent.tools:", dir(modelscope_agent.tools))
    except:
        pass
