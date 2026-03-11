#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Skills 服务适配器
集成 ModelScope Agent 以支持 Anthropic Agent Skills (Computer Use, Bash, etc.)
"""

import logging
import json
import os
import shutil
import subprocess
import shlex
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.logger import logger
from app.services.skill_adapter import SkillAdapter

# 尝试导入 modelscope-agent，如果未安装则提供优雅降级
try:
    from modelscope_agent.agents import RolePlay
    from modelscope_agent.tools import BaseTool, register_tool, TOOL_REGISTRY
    MS_AGENT_AVAILABLE = True
    
    # --- Monkey Patch for Ollama LLM Bug ---
    # Fixes TypeError: unsupported operand type(s) for +: 'NoneType' and 'NoneType'
    try:
        from modelscope_agent.llm.ollama import OllamaLLM
        
        def safe_stat_last_call_token_info_stream(self, response):
            try:
                # Handle dictionary response
                prompt_tokens = response.get('prompt_eval_count')
                if prompt_tokens is None: prompt_tokens = 0
                
                completion_tokens = response.get('eval_count')
                if completion_tokens is None: completion_tokens = 0
                
                self.last_call_usage_info = {
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': prompt_tokens + completion_tokens
                }
                return response
            except AttributeError:
                # Handle generator response
                try:
                    for chunk in response:
                        # Safe dict access for chunk
                        if isinstance(chunk, dict):
                            prompt_tokens = chunk.get('prompt_eval_count')
                            if prompt_tokens is None: prompt_tokens = 0
                            
                            completion_tokens = chunk.get('eval_count')
                            if completion_tokens is None: completion_tokens = 0
                            
                            self.last_call_usage_info = {
                                'prompt_tokens': prompt_tokens,
                                'completion_tokens': completion_tokens,
                                'total_tokens': prompt_tokens + completion_tokens
                            }
                        yield chunk
                except Exception as e:
                    # Catch stream errors (like 502 Bad Gateway) to prevent crash
                    import logging
                    logging.getLogger(__name__).warning(f"Stream error in OllamaLLM patch: {e}")
                    # Optionally yield a final error chunk or just stop
                    return

        # Apply patch
        OllamaLLM.stat_last_call_token_info_stream = safe_stat_last_call_token_info_stream
        logger.info("Applied Monkey Patch for OllamaLLM.stat_last_call_token_info_stream")
        
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to patch OllamaLLM: {e}")
    # ---------------------------------------

except ImportError:
    logger.warning("modelscope-agent not installed. Agent Skills features will be disabled.")
    MS_AGENT_AVAILABLE = False
    RolePlay = object
    BaseTool = object
    def register_tool(name):
        def decorator(cls):
            return cls
        return decorator


if MS_AGENT_AVAILABLE:
    @register_tool('agent_skill_generator')
    class AgentSkillGeneratorTool(BaseTool):
        description = 'A tool to generate agent skill code structure'
        name = 'agent_skill_generator'
        parameters = [{
            'name': 'requirements',
            'type': 'string',
            'description': 'The requirements for the agent skill',
            'required': True
        }]
        
        def call(self, params: str, **kwargs) -> str:
            # 这是一个伪工具，引导 LLM 输出结构化数据
            # 实际上 LLM 会根据 Prompt 生成 JSON，而不仅是调用这个工具
            # 但既然我们要求 LLM 调用它，我们返回一个提示，让它把结果放在 tool output 或者直接输出
            return "Code structure generation context initialized. Please output the final JSON now."

else:
    class AgentSkillGeneratorTool:
        pass


class AgentSkillService:
    """
    Agent Skills 服务
    用于在 Executor Service 中加载和执行标准化工具
    """

    def __init__(self):
        self.available_skills = {}
        
        # 初始化 SkillAdapter
        # 硬编码路径以匹配用户环境
        root_path = Path(__file__).resolve().parents[2] / ".agents"
        self.skill_adapter = SkillAdapter(
            system_skills_path=str(root_path / "skills-system"),
            custom_skills_path=str(root_path / "skills-custom")
        )
        try:
            self.skill_adapter.load_skills()
        except Exception as e:
            logger.error(f"Failed to load skills via adapter: {e}")

        if MS_AGENT_AVAILABLE:
            self._register_default_skills()

    def _register_default_skills(self):
        """注册默认的 Agent Skills"""
        try:
            # 初始化标准工具集
            # 由于依赖版本变化，暂时只注册自定义生成器和基础工具
            self.available_skills = {
                "agent_skill_generator": AgentSkillGeneratorTool()
            }
            
            # 定义一个通用的资源工具类
            class ResourceSkillTool(BaseTool):
                def __init__(self, name: str, description: str, path: str):
                    self.name = name
                    self.path = path
                    self.parameters = []
                    self.description = description
                    
                    # Check for scripts
                    self.scripts_path = Path(path) / "scripts"
                    self.available_scripts = []
                    
                    if self.scripts_path.exists() and self.scripts_path.is_dir():
                        for script_file in self.scripts_path.iterdir():
                             if script_file.suffix in ['.py', '.sh', '.js', '.bat', '.ps1']:
                                 self.available_scripts.append(script_file.name)
                    
                    if self.available_scripts:
                        script_list = ", ".join(self.available_scripts)
                        self.description += f"\n\nAvailable executable scripts: {script_list}. To run a script, use the 'run_script' parameter."
                        
                        self.parameters.append({
                            'name': 'run_script',
                            'type': 'string',
                            'description': 'The name of the script to run (must be one of the available scripts)',
                            'required': False
                        })
                        self.parameters.append({
                            'name': 'args',
                            'type': 'string',
                            'description': 'Arguments for the script (as a space-separated string or JSON list)',
                            'required': False
                        })
                        
                    super().__init__()

                def call(self, params: str, **kwargs) -> str:
                    try:
                        params_dict = json.loads(params) if isinstance(params, str) else params
                    except json.JSONDecodeError:
                        params_dict = {}
                    
                    run_script = params_dict.get('run_script')
                    if run_script:
                        if run_script not in self.available_scripts:
                            return f"Error: Script '{run_script}' not found. Available: {self.available_scripts}"
                        
                        script_path = self.scripts_path / run_script
                        args = params_dict.get('args', '')
                        
                        # Prepare command
                        cmd = []
                        
                        # Determine interpreter
                        if script_path.suffix == '.py':
                            cmd = [sys.executable, str(script_path)]
                        elif script_path.suffix == '.sh':
                            cmd = ['bash', str(script_path)]
                        elif script_path.suffix == '.ps1':
                            cmd = ['powershell', '-File', str(script_path)]
                        else:
                             # Try direct execution
                             cmd = [str(script_path)]
                        
                        # Add arguments
                        if args:
                            if isinstance(args, list):
                                cmd.extend([str(a) for a in args])
                            else:
                                try:
                                    cmd.extend(shlex.split(args))
                                except:
                                    cmd.append(args) # Fallback
                        
                        try:
                            # Execute
                            # Default CWD to the parent of the skill directory (e.g., skills root)
                            cwd = Path(self.path).parent
                            if not cwd.exists():
                                cwd = Path(self.path)

                            logger.info(f"Executing script: {cmd} in {cwd}")
                            result = subprocess.run(
                                cmd, 
                                capture_output=True, 
                                text=True, 
                                check=False,
                                cwd=str(cwd)
                            )
                            return f"Script execution result:\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}\nExit Code: {result.returncode}"
                        except Exception as e:
                            return f"Error executing script: {e}"

                    return f"Skill resources for {self.name} are available at {self.path}. Please read SKILL.md for instructions."

            # 将 SkillAdapter 加载的技能也注册为 ResourceSkillTool (如果尚未存在)
            for skill in self.skill_adapter.list_skills():
                name = skill.get("name") or skill.get("id")
                if name and name not in self.available_skills:
                    path = skill.get("path", "")
                    # 读取代码文件以确定是否有可执行逻辑
                    code_files = self._read_skill_files(path)
                    
                    # 尝试动态加载（如果是有效的 Python 工具包）
                    # 只有当代码中明确包含了 modelscope-agent 的工具定义时才尝试加载为 Tool
                    # 否则，我们将其视为资源包 (ResourceSkillTool)
                    
                    is_executable = False
                    try:
                        files_map = json.loads(code_files)
                        # 检查 scripts 目录下是否有 .py 文件，且内容包含 register_tool
                        for fname, content in files_map.items():
                            if fname.endswith(".py") and "register_tool" in content:
                                # 这是一个可执行的 Skill
                                # 我们尝试加载它
                                # 注意：这需要复杂的动态加载逻辑（处理依赖等），这里做简化处理：
                                # 暂时不自动加载复杂的 Python 脚本，除非它们是单文件的
                                # 对于 skill-creator，它主要是文档和辅助脚本，我们将其作为 ResourceSkillTool 加载
                                # 但为了响应用户需求，我们检查是否有名为 'scripts/init_skill.py' 的文件，如果有，我们可以尝试暴露它
                                pass
                    except:
                        pass

                    # 默认作为 ResourceSkillTool 加载，这样 Agent 可以看到它
                    # 并能读取其描述 (SKILL.md)
                    desc = skill.get("description", "")
                    # 读取 SKILL.md 内容作为详细描述
                    skill_md_path = Path(path) / "SKILL.md"
                    if skill_md_path.exists():
                         try:
                             desc = skill_md_path.read_text(encoding="utf-8")[:2000] + "..."
                         except:
                             pass

                    self.available_skills[name] = ResourceSkillTool(name, desc, path)
                    
                    # 注册到 modelscope-agent 的全局注册表，以便 RolePlay 能够通过名称找到并使用该工具实例
                    # 注意：我们将实例作为 'class' 的值存入，这会触发 RolePlay 中的 TypeError 异常捕获逻辑，
                    # 从而直接使用该实例，而不是尝试实例化它。这是动态工具注册的关键 Hack。
                    TOOL_REGISTRY[name] = {'class': self.available_skills[name]}


            logger.info(f"Loaded {len(self.available_skills)} agent skills via modelscope-agent")
        except Exception as e:
            logger.error(f"Failed to register agent skills: {e}")

    def _read_skill_files(self, directory: str) -> str:
        """读取技能目录下的所有文件并返回 JSON 映射"""
        file_map = {}
        path_obj = Path(directory)
        if not path_obj.exists():
            return "{}"
            
        # 忽略的二进制和资源文件后缀
        ignored_extensions = {
            '.pyc', '.git', '.svn', '.DS_Store', 
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            '.ttf', '.woff', '.woff2', '.eot', '.otf', # Fonts
            '.mp3', '.mp4', '.avi', '.mov', '.wav', # Media
            '.zip', '.tar', '.gz', '.7z', '.rar', # Archives
            '.exe', '.dll', '.so', '.dylib', '.bin', '.obj', '.o', # Binaries
            '.pkl', '.model', '.onnx', '.pth', '.pt' # ML Models
        }
        
        # 单个文件大小限制 (1MB)，防止数据库字段溢出
        MAX_FILE_SIZE = 1 * 1024 * 1024 
        
        for root, _, files in os.walk(directory):
            for file in files:
                # 检查后缀
                _, ext = os.path.splitext(file)
                if ext.lower() in ignored_extensions or file.startswith('.') or '__pycache__' in root:
                    continue
                
                abs_path = Path(root) / file
                rel_path = abs_path.relative_to(path_obj).as_posix()
                
                # 检查大小
                try:
                    stats = abs_path.stat()
                    if stats.st_size > MAX_FILE_SIZE:
                        logger.warning(f"Skipping file {rel_path} because it is too large ({stats.st_size} bytes)")
                        continue
                        
                    content = abs_path.read_text(encoding='utf-8')
                    file_map[rel_path] = content
                except UnicodeDecodeError:
                    # 静默跳过二进制文件，不打印警告，避免刷屏
                    pass
                except Exception as e:
                    logger.warning(f"Failed to read file {abs_path}: {e}")
                    
        return json.dumps(file_map)

    def _path_code(self, path: str) -> str:
        return json.dumps({"__path__": path}, ensure_ascii=False)

    def _extract_path(self, code: Optional[str]) -> Optional[str]:
        if not code:
            return None
        try:
            data = json.loads(code)
            if isinstance(data, dict):
                path = data.get("__path__")
                if isinstance(path, str) and path:
                    return path
        except Exception:
            return None
        return None

    async def sync_skills_with_db(self, db: Any):
        """
        同步文件系统中的技能到数据库
        :param db: AsyncSession
        """
        from app.models import AgentTool
        from app.models.agent import ToolType
        from sqlalchemy import select
        
        file_skills = self.skill_adapter.list_skills()
        
        for skill in file_skills:
            name = skill.get("name") or skill.get("id")
            if not name:
                continue
                
            # 检查数据库
            query = select(AgentTool).where(AgentTool.name == name)
            result = await db.execute(query)
            db_tool = result.scalar_one_or_none()
            
            tool_type_raw = skill.get("tool_type", "custom")
            try:
                tool_type = ToolType(tool_type_raw)
            except Exception:
                tool_type = ToolType.CUSTOM
            is_builtin = skill.get("is_builtin", False)
            description = skill.get("description", "")
            path = skill.get("path", "")
            
            code_content = self._path_code(path)

            # 截断描述
            if len(description) > 1000:
                description = description[:997] + "..."
                
            if db_tool:
                # 更新元数据
                # 始终同步文件系统的代码到数据库，确保数据库是最新状态
                # 注意：这可能会覆盖用户在 UI 上的未保存修改，但考虑到 sync 通常在启动或列表刷新时发生
                # 且文件系统被视为 Source of Truth (对于 builtin) 或 持久化存储 (对于 custom)
                
                # 策略调整：如果是 built-in，强制同步。如果是 custom，如果 code 为空则同步。
                # 或者：始终同步，因为 Custom Skill 保存时也会写回文件系统（理论上应该这样，但目前还没看保存逻辑）
                # 暂时策略：如果 db_tool.code 为空 或者 是 built-in，则更新。
                
                update_needed = False
                if db_tool.is_builtin != is_builtin:
                    db_tool.is_builtin = is_builtin
                    update_needed = True
                
                if db_tool.tool_type != tool_type:
                    db_tool.tool_type = tool_type
                    update_needed = True
                    
                if db_tool.description != description:
                    db_tool.description = description
                    update_needed = True
                if db_tool.code != code_content:
                    db_tool.code = code_content
                    update_needed = True
                
                if update_needed:
                    db.add(db_tool)
            else:
                # 创建新技能
                new_tool = AgentTool(
                    name=name,
                    display_name=name,
                    description=description,
                    tool_type=tool_type,
                    is_builtin=is_builtin,
                    is_enabled=True, # 默认启用
                    config_schema={},
                    default_config={},
                    code=code_content
                )
                db.add(new_tool)
        
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to sync skills to DB: {e}")

    def _deploy_skill_files(self, name: str, files: Dict[str, str]) -> str:
        """
        部署技能文件到工作区
        返回部署路径
        """
        # 默认工作区
        workspace_root = Path(os.getcwd()) / "workspace" / "skills"
        skill_dir = workspace_root / name
        
        if skill_dir.exists():
            try:
                shutil.rmtree(skill_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup skill dir {skill_dir}: {e}")
        
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        for rel_path, content in files.items():
            # 安全检查：防止路径遍历
            if ".." in rel_path or rel_path.startswith("/") or rel_path.startswith("\\"):
                logger.warning(f"Skipping unsafe path {rel_path} in skill {name}")
                continue
                
            file_path = skill_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Failed to write file {file_path}: {e}")
                
        return str(skill_dir.absolute())

    def load_tool_from_code(self, name: str, code: str) -> Any:
        """
        从代码动态加载工具
        支持 Python 代码类定义或 JSON 文件包结构
        """
        # 1. 尝试作为文件包加载
        try:
            files = json.loads(code)
            # 简单的启发式检查：如果是字典且值都是字符串，认为是文件包
            if isinstance(files, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in files.items()):
                deploy_path = self._deploy_skill_files(name, files)
                logger.info(f"Deployed skill {name} files to {deploy_path}")
                
                # 创建一个通用资源工具
                # 将 SKILL.md 内容放入描述中，以便 LLM 感知
                skill_desc = files.get('SKILL.md', f"Skill resources for {name}")
                # 截断描述防止过长
                if len(skill_desc) > 2000:
                    skill_desc = skill_desc[:2000] + "...(truncated)"
                
                description = f"{skill_desc}\n\nResources are located at: {deploy_path}"
                
                class ResourceSkillTool:
                    def __init__(self, tool_name, tool_desc, path):
                        self.name = tool_name
                        self.description = tool_desc
                        self.path = path
                        self.parameters = []
                        
                    def __call__(self, *args, **kwargs):
                        return f"Skill resources are available at {self.path}"
                
                instance = ResourceSkillTool(name, description, deploy_path)
                self.available_skills[name] = instance
                return instance
                
        except (json.JSONDecodeError, TypeError):
            # 不是 JSON 或格式不符，继续按 Python 代码处理
            pass

        try:
            # 2. 原有的 Python 代码加载逻辑
            # 创建隔离的命名空间
            local_scope = {}
            # 执行代码
            exec(code, {}, local_scope)
            
            # 查找代码中定义的工具类
            # 假设工具类是代码中定义的某个类，或者有一个特定的变量指向它
            # 这里简单假设代码中定义了一个名为 ToolClass 的类，或者与 name 匹配的类
            
            tool_class = None
            for key, value in local_scope.items():
                if isinstance(value, type) and key != 'Tool' and key != 'object':
                    # 也可以检查是否继承自特定的基类
                    tool_class = value
                    break
            
            if tool_class:
                instance = tool_class()
                self.available_skills[name] = instance
                return instance
            else:
                logger.warning(f"No tool class found in code for {name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load tool from code {name}: {e}")
            return None

    def get_skill_tools(self, skill_names: List[str] = None) -> List[Any]:
        """
        获取指定的工具实例列表
        
        Args:
            skill_names: 需要启用的技能名称列表。如果为 None，则返回所有可用技能；如果为空列表 []，则返回空。
        """
        if not MS_AGENT_AVAILABLE:
            return []

        if skill_names is None:
            return list(self.available_skills.values())
        
        if len(skill_names) == 0:
            return []

        tools = []
        for name in skill_names:
            if name in self.available_skills:
                tools.append(self.available_skills[name])
            else:
                logger.warning(f"Skill {name} not found")
        return tools

    def save_or_update_custom_skill(self, name: str, code_json: str) -> Optional[str]:
        try:
            files = json.loads(code_json) if isinstance(code_json, str) else code_json
            if not isinstance(files, dict):
                return None
            target_dir = Path(self.skill_adapter.custom_skills_path) / name
            if target_dir.exists():
                try:
                    shutil.rmtree(target_dir)
                except Exception as e:
                    logger.warning(f"Cleanup failed for {target_dir}: {e}")
            target_dir.mkdir(parents=True, exist_ok=True)
            for rel_path, content in files.items():
                if ".." in rel_path or rel_path.startswith("/") or rel_path.startswith("\\"):
                    continue
                file_path = target_dir / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    logger.error(f"Write failed {file_path}: {e}")
            skill_md = target_dir / "SKILL.md"
            if not skill_md.exists():
                try:
                    with open(skill_md, "w", encoding="utf-8") as f:
                        f.write(f"---\nname: {name}\n---\n\n# {name}\n")
                except Exception as e:
                    logger.warning(f"SKILL.md init failed for {name}: {e}")
            try:
                self.skill_adapter.load_skills()
            except Exception as e:
                logger.warning(f"Reload skills failed: {e}")
            skill_info = self.skill_adapter.get_skill(name)
            if not skill_info:
                return None
            if MS_AGENT_AVAILABLE:
                class ResourceSkillTool(BaseTool):
                    def __init__(self, n: str, d: str, p: str):
                        self.name = n
                        self.description = d
                        self.path = p
                        self.parameters = []
                        super().__init__()
                    def call(self, params: str, **kwargs) -> str:
                        return f"Skill resources for {self.name} at {self.path}"
                desc = skill_info.get("description", "") or ""
                path = skill_info.get("path", "")
                self.available_skills[name] = ResourceSkillTool(name, desc, path)
                try:
                    TOOL_REGISTRY[name] = {'class': self.available_skills[name]}
                except Exception:
                    pass
            return path
        except Exception as e:
            logger.error(f"Save custom skill failed for {name}: {e}")
            return None

    async def execute_skill_task(
        self, 
        prompt: str, 
        model_config: Dict[str, Any],
        enabled_skills: List[str] = None
    ) -> str:
        """
        执行带有 Skills 的任务
        
        Args:
            prompt: 用户指令
            model_config: 模型配置 (包含 api_key, model_name 等)
            enabled_skills: 启用的技能列表
        """
        if not MS_AGENT_AVAILABLE:
            return "Error: modelscope-agent library is not installed."

        try:
            # 1. 准备工具
            tools = self.get_skill_tools(enabled_skills)
            
            # 2. 初始化 Agent (使用 ModelScope 的 RolePlay 或 ReAct 代理)
            # 注意：这里适配 ModelScope 的配置格式
            llm_config = {
                'model': model_config.get('model_name', 'qwen-max'),
                'api_key': model_config.get('api_key'),
                'model_server': model_config.get('provider', 'dashscope'),
            }
            
            # 适配不同 Provider 的配置
            base_url = model_config.get('base_url') or model_config.get('api_endpoint')
            provider = model_config.get('provider', 'dashscope')
            
            if base_url:
                if provider == 'ollama':
                    # Ollama 需要 host 参数，且通常不需要 /api/chat 后缀
                    import re
                    # 移除 /api/chat 或 /api/generate 后缀
                    host = re.sub(r'/api/(chat|generate)$', '', base_url)
                    llm_config['host'] = host
                    llm_config['base_url'] = host # 保险起见保留
                elif provider == 'openai':
                    # OpenAI 需要 api_base 参数
                    llm_config['api_base'] = base_url
                    llm_config['base_url'] = base_url
                else:
                    llm_config['base_url'] = base_url
                    llm_config['api_base'] = base_url

            bot = RolePlay(
                function_list=[t.name for t in tools], # 传递工具名称
                llm=llm_config,
                instruction=prompt
            )

            # 3. 执行任务
            # ms-agent 通常是同步或基于生成器的，这里根据实际情况可能需要 run_in_executor
            # 某些 LLM（如 Ollama）可能会因为 stream 问题报错，尝试禁用 stream 或处理 stream
            # 但 RolePlay 默认好像是 stream 的。
            
            # 修复 AgentLogger debug 属性缺失的问题 (Monkey Patch)
            import logging
            from modelscope_agent.utils.logger import agent_logger
            if not hasattr(agent_logger, 'debug'):
                agent_logger.debug = agent_logger.info
            
            # 使用 asyncio.to_thread 在后台线程中运行阻塞的 bot.run，防止阻塞 FastAPI 主事件循环
            import asyncio
            response = await asyncio.to_thread(bot.run, prompt)
            
            # 处理生成器返回
            final_result = ""
            for chunk in response:
                # 检查是否有错误信息
                # 有些时候 chunk 是字符串
                if isinstance(chunk, str):
                    final_result += chunk
                elif isinstance(chunk, dict):
                    final_result += chunk.get('content') or ''
                
            return final_result

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Error executing skill task: {e}\n{tb}")
            return f"Execution failed: {str(e)}\nTraceback: {tb}"

# 全局单例
agent_skill_service = AgentSkillService()

