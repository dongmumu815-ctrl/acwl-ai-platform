from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any
import logging
from app.services.template_service import template_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def get_template_list(
    name: str = None,
    is_active: bool = None,
    file_type: str = None
):
    """
    获取模板列表
    """
    filters = {}
    if name:
        filters['name'] = name
    if is_active is not None:
        filters['is_active'] = is_active
    if file_type:
        filters['file_type'] = file_type
        
    result = template_service.get_template_list(filters)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
        
    return result

@router.get("/{template_id}")
async def get_template(template_id: str):
    """
    获取单个模板详情
    """
    result = template_service.get_template(template_id)
    
    if not result.get("success"):
        if result.get("message") == "模板不存在":
            raise HTTPException(status_code=404, detail="模板不存在")
        raise HTTPException(status_code=500, detail=result.get("message"))
        
    return result

@router.post("/")
async def create_template(template_data: Dict[str, Any] = Body(...)):
    """
    创建模板
    """
    # 确保 excel_filename 字段被正确处理
    if 'excel_filename' in template_data:
        logger.info(f"创建模板 Excel 文件名: {template_data['excel_filename']}")
    
    result = template_service.create_template(template_data)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
        
    return result

@router.put("/{template_id}")
async def update_template(template_id: str, template_data: Dict[str, Any] = Body(...)):
    """
    更新模板
    """
    # 确保 excel_filename 字段被正确处理
    # 如果模板数据中包含 excel_filename，将其保存到数据库
    if 'excel_filename' in template_data:
        logger.info(f"更新模板 {template_id} 的 Excel 文件名: {template_data['excel_filename']}")
    
    result = template_service.update_template(template_id, template_data)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
        
    return result
