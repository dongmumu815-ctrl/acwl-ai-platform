"""Excel生成服务"""

import io
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.models.resource_package import ResourcePackage, ResourcePackageFile
from app.services.elasticsearch_service import ElasticsearchService
import logging

logger = logging.getLogger(__name__)


class ExcelService:
    """Excel生成和MinIO上传服务"""
    
    def __init__(self):
        self.minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
            region=settings.MINIO_REGION
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.es_service = ElasticsearchService()
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name, location=settings.MINIO_REGION)
                logger.info(f"创建MinIO存储桶: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"MinIO存储桶操作失败: {e}")
            raise
    
    async def generate_and_upload_excel(
        self, 
        package_id: int, 
        query_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        生成Excel并上传到MinIO
        
        Args:
            package_id: 资源包ID
            query_data: 查询数据和参数
            db: 数据库会话
            
        Returns:
            Dict包含下载URL和状态信息
        """
        # 获取资源包信息
        result = await db.execute(
            select(ResourcePackage).where(ResourcePackage.id == package_id)
        )
        package = result.scalar_one_or_none()
        
        if not package:
            raise ValueError("资源包不存在")
        
        # 执行查询获取最新数据（基于 excel_time 过滤）
        query_result = await self._execute_query(package, query_data, db)
        
        if not query_result or not query_result.get('hits', {}).get('hits'):
            return {"status": "no_new_data", "message": "无最新数据，无需生成"}
        
        # 检查数据更新时间是否大于 excel_time
        if not await self._has_new_data(package, query_result):
            return {"status": "no_new_data", "message": "无最新数据，无需生成"}
        
        # 生成Excel文件
        excel_buffer = self._generate_excel(query_result, package.name, requested_fields=query_data.get("_source"))
        
        # 上传到MinIO
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resource_package_{package_id}_{timestamp}.xlsx"
        object_path = f"resource_packages/{package_id}/{filename}"
        
        try:
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                data=excel_buffer,
                length=excel_buffer.getbuffer().nbytes,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            # 保存历史记录
            file_rec = ResourcePackageFile(
                package_id=package_id,
                filename=filename,
                object_path=object_path,
                generated_at=datetime.now()
            )
            db.add(file_rec)
            
            # 更新资源包的生成信息
            package.excel_time = datetime.now()
            package.download_url = f"minio://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{object_path}"
            await db.commit()
            
            # 生成预签名下载URL（有效期1小时）
            download_url = self.minio_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                expires=timedelta(seconds=3600)  # 1小时
            )
            
            return {
                "status": "success",
                "download_url": download_url,
                "filename": filename,
                "minio_path": package.download_url
            }
            
        except S3Error as e:
            logger.error(f"MinIO上传失败: {e}")
            raise Exception(f"文件上传失败: {str(e)}")
    
    async def _execute_query(self, package: ResourcePackage, query_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """执行ES查询获取数据（按 excel_time 过滤）"""
        try:
            # 获取数据源信息
            from app.services.datasource import DatasourceService
            from elasticsearch import AsyncElasticsearch
            
            datasource_service = DatasourceService(db)
            datasource = await datasource_service.get_datasource(package.datasource_id)
            
            if not datasource:
                raise ValueError(f"数据源 ID {package.datasource_id} 不存在")
            
            # 创建ES客户端
            if datasource.username and datasource.password:
                es_client = AsyncElasticsearch(
                    [{
                        'scheme': 'http',
                        'host': datasource.host,
                        'port': datasource.port
                    }],
                    basic_auth=(datasource.username, datasource.password),
                    verify_certs=False
                )
            else:
                es_client = AsyncElasticsearch(
                    [{
                        'scheme': 'http',
                        'host': datasource.host,
                        'port': datasource.port
                    }],
                    verify_certs=False
                )
            
            try:
                # 构建查询体（加入 update_time > excel_time 过滤）
                base_query = query_data.get("query", {"match_all": {}})
                
                # 根据资源包的excel生成时间添加 update_time 过滤
                xl_time = package.excel_time
                range_filter = None
                if xl_time is not None:
                    xl_dt = None
                    if isinstance(xl_time, (int, float)):
                        try:
                            xl_dt = datetime.fromtimestamp(xl_time)
                        except Exception:
                            xl_dt = None
                    elif isinstance(xl_time, datetime):
                        xl_dt = xl_time
                    if xl_dt is not None:
                        excel_time_str = xl_dt.strftime("%Y-%m-%dT%H:%M:%S")
                        range_filter = {"range": {"update_time": {"gt": excel_time_str}}}
                
                # 合成最终查询
                if range_filter:
                    query = {"bool": {"must": [base_query], "filter": [range_filter]}}
                else:
                    query = base_query
                
                query_body = {
                    "query": query,
                    "size": 10000,  # 最大返回10000条记录
                    "from": 0
                }
                
                if query_data.get("_source"):
                    query_body["_source"] = query_data["_source"]
                
                # 执行ES查询
                result = await es_client.search(
                    index=query_data.get("index", ""),
                    query=query,
                    size=query_body.get("size", 10),
                    from_=query_body.get("from", 0),
                    source=query_body.get("_source"),
                    sort=query_body.get("sort"),
                    aggs=query_body.get("aggs")
                )
                return result
                
            finally:
                await es_client.close()
            
        except Exception as e:
            logger.error(f"执行ES查询失败: {e}")
            raise
    
    async def _has_new_data(self, package: ResourcePackage, query_result: Dict[str, Any]) -> bool:
        """检查是否有新数据（与 excel_time 比较）"""
        hits = query_result.get('hits', {}).get('hits', [])
        if not hits:
            return False
        
        # 如果是第一次生成（excel_time为None），有数据即可生成
        if package.excel_time is None:
            return True
        
        # 确保excel_time是datetime对象
        excel_time = package.excel_time
        if isinstance(excel_time, (int, float)):
            try:
                # 检查时间戳是否有效（不能为负数或过大）
                if excel_time < 0 or excel_time > 2147483647:  # Unix时间戳最大值
                    logger.warning(f"无效的时间戳值: {excel_time}")
                    return True
                excel_time = datetime.fromtimestamp(excel_time)
            except (ValueError, OSError, OverflowError) as e:
                logger.warning(f"时间戳转换失败: {e}, excel_time: {excel_time}")
                return True  # 转换失败，默认认为有新数据
        elif not isinstance(excel_time, datetime):
            logger.warning(f"excel_time类型异常: {type(excel_time)}, 值: {excel_time}")
            return True  # 如果类型异常，默认认为有新数据
        
        # 检查数据中是否有update_time字段大于excel_time的记录
        for hit in hits:
            source = hit.get('_source', {})
            update_time_str = source.get('update_time') or source.get('updated_at') or source.get('updateTime')
            
            if update_time_str:
                try:
                    # 尝试解析时间字符串
                    if isinstance(update_time_str, str):
                        # 支持多种时间格式
                        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                            try:
                                update_time = datetime.strptime(update_time_str, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            continue  # 无法解析时间格式，跳过此记录
                    elif isinstance(update_time_str, (int, float)):
                        # 时间戳格式
                        try:
                            # 检查时间戳是否有效
                            if update_time_str < 0 or update_time_str > 2147483647:
                                logger.warning(f"无效的update_time时间戳: {update_time_str}")
                                continue
                            update_time = datetime.fromtimestamp(update_time_str)
                        except (ValueError, OSError, OverflowError) as e:
                            logger.warning(f"update_time时间戳转换失败: {e}, update_time_str: {update_time_str}")
                            continue
                    else:
                        continue
                    
                    # 比较时间
                    if update_time > excel_time:
                        return True
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"时间解析失败: {e}, update_time_str: {update_time_str}")
                    continue
        
        return False
    
    def _generate_excel(self, query_result: Dict[str, Any], package_name: str, requested_fields: Optional[List[str]] = None) -> io.BytesIO:
        """生成Excel文件"""
        wb = Workbook()
        ws = wb.active
        ws.title = "查询结果"
        
        # 获取数据
        hits = query_result.get('hits', {}).get('hits', [])
        if not hits:
            raise ValueError("无数据可导出")
        
        # 获取所有字段名
        all_fields = set()
        for hit in hits:
            source = hit.get('_source', {})
            all_fields.update(source.keys())
        
        # 优先使用请求中的_source字段列表，以保持与前端显示一致
        fields = list(requested_fields) if requested_fields and len(requested_fields) > 0 else sorted(list(all_fields))
        
        # 设置标题样式
        title_font = Font(bold=True, color="FFFFFF")
        title_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        title_alignment = Alignment(horizontal="center", vertical="center")
        
        # 写入表头
        for col_idx, field in enumerate(fields, 1):
            cell = ws.cell(row=1, column=col_idx, value=field)
            cell.font = title_font
            cell.fill = title_fill
            cell.alignment = title_alignment
        
        # 写入数据
        for row_idx, hit in enumerate(hits, 2):
            source = hit.get('_source', {})
            for col_idx, field in enumerate(fields, 1):
                value = source.get(field, '')
                # 处理复杂数据类型
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                ws.cell(row=row_idx, column=col_idx, value=value)
        
        # 自动调整列宽
        for col_idx, field in enumerate(fields, 1):
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].width = min(max(len(field) + 2, 10), 50)
        
        # 添加信息工作表
        info_ws = wb.create_sheet("导出信息")
        info_data = [
            ["资源包名称", package_name],
            ["导出时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["数据条数", len(hits)],
            ["字段数量", len(fields)]
        ]
        
        for row_idx, (key, value) in enumerate(info_data, 1):
            info_ws.cell(row=row_idx, column=1, value=key).font = Font(bold=True)
            info_ws.cell(row=row_idx, column=2, value=value)
        
        # 保存到内存
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        return excel_buffer