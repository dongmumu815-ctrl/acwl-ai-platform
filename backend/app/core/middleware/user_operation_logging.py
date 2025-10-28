#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户操作日志中间件

将每个请求的关键信息（用户、方法、路径、状态码、耗时、IP等）
写入 user_operation_logs 与 user_operation_log_details 表，用于后续查询展示。
"""
import json
import time
import uuid
import traceback
import socket
import os
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response
from starlette.concurrency import iterate_in_threadpool

from sqlalchemy import text

from app.core.database import get_db_context
from app.core.security import decode_access_token
from app.core.logger import get_logger

logger = get_logger(__name__)


class UserOperationLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    def _extract_module_from_path(self, path: str) -> str:
        """从请求路径中提取模块名称，返回中文标签"""
        if not path or path == "/":
            return "首页"
        
        # 移除查询参数
        path = path.split('?')[0]
        
        # 按 / 分割路径
        parts = [p for p in path.split('/') if p]
        
        if not parts:
            return "首页"
        
        # 路径到中文标签的映射
        path_to_label = {
            # API 相关
            "api/v1/auth": "用户认证",
            "api/v1/users": "用户管理",
            "api/v1/user_operation_logs": "操作日志",
            "api/v1/data_resources": "数据资源",
            "api/v1/datasources": "数据源管理",
            "api/v1/templates": "模板管理",
            "api/v1/tags": "标签管理",
            "api/v1/permissions": "权限管理",
            "api/v1/system": "系统管理",
            "api/v1/dashboard": "仪表盘",
            "api/v1/reports": "报表管理",
            "api/v1/analytics": "数据分析",
            "api/v1/settings": "系统设置",
            "api/v1/es/aggregations": "仪表盘",
            "api/v1/es/templates": "中心表查询",
            "api/v1/es/query": "查询操作",
            "api/v1/resource-packages/2/generate-excel": "生成资源包",
            "api/v1/resource-packages/2/download-latest": "下载资源包",
            
            # 前端页面路径
            "login": "登录页面",
            "dashboard": "仪表盘",
            "users": "用户管理",
            "data-resources": "数据资源",
            "datasources": "数据源管理",
            "templates": "模板管理",
            "tags": "标签管理",
            "permissions": "权限管理",
            "system": "系统管理",
            "reports": "报表管理",
            "analytics": "数据分析",
            "settings": "系统设置",
            "profile": "个人资料",
            "logs": "操作日志",
        }
        
        # 尝试匹配完整路径
        full_path = "/".join(parts)
        if full_path in path_to_label:
            return path_to_label[full_path]
        
        # 尝试匹配前缀路径
        for path_prefix, label in path_to_label.items():
            if full_path.startswith(path_prefix):
                return label
        
        # 根据第一级路径判断
        first_part = parts[0]
        if first_part == "api":
            if len(parts) >= 3:
                # API 路径，取第三部分作为模块名
                module_name = parts[2]
                module_mapping = {
                     "auth": "用户认证",
                     "users": "用户管理",
                     "user_operation_logs": "操作日志",
                     "data_resources": "数据资源",
                     "data-resources": "数据资源",
                     "data_resource_types": "数据资源类型",
                     "data-resource-types": "数据资源类型",
                     "datasources": "数据源管理",
                     "templates": "模板管理",
                     "tags": "标签管理",
                     "permissions": "权限管理",
                     "system": "系统管理",
                     "dashboard": "仪表盘",
                     "reports": "报表管理",
                     "analytics": "数据分析",
                     "settings": "系统设置",
                     "apis": "接口管理",
                     "customers": "客户管理",
                     "resource-packages": "资源包管理",
                     "resource_packages": "资源包管理",
                     "es": "搜索引擎",
                     "elasticsearch": "搜索引擎",
                     "search": "搜索功能",
                     "stats": "统计分析",
                     "statistics": "统计分析",
                     "upload": "文件上传",
                     "download": "文件下载",
                     "export": "数据导出",
                     "import": "数据导入",
                     "backup": "数据备份",
                     "restore": "数据恢复",
                     "monitor": "系统监控",
                     "health": "健康检查",
                     "status": "状态查询",
                     "config": "配置管理",
                     "logs": "日志管理",
                     "audit": "审计日志",
                     "notification": "消息通知",
                     "workflow": "工作流程",
                     "task": "任务管理",
                     "job": "作业管理",
                     "schedule": "调度管理",
                     "queue": "队列管理",
                     "cache": "缓存管理",
                     "session": "会话管理",
                     "token": "令牌管理",
                     "oauth": "第三方认证",
                     "sso": "单点登录",
                     "profile": "个人资料",
                     "account": "账户管理",
                     "role": "角色管理",
                     "group": "用户组管理",
                     "organization": "组织管理",
                     "department": "部门管理",
                     "project": "项目管理",
                     "workspace": "工作空间",
                     "file": "文件管理",
                     "folder": "文件夹管理",
                     "document": "文档管理",
                     "image": "图片管理",
                     "video": "视频管理",
                     "audio": "音频管理",
                     "media": "媒体管理",
                     "api": "接口管理",
                     "webhook": "回调接口",
                     "integration": "系统集成",
                     "plugin": "插件管理",
                     "extension": "扩展管理",
                     "theme": "主题管理",
                     "language": "语言设置",
                     "locale": "本地化设置",
                     "timezone": "时区设置",
                     "currency": "货币设置",
                     "unit": "单位设置",
                     "format": "格式设置",
                     "validation": "数据验证",
                     "security": "安全管理",
                     "encryption": "加密管理",
                     "certificate": "证书管理",
                     "license": "许可证管理",
                     "version": "版本管理",
                     "update": "系统更新",
                     "patch": "补丁管理",
                     "maintenance": "系统维护",
                     "cleanup": "数据清理",
                     "optimize": "性能优化",
                     "debug": "调试工具",
                     "test": "测试工具",
                     "mock": "模拟数据",
                     "sample": "示例数据",
                     "demo": "演示功能",
                     "help": "帮助文档",
                     "support": "技术支持",
                     "feedback": "用户反馈",
                     "survey": "问卷调查",
                     "rating": "评分系统",
                     "comment": "评论管理",
                     "review": "审核管理",
                     "approval": "审批流程",
                     "workflow": "工作流",
                     "process": "流程管理",
                     "step": "步骤管理",
                     "stage": "阶段管理",
                     "phase": "阶段管理",
                     "milestone": "里程碑",
                     "deadline": "截止日期",
                     "calendar": "日历管理",
                     "event": "事件管理",
                     "reminder": "提醒功能",
                     "alert": "告警管理",
                     "warning": "警告信息",
                     "error": "错误处理",
                     "exception": "异常处理",
                     "log": "日志记录",
                     "trace": "链路追踪",
                     "metric": "指标监控",
                     "performance": "性能监控",
                     "resource": "资源监控",
                     "capacity": "容量管理",
                     "quota": "配额管理",
                     "limit": "限制管理",
                     "threshold": "阈值管理",
                     "rule": "规则管理",
                     "policy": "策略管理",
                     "filter": "过滤器",
                     "sort": "排序功能",
                     "search": "搜索功能",
                     "query": "查询功能",
                     "browse": "浏览功能",
                     "view": "查看功能",
                     "edit": "编辑功能",
                     "create": "创建功能",
                     "delete": "删除功能",
                     "update": "更新功能",
                     "modify": "修改功能",
                     "copy": "复制功能",
                     "move": "移动功能",
                     "rename": "重命名功能",
                     "share": "分享功能",
                     "publish": "发布功能",
                     "unpublish": "取消发布",
                     "archive": "归档功能",
                     "restore": "恢复功能",
                     "recycle": "回收站",
                     "trash": "垃圾箱",
                     "favorite": "收藏功能",
                     "bookmark": "书签管理",
                     "history": "历史记录",
                     "recent": "最近访问",
                     "popular": "热门内容",
                     "trending": "趋势分析",
                     "recommend": "推荐系统",
                     "suggest": "建议功能",
                     "auto": "自动化",
                     "manual": "手动操作",
                     "batch": "批量操作",
                     "bulk": "批量处理",
                     "mass": "批量管理",
                     "multi": "多选操作",
                     "single": "单选操作",
                     "all": "全选操作",
                     "none": "取消选择",
                     "select": "选择功能",
                     "pick": "选取功能",
                     "choose": "选择功能",
                     "option": "选项管理",
                     "preference": "偏好设置",
                     "custom": "自定义",
                     "default": "默认设置",
                     "standard": "标准设置",
                     "advanced": "高级设置",
                     "basic": "基础设置",
                     "simple": "简单模式",
                     "complex": "复杂模式",
                     "expert": "专家模式",
                     "beginner": "新手模式",
                     "guide": "操作指南",
                     "tutorial": "教程",
                     "wizard": "向导",
                     "assistant": "助手",
                     "tool": "工具",
                     "utility": "实用工具",
                     "service": "服务",
                     "component": "组件",
                     "module": "模块",
                     "plugin": "插件",
                     "addon": "附加组件",
                     "extension": "扩展",
                     "widget": "小部件",
                     "gadget": "小工具",
                     "feature": "功能",
                     "function": "函数",
                     "method": "方法",
                     "action": "操作",
                     "command": "命令",
                     "request": "请求",
                     "response": "响应",
                     "result": "结果",
                     "output": "输出",
                     "input": "输入",
                     "data": "数据",
                     "info": "信息",
                     "detail": "详情",
                     "summary": "摘要",
                     "overview": "概览",
                     "list": "列表",
                     "table": "表格",
                     "grid": "网格",
                     "chart": "图表",
                     "graph": "图形",
                     "diagram": "图表",
                     "map": "地图",
                     "tree": "树形结构",
                     "hierarchy": "层级结构",
                     "category": "分类",
                     "group": "分组",
                     "cluster": "集群",
                     "collection": "集合",
                     "set": "集合",
                     "array": "数组",
                     "object": "对象",
                     "entity": "实体",
                     "model": "模型",
                     "schema": "架构",
                     "structure": "结构",
                     "format": "格式",
                     "type": "类型",
                     "kind": "种类",
                     "style": "样式",
                     "theme": "主题",
                     "skin": "皮肤",
                     "layout": "布局",
                     "design": "设计",
                     "template": "模板",
                     "pattern": "模式",
                     "example": "示例",
                     "sample": "样本",
                     "demo": "演示",
                     "preview": "预览",
                     "thumbnail": "缩略图",
                     "icon": "图标",
                     "logo": "标志",
                     "brand": "品牌",
                     "title": "标题",
                     "name": "名称",
                     "label": "标签",
                     "tag": "标记",
                     "mark": "标记",
                     "flag": "标志",
                     "badge": "徽章",
                     "status": "状态",
                     "state": "状态",
                     "condition": "条件",
                     "criteria": "标准",
                     "requirement": "需求",
                     "specification": "规格",
                     "definition": "定义",
                     "description": "描述",
                     "explanation": "说明",
                     "instruction": "指令",
                     "direction": "方向",
                     "guidance": "指导",
                     "tip": "提示",
                     "hint": "提示",
                     "clue": "线索",
                     "note": "备注",
                     "comment": "评论",
                     "remark": "备注",
                     "annotation": "注释",
                     "documentation": "文档",
                     "manual": "手册",
                     "handbook": "手册",
                     "reference": "参考",
                     "guide": "指南",
                     "faq": "常见问题",
                     "qa": "问答",
                     "question": "问题",
                     "answer": "答案",
                     "solution": "解决方案",
                     "fix": "修复",
                     "patch": "补丁",
                     "hotfix": "热修复",
                     "bugfix": "错误修复",
                     "improvement": "改进",
                     "enhancement": "增强",
                     "optimization": "优化",
                     "upgrade": "升级",
                     "migration": "迁移",
                     "transition": "过渡",
                     "conversion": "转换",
                     "transformation": "转换",
                     "translation": "翻译",
                     "localization": "本地化",
                     "internationalization": "国际化",
                     "globalization": "全球化",
                     "regionalization": "区域化"
                 }
                return module_mapping.get(module_name, f"API-{module_name}")
            return "API接口"
        
        # 前端页面路径映射
        page_mapping = {
            "login": "登录页面",
            "register": "注册页面",
            "signup": "注册页面",
            "signin": "登录页面",
            "logout": "退出登录",
            "signout": "退出登录",
            "dashboard": "仪表盘",
            "home": "首页",
            "index": "首页",
            "main": "主页面",
            "users": "用户管理",
            "user": "用户管理",
            "profile": "个人资料",
            "account": "账户管理",
            "settings": "系统设置",
            "config": "配置管理",
            "configuration": "配置管理",
            "data-resources": "数据资源",
            "data_resources": "数据资源",
            "resources": "资源管理",
            "resource": "资源管理",
            "datasources": "数据源管理",
            "datasource": "数据源管理",
            "data-sources": "数据源管理",
            "data_sources": "数据源管理",
            "templates": "模板管理",
            "template": "模板管理",
            "tags": "标签管理",
            "tag": "标签管理",
            "permissions": "权限管理",
            "permission": "权限管理",
            "roles": "角色管理",
            "role": "角色管理",
            "groups": "用户组管理",
            "group": "用户组管理",
            "system": "系统管理",
            "admin": "系统管理",
            "administration": "系统管理",
            "reports": "报表管理",
            "report": "报表管理",
            "analytics": "数据分析",
            "analysis": "数据分析",
            "statistics": "统计分析",
            "stats": "统计分析",
            "logs": "操作日志",
            "log": "操作日志",
            "audit": "审计日志",
            "monitor": "系统监控",
            "monitoring": "系统监控",
            "health": "健康检查",
            "status": "状态查询",
            "files": "文件管理",
            "file": "文件管理",
            "upload": "文件上传",
            "uploads": "文件上传",
            "download": "文件下载",
            "downloads": "文件下载",
            "export": "数据导出",
            "import": "数据导入",
            "backup": "数据备份",
            "restore": "数据恢复",
            "search": "搜索功能",
            "query": "查询功能",
            "browse": "浏览功能",
            "view": "查看功能",
            "edit": "编辑功能",
            "create": "创建功能",
            "add": "添加功能",
            "new": "新建功能",
            "delete": "删除功能",
            "remove": "删除功能",
            "update": "更新功能",
            "modify": "修改功能",
            "change": "修改功能",
            "copy": "复制功能",
            "duplicate": "复制功能",
            "move": "移动功能",
            "rename": "重命名功能",
            "share": "分享功能",
            "publish": "发布功能",
            "unpublish": "取消发布",
            "archive": "归档功能",
            "unarchive": "取消归档",
            "trash": "垃圾箱",
            "recycle": "回收站",
            "favorite": "收藏功能",
            "favorites": "收藏夹",
            "bookmark": "书签管理",
            "bookmarks": "书签管理",
            "history": "历史记录",
            "recent": "最近访问",
            "popular": "热门内容",
            "trending": "趋势分析",
            "recommend": "推荐系统",
            "recommendations": "推荐系统",
            "notification": "消息通知",
            "notifications": "消息通知",
            "message": "消息管理",
            "messages": "消息管理",
            "mail": "邮件管理",
            "email": "邮件管理",
            "workflow": "工作流程",
            "workflows": "工作流程",
            "task": "任务管理",
            "tasks": "任务管理",
            "job": "作业管理",
            "jobs": "作业管理",
            "schedule": "调度管理",
            "scheduler": "调度管理",
            "calendar": "日历管理",
            "event": "事件管理",
            "events": "事件管理",
            "project": "项目管理",
            "projects": "项目管理",
            "workspace": "工作空间",
            "workspaces": "工作空间",
            "organization": "组织管理",
            "organizations": "组织管理",
            "department": "部门管理",
            "departments": "部门管理",
            "help": "帮助文档",
            "support": "技术支持",
            "about": "关于我们",
            "contact": "联系我们",
            "feedback": "用户反馈",
            "survey": "问卷调查",
            "api": "接口管理",
            "docs": "API文档",
            "documentation": "文档中心",
            "guide": "操作指南",
            "tutorial": "教程",
            "faq": "常见问题",
            "error": "错误页面",
            "404": "页面未找到",
            "403": "访问被拒绝",
            "500": "服务器错误",
            "maintenance": "系统维护",
            "coming-soon": "即将上线",
            "under-construction": "建设中"
        }
        
        # 检查是否匹配页面映射
        for part in parts:
            if part in page_mapping:
                return page_mapping[part]
        
        # 如果没有匹配到，尝试处理复合路径
        if len(parts) >= 2:
            # 处理类似 "data-resources/123" 或 "users/edit" 的情况
            combined_path = "-".join(parts[:2])
            if combined_path in page_mapping:
                return page_mapping[combined_path]
            
            # 处理下划线连接的路径
            combined_path = "_".join(parts[:2])
            if combined_path in page_mapping:
                return page_mapping[combined_path]
        
        # 最后的回退策略：返回第一个路径部分的中文映射
        return page_mapping.get(first_part, f"页面-{first_part}")

    def _get_server_host(self) -> str:
        """获取服务器主机名"""
        try:
            # 优先使用环境变量
            host = os.environ.get('SERVER_HOST') or os.environ.get('HOSTNAME')
            if host:
                return host
            # 获取主机名
            return socket.gethostname()
        except Exception:
            return 'unknown'

    def _get_session_id(self, request: Request) -> Optional[str]:
        """从请求中提取会话ID"""
        try:
            # 从Cookie中获取会话ID
            session_id = request.cookies.get('session_id') or request.cookies.get('sessionid')
            if session_id:
                return session_id
            
            # 从Header中获取
            session_id = request.headers.get('X-Session-ID') or request.headers.get('Session-ID')
            if session_id:
                return session_id
                
            return None
        except Exception:
            return None

    async def dispatch(self, request: Request, call_next):
        # 过滤不必要的请求，例如静态、文档、健康检查、预检
        path = request.url.path
        method = request.method.upper()
        full_url = str(request.url)
        # 映射HTTP方法为通用的动作类型，兼容旧库必填字段
        def map_action_type(m: str) -> str:
            m = (m or '').upper()
            if m == 'GET':
                return 'read'
            if m == 'POST':
                return 'create'
            if m in ('PUT', 'PATCH'):
                return 'update'
            if m == 'DELETE':
                return 'delete'
            return 'other'
        action_type = map_action_type(method)
        if (
            method == 'OPTIONS'
            or path.startswith('/docs')
            or path.startswith('/redoc')
            or path.startswith('/openapi')
            or path.startswith('/api/v1/user-operation-logs/')
            or path.startswith('/api/v1/data-upload-logs')
            or path.startswith('/ui/assets')
        ):
            return await call_next(request)

        # 记录开始时间
        start_ts = time.time()
        request_id = str(uuid.uuid4())

        # 解析用户信息（从Authorization中解码JWT）
        user_id: Optional[int] = None
        username: Optional[str] = None
        try:
            auth = request.headers.get('Authorization')
            if auth and auth.startswith('Bearer '):
                token = auth.split(' ', 1)[1]
                payload = decode_access_token(token)
                # JWT中约定sub为用户ID
                uid = payload.get('sub')
                if uid is not None:
                    try:
                        user_id = int(uid)
                    except Exception:
                        user_id = None
                username = payload.get('username') or payload.get('name')
        except Exception:
            # 解码失败不影响业务
            pass

        # 请求基础信息 - 优先从X-Forwarded-For获取真实IP
        ip_address = None
        if 'x-forwarded-for' in request.headers:
            ip_address = request.headers['x-forwarded-for'].split(',')[0].strip()
        elif 'x-real-ip' in request.headers:
            ip_address = request.headers['x-real-ip']
        elif request.client:
            ip_address = request.client.host
        query_params = dict(request.query_params) if request.query_params else {}
        headers = {k: v for k, v in request.headers.items()}

        # 提取新增字段信息
        module = self._extract_module_from_path(path)
        server_host = self._get_server_host()
        user_agent = request.headers.get('User-Agent')
        referer = request.headers.get('Referer')
        session_id = self._get_session_id(request)
        trace_id = request.headers.get('X-Trace-ID') or request.headers.get('Trace-ID') or request_id

        # 尝试读取请求体（可能为空或流）
        request_body = None
        request_size = 0
        try:
            body_bytes = await request.body()
            # 将body回填，避免下游无法读取
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive  # type: ignore
            request_body = body_bytes.decode('utf-8', errors='ignore') if body_bytes else None
            request_size = len(body_bytes) if body_bytes else 0
        except Exception:
            request_body = None
            request_size = 0

        error_message = None
        stack_trace = None

        # 调用下游并捕获响应体
        response: Response
        status_code = None
        response_size = 0
        try:
            response = await call_next(request)
            status_code = response.status_code
            # 读取响应体内容（可能是流式）
            try:
                resp_body = [section async for section in response.body_iterator]
                response.body_iterator = iterate_in_threadpool(iter(resp_body))
                response_body = b"".join(resp_body)
                response_text = response_body.decode('utf-8', errors='ignore') if response_body else None
                response_size = len(response_body) if response_body else 0
            except Exception:
                response_text = None
                response_size = 0
        except Exception as e:
            # 下游异常
            status_code = 500
            error_message = str(e)
            stack_trace = traceback.format_exc()
            response = Response(
                content=json.dumps({"detail": "Internal Server Error"}, ensure_ascii=False),
                status_code=500,
                media_type="application/json"
            )
            response_text = None
            response_size = 0

        # 计算耗时
        duration_ms = int((time.time() - start_ts) * 1000)
        # 确保result_status不为null
        if status_code is not None:
            result_status = 'success' if status_code < 400 else 'failure'
        else:
            result_status = 'failure'  # 如果status_code为None，默认为failure

        # 将日志写入数据库
        try:
            async with get_db_context() as db:
                # 动态检测主表可用列，构造兼容的 INSERT
                main_cols_res = await db.execute(text(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'user_operation_logs'"
                ))
                main_cols = {row[0] for row in main_cols_res.fetchall()}

                insert_cols = []
                value_exprs = []
                params = {
                    'request_id': request_id,
                    'user_id': user_id,
                    'username': username,
                    'method': method,
                    'path': path,
                    'url': full_url,
                    'action_type': action_type,
                    'status_code': int(status_code) if status_code is not None else None,
                    'result_status': result_status,
                    'ip_address': ip_address,
                    'duration_ms': duration_ms,
                    'module': module,
                    'response_status': int(status_code) if status_code is not None else None,
                    'server_host': server_host,
                    'user_agent': user_agent,
                    'referer': referer,
                    'request_size': request_size,
                    'response_size': response_size,
                    'session_id': session_id,
                    'trace_id': trace_id,
                }

                def add(col, expr= None, param_name=None):
                    if col in main_cols:
                        insert_cols.append(col)
                        if expr is not None:
                            value_exprs.append(expr)
                        else:
                            pn = param_name or col
                            value_exprs.append(f":{pn}")

                add('request_id')
                add('user_id')
                add('username')
                add('method')
                add('path')
                add('url')
                add('action_type')
                add('status_code')
                add('result_status')
                add('ip_address')
                add('duration_ms')
                add('module')
                add('response_status')
                add('server_host')
                add('user_agent')
                add('referer')
                add('request_size')
                add('response_size')
                add('session_id')
                add('trace_id')
                # created_at 用数据库时间
                add('created_at', expr='CURRENT_TIMESTAMP')

                if insert_cols:
                    insert_main_sql = text(
                        f"INSERT INTO user_operation_logs ({', '.join(insert_cols)}) VALUES ({', '.join(value_exprs)})"
                    )
                    await db.execute(insert_main_sql, params)

                    # 获取刚插入ID（MySQL）
                    result = await db.execute(text("SELECT LAST_INSERT_ID()"))
                    log_id_row = result.fetchone()
                    log_id = log_id_row[0] if log_id_row else None
                else:
                    log_id = None

                # 动态检测详情表可用列，构造兼容的 INSERT
                detail_cols_res = await db.execute(text(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'user_operation_log_details'"
                ))
                detail_cols = {row[0] for row in detail_cols_res.fetchall()}

                # 兼容旧库可能存在的必填字段 field_name
                def _guess_field_name():
                    try:
                        if request_body:
                            jb = json.loads(request_body)
                            if isinstance(jb, dict) and jb:
                                return next(iter(jb.keys()))
                            if isinstance(jb, list) and jb and isinstance(jb[0], dict) and jb[0]:
                                return next(iter(jb[0].keys()))
                    except Exception:
                        pass
                    if query_params:
                        for k in query_params.keys():
                            if k:
                                return k
                    try:
                        seg = path.strip('/').split('/')[-1]
                        if seg:
                            return seg
                    except Exception:
                        pass
                    return 'unknown'
                field_name = _guess_field_name()

                d_insert_cols = []
                d_value_exprs = []
                d_params = {
                    'log_id': log_id,
                    'request_headers': json.dumps(headers, ensure_ascii=False),
                    'query_params': json.dumps(query_params, ensure_ascii=False),
                    'request_body': request_body,
                    'response_body': response_text,
                    'error_message': error_message,
                    'stack_trace': stack_trace,
                    'field_name': field_name,
                }

                def d_add(col, expr=None, param_name=None):
                    if col in detail_cols:
                        d_insert_cols.append(col)
                        if expr is not None:
                            d_value_exprs.append(expr)
                        else:
                            pn = param_name or col
                            d_value_exprs.append(f":{pn}")

                d_add('log_id')
                d_add('request_headers')
                d_add('query_params')
                d_add('request_body')
                d_add('response_body')
                d_add('error_message')
                d_add('stack_trace')
                d_add('field_name')
                d_add('created_at', expr='CURRENT_TIMESTAMP')

                if d_insert_cols:
                    insert_detail_sql = text(
                        f"INSERT INTO user_operation_log_details ({', '.join(d_insert_cols)}) VALUES ({', '.join(d_value_exprs)})"
                    )
                    await db.execute(insert_detail_sql, d_params)
        except Exception as e:
            # 写库失败不影响业务流，记录到应用日志
            logger.error(f"写入用户操作日志失败: {e}")
        return response