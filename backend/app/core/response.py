from typing import Any, Optional
from datetime import datetime, date
import json
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class CustomJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime对象"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def success_response(
    data: Any = None,
    message: str = "操作成功",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    成功响应函数
    
    Args:
        data: 响应数据
        message: 响应消息
        status_code: HTTP状态码
        
    Returns:
        JSONResponse: 成功响应
    """
    # 如果data是Pydantic模型，转换为字典
    if isinstance(data, BaseModel):
        data = data.model_dump()
    elif hasattr(data, '__dict__') and hasattr(data, '__class__'):
        # 处理其他可能的模型对象
        try:
            data = data.model_dump() if hasattr(data, 'model_dump') else data.__dict__
        except:
            pass
    
    response_data = {
        "success": True,
        "message": message,
        "data": data
    }
    # 使用自定义编码器序列化数据
    json_content = json.dumps(response_data, cls=CustomJSONEncoder, ensure_ascii=False)
    return JSONResponse(content=json.loads(json_content), status_code=status_code)


def error_response(
    message: str = "操作失败",
    error_code: Optional[str] = None,
    detail: Any = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """
    错误响应函数
    
    Args:
        message: 错误消息
        error_code: 错误代码
        detail: 错误详情
        status_code: HTTP状态码
        
    Returns:
        JSONResponse: 错误响应
    """
    response_data = {
        "success": False,
        "message": message,
        "error_code": error_code,
        "detail": detail
    }
    # 使用自定义编码器序列化数据
    json_content = json.dumps(response_data, cls=CustomJSONEncoder, ensure_ascii=False)
    return JSONResponse(content=json.loads(json_content), status_code=status_code)


def paginated_response(
    items: list,
    total: int,
    page: int,
    size: int,
    message: str = "获取数据成功"
) -> JSONResponse:
    """
    分页响应函数
    
    Args:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        size: 每页大小
        message: 响应消息
        
    Returns:
        JSONResponse: 分页响应
    """
    pages = (total + size - 1) // size  # 计算总页数
    
    response_data = {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
    }
    # 使用自定义编码器序列化数据
    json_content = json.dumps(response_data, cls=CustomJSONEncoder, ensure_ascii=False)
    return JSONResponse(content=json.loads(json_content), status_code=status.HTTP_200_OK)