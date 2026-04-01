#!/usr/bin/env python3
"""
图书审读Agent - HTTP API 服务

启动方式:
  uvicorn api:app --host 0.0.0.0 --port 5080 --workers 2
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import re
import uuid
import time
from datetime import datetime

from agent import BookReviewAgent
from main import parse_metadata

app = FastAPI(
    title="图书审读Agent API",
    description="基于大模型的图书敏感内容审读服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局默认 Agent 实例（无自定义 LLM 配置时复用）
_default_agent: Optional[BookReviewAgent] = None


def get_agent(
    llm_base_url: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    llm_model: Optional[str] = None,
) -> BookReviewAgent:
    global _default_agent
    if llm_base_url or llm_api_key or llm_model:
        agent = BookReviewAgent(
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            llm_model=llm_model,
        )
        agent.initialize()
        return agent
    if _default_agent is None:
        _default_agent = BookReviewAgent()
        _default_agent.initialize()
    return _default_agent


CONCLUSION_MAP = {
    "critical": "critical（极高风险）",
    "high": "high（高风险）",
    "medium": "medium（中风险）",
    "low": "low（低风险）",
    "safe": "safe（安全）",
}


def extract_conclusion(report: str) -> str:
    pattern = re.compile(
        r'最终审读结论[\uff1a:\s*\*]*(critical|high|medium|low|safe)',
        re.IGNORECASE
    )
    m = pattern.search(report)
    if m:
        return CONCLUSION_MAP.get(m.group(1).lower(), m.group(1).lower())
    return ""


def build_short_report(report: str, conclusion: str) -> str:
    """从完整报告中提取简短摘要，供 API 返回使用。
    只保留三类核心信息：最终结论、历史审读结论、敏感词命中情况。
    """
    parts = []

    # 1. 最终审读结论
    if conclusion:
        parts.append(f"最终审读结论：{conclusion}")

    # 2. 历史审读结论
    history_pattern = re.compile(
        r'(实物禁发|电子禁发|采集禁发|客户禁发|实物限阅|采集限阅|客户限阅'
        r'|实物通过|电子通过|订单通过|文章通过|电子问题|敏感文章)'
    )
    history_matches = list(dict.fromkeys(history_pattern.findall(report)))
    if history_matches:
        parts.append("历史审读：" + "、".join(history_matches[:3]))
    elif re.search(r'(无历史|未查询到|无记录|没有历史|未找到)', report):
        parts.append("历史审读：无历史记录")

    # 3. 敏感词命中情况
    level_pattern = re.compile(r'[Ss]([1-5])')
    levels = [int(x) for x in level_pattern.findall(report)]
    hit_count_m = re.search(r'命中\s*([\d]+)\s*[条个]', report)
    if hit_count_m:
        hit_count = hit_count_m.group(1)
        highest = f"S{min(levels)}" if levels else ""
        parts.append(f"敏感词：命中 {hit_count} 条" + (f"，最高等级 {highest}" if highest else ""))
    elif re.search(r'(未命中|未发现|未检测到|无敏感词|0\s*条)', report):
        parts.append("敏感词：未命中")

    if not parts:
        clean = re.sub(r'[*_`#>|\-=]+', '', report).strip()
        return clean[:80]

    return "；".join(parts)


# -------------------------------------------------------------------
# 请求/响应模型
# -------------------------------------------------------------------

ALL_SKILLS = [
    "query_sensitive_words",
    "sensitive_words_check",
    "query_book_review",
    "pdf_parse",
    "image_analysis",
]


class ReviewRequest(BaseModel):
    content: str = Field(..., description="审读内容或结构化元数据（如 'ISBN:xxx,正题名:yyy,作者:zzz,出版社:www'）")
    title: Optional[str] = Field(None, description="图书标题（可选，自动从元数据中提取）")
    llm_base_url: Optional[str] = Field(None, description="大模型 API 地址，不填则使用服务默认配置")
    llm_api_key: Optional[str] = Field(None, description="大模型 API Key，不填则使用服务默认配置")
    llm_model: Optional[str] = Field(None, description="大模型名称，不填则使用服务默认配置")
    skills: Optional[List[str]] = Field(
        None,
        description=(
            "允许使用的技能名称列表。不传或传 null 则使用全部技能；传空列表 [] 则不使用任何技能。"
            "可选值：query_sensitive_words / sensitive_words_check / query_book_review / pdf_parse / image_analysis"
        )
    )


class ReviewResponse(BaseModel):
    request_id: str
    status: str
    title: str
    conclusion: str = Field("", description="最终审读结论等级")
    report: str = Field("", description="审读摘要信息")
    report_path: str = Field("", description="报告在 MinIO 中的对象路径（API调用时为空）")
    duration_seconds: float
    timestamp: str
    model_used: str = Field("", description="本次审读使用的大模型名称")
    skills_used: List[str] = Field([], description="本次审读开放的技能列表")
    prompt_tokens: int = Field(0, description="输入 token 总量（所有迭代累计）")
    completion_tokens: int = Field(0, description="输出 token 总量（所有迭代累计）")
    total_tokens: int = Field(0, description="总 token 用量")


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model: str


# -------------------------------------------------------------------
# 接口
# -------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, summary="健康检查")
def health_check():
    agent = get_agent()
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat(),
        model=agent.model
    )


@app.post("/review", response_model=ReviewResponse, summary="图书审读")
def review_book(req: ReviewRequest):
    """
    提交图书审读请求。

    - **content**: 结构化元数据字符串或普通文本内容。
    - **title**: 可选，图书标题。
    - **llm_base_url / llm_api_key / llm_model**: 可选，自定义大模型配置。
    - **skills**: 可选，指定允许使用的技能列表。
    """
    request_id = str(uuid.uuid4())[:8]
    start = time.time()

    try:
        agent = get_agent(
            llm_base_url=req.llm_base_url,
            llm_api_key=req.llm_api_key,
            llm_model=req.llm_model,
        )
        content, auto_title = parse_metadata(req.content)
        title = req.title or auto_title

        allowed_skills = req.skills
        skills_used = allowed_skills if allowed_skills is not None else ALL_SKILLS

        result = agent.review_book(content, title, allowed_skills=allowed_skills, save_report=False)
        duration = round(time.time() - start, 2)
        report_text = result["response"]
        usage = result.get("usage", {})
        conclusion = extract_conclusion(report_text)

        return ReviewResponse(
            request_id=request_id,
            status="completed",
            title=title,
            conclusion=conclusion,
            report=build_short_report(report_text, conclusion),
            report_path="",
            duration_seconds=duration,
            timestamp=datetime.now().isoformat(),
            model_used=agent.model,
            skills_used=skills_used,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/review/pdf", response_model=ReviewResponse, summary="PDF文件审读")
def review_pdf(
    pdf_path: str,
    llm_base_url: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    llm_model: Optional[str] = None,
):
    """
    对指定路径的 PDF 文件进行审读（服务器本地路径）。
    """
    request_id = str(uuid.uuid4())[:8]
    start = time.time()

    try:
        agent = get_agent(
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            llm_model=llm_model,
        )
        content = f"请审读以下PDF文件: {pdf_path}"
        result = agent.review_book(content, f"PDF: {pdf_path}", save_report=False)
        duration = round(time.time() - start, 2)
        report_text = result["response"]
        usage = result.get("usage", {})
        conclusion = extract_conclusion(report_text)

        return ReviewResponse(
            request_id=request_id,
            status="completed",
            title=f"PDF: {pdf_path}",
            conclusion=conclusion,
            report=build_short_report(report_text, conclusion),
            report_path="",
            duration_seconds=duration,
            timestamp=datetime.now().isoformat(),
            model_used=agent.model,
            skills_used=ALL_SKILLS,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
