import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List
from openai import OpenAI
from context_manager import ContextManager
from skill_executor import SkillExecutor
from skills import get_tools_definition
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")


class BookReviewAgent:
    """图书审读Agent（使用本地大模型，兼容 OpenAI 接口）"""

    def __init__(self, llm_base_url: str = None, llm_api_key: str = None, llm_model: str = None):
        base_url = llm_base_url or LLM_BASE_URL
        api_key = llm_api_key or LLM_API_KEY
        self.model = llm_model or LLM_MODEL
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.context_manager = ContextManager()
        self.skill_executor = None
        self.conversation_history = []

    def initialize(self):
        """初始化Agent，验证数据库连通性"""
        print("初始化图书审读Agent...")
        self.context_manager.load_knowledge_base()

        self.skill_executor = SkillExecutor(
            mysql=self.context_manager.mysql,
            doris=self.context_manager.doris,
        )

        print(f"Agent初始化完成 (模型: {self.model})")

    def review_book(self, book_content: str, book_title: str = "未命名", allowed_skills: List[str] = None, save_report: bool = True) -> Dict[str, Any]:
        """审读图书，完成后将结果上传到 MinIO
        
        allowed_skills: 允许使用的技能名称列表，None 表示使用全部技能，空列表表示不使用任何技能
        save_report: 是否保存报告到 MinIO/本地，False 时跳过保存（适用于 API 调用场景）
        """
        print(f"\n开始审读: {book_title}")
        print("=" * 60)

        user_message = f"""请对以下图书内容进行审读：

【图书标题】{book_title}

【内容】
{book_content}

请基于已有的敏感词库和审读规则库进行分析，并在必要时调用相应的技能进行深度检查。"""

        self.conversation_history = []
        self._last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        response = self._agentic_loop(user_message, allowed_skills=allowed_skills)

        report_path = ""
        if save_report:
            report_path = self._save_report(book_title, response)

        return {
            "title": book_title,
            "status": "completed",
            "response": response,
            "report_path": report_path,
            "conversation_turns": len(self.conversation_history),
            "usage": self._last_usage,
        }

    def _save_report(self, book_title: str, content: str) -> str:
        """将审读结果上传到 MinIO，返回对象路径"""
        from minio_storage import get_minio_storage

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in book_title if c not in r'\/:*?"\u003c\u003e|').strip()[:50]
        filename = f"{timestamp}_{safe_title}.md"

        md_content = f"""
{content}

---

> 最终结论等级说明：critical（极高风险）> high（高风险）> medium（中风险）> low（低风险）> safe（安全）
"""
        try:
            storage = get_minio_storage()
            object_path = storage.upload_report(filename, md_content)
            print(f"\n报告已上传到 MinIO: {object_path}")
            return object_path
        except Exception as e:
            # MinIO 上传失败时回退到本地保存
            print(f"\nMinIO 上传失败({e})，回退到本地保存...")
            os.makedirs(REPORT_DIR, exist_ok=True)
            filepath = os.path.join(REPORT_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_content)
            print(f"报告已保存到本地: {filepath}")
            return filepath

    def _parse_text_tool_calls(self, text: str) -> List[tuple]:
        """解析模型以纯文本输出的 <tool_call> XML，返回 [(name, input_dict), ...]"""
        if "<tool_call>" not in text and "<function=" not in text:
            return []

        results = []

        # 格式一：<tool_call>\n<function=name>\n<parameter=k>v</parameter>\n</function>\n</tool_call>
        pattern_func = re.compile(
            r"<tool_call>\s*<function=(\S+?)>\s*(.*?)\s*</function>\s*</tool_call>",
            re.DOTALL
        )
        for m in pattern_func.finditer(text):
            name = m.group(1).strip()
            body = m.group(2)
            params = {}
            for pm in re.finditer(r"<parameter=(\w+)>\s*(.*?)\s*</parameter>", body, re.DOTALL):
                params[pm.group(1)] = pm.group(2).strip()
            # 尝试将字符串值转换为合适类型
            params = self._coerce_param_types(params)
            results.append((name, params))

        if results:
            return results

        # 格式二：<tool_call>{"name": "...", "arguments": {...}}</tool_call>
        pattern_json = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
        for m in pattern_json.finditer(text):
            try:
                obj = json.loads(m.group(1))
                name = obj.get("name") or obj.get("function", {}).get("name", "")
                args = obj.get("arguments") or obj.get("parameters") or {}
                if isinstance(args, str):
                    args = json.loads(args)
                if name:
                    results.append((name, args))
            except (json.JSONDecodeError, KeyError):
                pass

        return results

    @staticmethod
    def _coerce_param_types(params: dict) -> dict:
        """将字符串参数值尝试转换为 bool/int/float"""
        coerced = {}
        for k, v in params.items():
            if isinstance(v, str):
                if v.lower() == "true":
                    coerced[k] = True
                elif v.lower() == "false":
                    coerced[k] = False
                else:
                    try:
                        coerced[k] = int(v)
                    except ValueError:
                        try:
                            coerced[k] = float(v)
                        except ValueError:
                            coerced[k] = v
            else:
                coerced[k] = v
        return coerced

    def _build_openai_tools(self, allowed_skills: List[str] = None) -> List[Dict[str, Any]]:
        """将技能定义转换为 OpenAI tools 格式，支持按名称过滤"""
        tools = []
        for tool in get_tools_definition():
            if allowed_skills is not None and tool["name"] not in allowed_skills:
                continue
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        return tools

    def _agentic_loop(self, user_message: str, max_iterations: int = 20, allowed_skills: List[str] = None) -> str:
        """Agent循环：处理消息、调用技能、返回结果
        
        allowed_skills: 允许使用的技能名称列表，None 表示使用全部技能，空列表表示不使用任何技能
        """

        self.conversation_history = [
            {"role": "system", "content": self.context_manager.get_system_prompt()},
            {"role": "user", "content": user_message}
        ]

        # 如果限定了技能列表，在 system prompt 末尾追加强制约束
        if allowed_skills is not None:
            if allowed_skills:
                skill_list = "、".join(allowed_skills)
                constraint = f"\n\n【重要限制】本次审读只允许调用以下技能：{skill_list}。严禁调用其他任何工具，否则将视为违规。"
            else:
                constraint = "\n\n【重要限制】本次审读不允许调用任何工具，请直接根据已知信息生成审读报告。"
            self.conversation_history[0]["content"] += constraint

        tools = self._build_openai_tools(allowed_skills=allowed_skills)
        # 不传 tool_choice，由服务端决定默认行为（兼容 SGLang/vLLM 未开启 auto-tool-choice 的情况）
        tool_choice = None
        iteration = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n[迭代 {iteration}]")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                **(({
                    "tools": tools,
                    "extra_body": {"tool_choice": None},
                }) if tools else {}),
            )

            # 累计 token 用量
            if response.usage:
                total_prompt_tokens += response.usage.prompt_tokens or 0
                total_completion_tokens += response.usage.completion_tokens or 0

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            self.conversation_history.append(message.model_dump(exclude_unset=False))

            if finish_reason == "tool_calls" and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_input = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_input = {}

                    print(f"  调用技能: {tool_name}")
                    print(f"  输入: {json.dumps(tool_input, ensure_ascii=False, indent=2)}")

                    result = self.skill_executor.execute(tool_name, tool_input)

                    print(f"  结果: {json.dumps(result, ensure_ascii=False)[:200]}...")

                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

            elif finish_reason == "stop":
                final_response = message.content or ""

                # 检测模型以纯文本形式输出 <tool_call> 标签的情况
                # （部分推理服务/模型不通过 finish_reason=tool_calls 触发工具调用）
                parsed_calls = self._parse_text_tool_calls(final_response)
                if parsed_calls:
                    # 移除对话历史中刚追加的那条消息，替换为包含 tool_calls 的结构
                    self.conversation_history.pop()
                    # 构造一个虚拟的 assistant tool_calls 消息追加到历史
                    fake_tool_calls = []
                    for idx, (tc_name, tc_input) in enumerate(parsed_calls):
                        fake_tool_calls.append({
                            "id": f"call_text_{iteration}_{idx}",
                            "type": "function",
                            "function": {"name": tc_name, "arguments": json.dumps(tc_input, ensure_ascii=False)}
                        })
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": fake_tool_calls,
                    })
                    for tc in fake_tool_calls:
                        tc_name = tc["function"]["name"]
                        tc_input = json.loads(tc["function"]["arguments"])
                        print(f"  调用技能(文本解析): {tc_name}")
                        print(f"  输入: {json.dumps(tc_input, ensure_ascii=False, indent=2)}")
                        result = self.skill_executor.execute(tc_name, tc_input)
                        print(f"  结果: {json.dumps(result, ensure_ascii=False)[:200]}...")
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": tc_name,
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                    # 继续循环，让模型根据工具结果生成报告
                    continue

                print(f"Agent完成 (共{iteration}次迭代, prompt_tokens={total_prompt_tokens}, completion_tokens={total_completion_tokens})")
                self._last_usage = {
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "total_tokens": total_prompt_tokens + total_completion_tokens,
                }
                return final_response

            else:
                print(f"未知的停止原因: {finish_reason}")
                break

        # 达到最大迭代次数：追加一条催促消息，让模型直接输出报告
        print(f"已达到最大迭代次数({max_iterations})，请求模型生成最终报告...")
        self.conversation_history.append({
            "role": "user",
            "content": (
                "你已完成所有必要的查询，请立即根据以上已获取的所有信息，"
                "直接生成完整的图书审读报告，必须包含最终审读结论等级"
                "（critical / high / medium / low / safe 中选一个）。"
                "不要再调用任何工具。"
            )
        })
        try:
            final_resp = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
            )
            return final_resp.choices[0].message.content or "达到最大迭代次数，模型未返回内容"
        except Exception as e:
            return f"达到最大迭代次数，生成报告失败: {e}"

    def interactive_review(self):
        """交互式审读模式"""
        print("\n进入交互式审读模式")
        print("输入 'quit' 退出\n")

        self.conversation_history = [
            {"role": "system", "content": self.context_manager.get_system_prompt()}
        ]
        tools = self._build_openai_tools()

        while True:
            user_input = input("你: ").strip()
            if user_input.lower() == "quit":
                print("再见！")
                break
            if not user_input:
                continue

            self.conversation_history.append({"role": "user", "content": user_input})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                **(({
                    "tools": tools,
                    "extra_body": {"tool_choice": None},
                }) if tools else {}),
            )

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason
            self.conversation_history.append(message.model_dump(exclude_unset=False))

            if finish_reason == "tool_calls" and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_input = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_input = {}

                    print(f"  调用技能: {tool_name}")
                    result = self.skill_executor.execute(tool_name, tool_input)

                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

                followup = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                )
                final = followup.choices[0].message
                self.conversation_history.append(final.model_dump(exclude_unset=False))
                print(f"\nAgent: {final.content}\n")
            else:
                print(f"\nAgent: {message.content}\n")
