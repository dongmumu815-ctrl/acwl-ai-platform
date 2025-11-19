"""异步导出服务"""

import os
import csv
import json
import zipfile
import tempfile
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.database import get_db_context
from app.models.resource_package import ResourcePackage, ResourcePackageFile
from app.services.elasticsearch_service import ElasticsearchService
import logging
import hashlib

logger = logging.getLogger(__name__)

# 任务状态存储（在实际生产环境中应该使用Redis等外部存储）
_export_tasks = {}

class AsyncExportService:
    """异步导出服务类"""
    
    def __init__(self):
        self.es_service = ElasticsearchService()
    
    async def export_all_results(
        self, 
        package_id: int, 
        query_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        异步导出全部查询结果
        
        Args:
            package_id: 资源包ID
            query_data: 查询数据和参数
            db: 数据库会话
            
        Returns:
            Dict包含任务信息
        """
        try:
            # 获取资源包信息
            result = await db.execute(
                select(ResourcePackage).where(ResourcePackage.id == package_id)
            )
            package = result.scalar_one_or_none()
            
            if not package:
                raise ValueError("资源包不存在")
            
            # 创建异步任务来处理导出
            task_id = f"export_all_{package_id}_{int(datetime.now().timestamp())}"
            
            # 初始化任务状态
            _export_tasks[task_id] = {
                "status": "started",
                "package_id": package_id,
                "message": "已开始导出全部结果",
                "file_url": None,
                "file_path": None,
                "created_at": datetime.now(),
                # 初始化进度，避免前端读取到 null
                "progress": {
                    "total": None,
                    "processed": 0,
                    "percentage": None,
                    "pages_fetched": 0,
                    "files_generated": 0,
                    "current_file_rows": 0,
                }
            }
            
            # 在后台执行导出任务（使用独立数据库会话）
            asyncio.create_task(
                self._perform_export_task(package_id, query_data, task_id)
            )
            
            return {
                "status": "started",
                "task_id": task_id,
                "message": "已开始导出全部结果，请稍后查看下载链接"
            }
            
        except Exception as e:
            logger.error(f"启动异步导出失败: {e}")
            raise Exception(f"启动异步导出失败: {str(e)}")
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态
        
        返回当前任务的状态、提示信息、生成的下载链接（如果已完成），以及进度信息。
        """
        task_info = _export_tasks.get(task_id)
        if not task_info:
            return {"status": "not_found", "message": "任务不存在"}
        
        return {
            "status": task_info["status"],
            "message": task_info["message"],
            "file_url": task_info["file_url"],
            "progress": task_info.get("progress"),
            "created_at": task_info["created_at"]
        }
    
    async def get_latest_export_file(self, package_id: int, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """获取最新的导出文件，如果文件超过1小时则返回None"""
        try:
            # 查询最新的导出文件
            result = await db.execute(
                select(ResourcePackageFile)
                .where(ResourcePackageFile.package_id == package_id)
                .order_by(ResourcePackageFile.generated_at.desc())
                .limit(1)
            )
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                return None
            
            # 检查文件是否过期（超过1小时）
            if (datetime.now() - file_record.generated_at).total_seconds() > 3600:  # 1小时 = 3600秒
                # 文件过期，删除记录
                await db.delete(file_record)
                await db.commit()
                return None
            
            # 生成下载URL
            minio_client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
                region=settings.MINIO_REGION
            )
            
            try:
                presigned_url = minio_client.presigned_get_object(
                    bucket_name=settings.MINIO_BUCKET_NAME,
                    object_name=file_record.object_path,
                    expires=timedelta(hours=1)  # 1小时过期
                )
                
                return {
                    "file_id": file_record.id,
                    "filename": file_record.filename,
                    "download_url": presigned_url,
                    "generated_at": file_record.generated_at,
                    "object_path": file_record.object_path
                }
            except S3Error as e:
                logger.error(f"生成预签名URL失败: {e}")
                return None
                
        except Exception as e:
            logger.error(f"获取最新导出文件失败: {e}")
            return None

    async def get_matching_export_file(self, package_id: int, db: AsyncSession, query_hash: str) -> Optional[Dict[str, Any]]:
        """按查询哈希匹配最新导出文件
        
        功能：
        - 仅返回在1小时内生成且文件名包含指定查询哈希的导出文件
        - 返回包含预签名下载URL（1小时有效）
        """
        try:
            # 查询匹配的最新导出文件
            result = await db.execute(
                select(ResourcePackageFile)
                .where(
                    and_(
                        ResourcePackageFile.package_id == package_id,
                        ResourcePackageFile.filename.like(f"%{query_hash}%")
                    )
                )
                .order_by(ResourcePackageFile.generated_at.desc())
                .limit(1)
            )
            file_record = result.scalar_one_or_none()

            if not file_record:
                return None

            # 检查文件是否过期（超过1小时）
            if (datetime.now() - file_record.generated_at).total_seconds() > 3600:
                await db.delete(file_record)
                await db.commit()
                return None

            # 生成下载URL
            minio_client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
                region=settings.MINIO_REGION
            )

            try:
                presigned_url = minio_client.presigned_get_object(
                    bucket_name=settings.MINIO_BUCKET_NAME,
                    object_name=file_record.object_path,
                    expires=timedelta(hours=1)
                )

                return {
                    "file_id": file_record.id,
                    "filename": file_record.filename,
                    "download_url": presigned_url,
                    "generated_at": file_record.generated_at,
                    "object_path": file_record.object_path
                }
            except S3Error as e:
                logger.error(f"生成预签名URL失败: {e}")
                return None
        except Exception as e:
            logger.error(f"按查询哈希获取导出文件失败: {e}")
            return None
    
    async def delete_export_file(self, file_id: int, db: AsyncSession) -> bool:
        """删除导出文件记录和实际文件"""
        try:
            # 获取文件记录
            result = await db.execute(
                select(ResourcePackageFile).where(ResourcePackageFile.id == file_id)
            )
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                return False
            
            # 删除MinIO中的文件
            try:
                minio_client = Minio(
                    endpoint=settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE,
                    region=settings.MINIO_REGION
                )
                minio_client.remove_object(
                    bucket_name=settings.MINIO_BUCKET_NAME,
                    object_name=file_record.object_path
                )
            except S3Error as e:
                logger.error(f"删除MinIO文件失败: {e}")
            
            # 删除数据库记录
            await db.delete(file_record)
            await db.commit()
            
            return True
        except Exception as e:
            logger.error(f"删除导出文件失败: {e}")
            return False
    
    async def _perform_export_task(
        self, 
        package_id: int, 
        query_data: Dict[str, Any],
        task_id: str
    ):
        """执行导出任务
        
        使用独立数据库会话执行后台导出，避免复用请求中的会话在请求结束后被关闭导致错误。
        优化为：Elasticsearch滚动查询时边写CSV，减少内存占用，同时实时更新导出进度。
        """
        try:
            logger.info(f"开始执行异步导出任务: {task_id}")
            
            # 更新任务状态
            if task_id in _export_tasks:
                _export_tasks[task_id]["status"] = "processing"
                _export_tasks[task_id]["message"] = "正在处理导出任务"
                # 确保进度对象存在
                _export_tasks[task_id].setdefault("progress", {
                    "total": None,
                    "processed": 0,
                    "percentage": None,
                    "pages_fetched": 0,
                    "files_generated": 0,
                    "current_file_rows": 0,
                })
            
            # 1) 数据库会话：查询资源包，准备导出名称
            async with get_db_context() as task_db:
                result = await task_db.execute(
                    select(ResourcePackage).where(ResourcePackage.id == package_id)
                )
                package = result.scalar_one_or_none()
                if not package:
                    logger.error(f"资源包不存在: {package_id}")
                    if task_id in _export_tasks:
                        _export_tasks[task_id]["status"] = "failed"
                        _export_tasks[task_id]["message"] = "资源包不存在"
                    return
                package_name = str(package.name) if package.name is not None else f"package_{package_id}"
                # 计算查询哈希（基于索引 + 查询体 + 字段选择）
                try:
                    query_fingerprint = {
                        "index": query_data.get("index"),
                        "query": query_data.get("query"),
                        "_source": query_data.get("_source"),
                    }
                    qstr = json.dumps(query_fingerprint, ensure_ascii=False, sort_keys=True)
                except Exception:
                    # 兜底：直接dump query_data
                    qstr = json.dumps(query_data, ensure_ascii=False, sort_keys=True)
                query_hash = hashlib.md5(f"{package_id}:{qstr}".encode("utf-8")).hexdigest()
            
            # 2) 缓存检查：若1小时内已有相同查询结果，复用已生成的文件
            minio_client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
                region=settings.MINIO_REGION
            )
            async with get_db_context() as cache_db:
                existing_result = await cache_db.execute(
                    select(ResourcePackageFile)
                    .where(
                        and_(
                            ResourcePackageFile.package_id == package_id,
                            ResourcePackageFile.filename.like(f"%{query_hash}%")
                        )
                    )
                    .order_by(ResourcePackageFile.generated_at.desc())
                    .limit(1)
                )
                existing_file = existing_result.scalar_one_or_none()
                if existing_file:
                    # 检查是否在1小时内有效
                    if (datetime.now() - existing_file.generated_at).total_seconds() <= 3600:
                        try:
                            presigned_url_cache = minio_client.presigned_get_object(
                                bucket_name=settings.MINIO_BUCKET_NAME,
                                object_name=existing_file.object_path,
                                expires=timedelta(hours=1)
                            )
                            if task_id in _export_tasks:
                                _export_tasks[task_id]["status"] = "completed"
                                _export_tasks[task_id]["message"] = "使用缓存文件（1小时内有效）"
                                _export_tasks[task_id]["file_url"] = presigned_url_cache
                                _export_tasks[task_id]["file_path"] = existing_file.object_path
                            logger.info(f"复用缓存导出文件: {existing_file.object_path}")
                            return
                        except S3Error as e:
                            logger.warning(f"缓存文件生成预签名链接失败，转为重新导出: {e}")

            # 3) 连接ES并滚动查询，边写CSV
            from app.services.datasource import DatasourceService
            from elasticsearch import AsyncElasticsearch
            from elasticsearch.exceptions import ConnectionError as ESConnectionError, AuthenticationException, ConnectionTimeout as ESConnectionTimeout
            try:
                from elasticsearch import ApiError
            except Exception:
                from elasticsearch.exceptions import TransportError as ApiError

            # 独立会话用于获取数据源配置
            async with get_db_context() as task_db_for_ds:
                datasource_service = DatasourceService(task_db_for_ds)
                datasource_id = int(str(package.datasource_id)) if package.datasource_id is not None else 0
                datasource = await datasource_service.get_datasource(datasource_id)
            if not datasource:
                logger.error(f"数据源不存在: {datasource_id}")
                if task_id in _export_tasks:
                    _export_tasks[task_id]["status"] = "failed"
                    _export_tasks[task_id]["message"] = "数据源不存在"
                return

            timeout = datasource.connection_params.get('timeout', 30) if datasource.connection_params else 30
            try:
                timeout = int(timeout)
            except Exception:
                timeout = 30
            if timeout < 120:
                timeout = 120
            max_retries = datasource.connection_params.get('max_retries', 3) if datasource.connection_params else 3
            try:
                max_retries = int(max_retries)
            except Exception:
                max_retries = 3
            scheme = 'https' if (isinstance((datasource.connection_params or {}).get('use_ssl'), bool) and (datasource.connection_params or {}).get('use_ssl')) else (datasource.connection_params or {}).get('scheme', 'http')
            host_str = str(datasource.host) if datasource.host else 'localhost'
            port_int = int(datasource.port) if datasource.port else 9200
            hosts_config = [{ 'scheme': scheme, 'host': host_str, 'port': port_int }]

            es_client = AsyncElasticsearch(
                hosts=hosts_config,
                basic_auth=(datasource.username, datasource.password) if (datasource.username and datasource.password) else None,
                verify_certs=False,
                request_timeout=timeout,
                max_retries=max_retries,
                retry_on_timeout=True
            )

            rows_per_file = 100000
            source_fields = query_data.get("_source")
            took_total = 0
            pages_fetched = 0
            processed = 0
            total_value = None
            files_generated = 0

            import tempfile, csv, os
            temp_dir_ctx = tempfile.TemporaryDirectory()
            temp_dir = temp_dir_ctx.__enter__()
            csv_writer = None
            csv_file = None
            current_file_rows = 0
            fields = None

            try:
                await es_client.cluster.health()

                base_query = query_data.get("query", {"match_all": {}})
                page_size = int((datasource.connection_params or {}).get('export_page_size', 10000) or 10000)
                scroll_keep_alive = "10m"

                try:
                    count_resp = await es_client.search(
                        index=query_data.get("index", ""),
                        query=base_query,
                        size=0,
                        track_total_hits=True,
                        request_cache=False
                    )
                    total_meta_count = count_resp.get('hits', {}).get('total')
                    total_value_count = (total_meta_count.get('value') if isinstance(total_meta_count, dict) else total_meta_count) if total_meta_count is not None else None
                    if task_id in _export_tasks:
                        prog = _export_tasks[task_id].get("progress", {})
                        prog["total"] = total_value_count
                        prog["percentage"] = 0.0 if isinstance(total_value_count, int) and total_value_count > 0 else None
                        _export_tasks[task_id]["progress"] = prog
                except Exception as e:
                    logger.warning(f"快速总数统计失败: {e}")

                try:
                    first = await es_client.search(
                        index=query_data.get("index", ""),
                        query=base_query,
                        size=page_size,
                        sort=["_doc"],
                        source=source_fields,
                        scroll=scroll_keep_alive,
                        request_cache=False
                    )
                except ESConnectionTimeout:
                    fallback_sizes = [min(page_size, 2000), 500, 100]
                    first = None
                    for s in fallback_sizes:
                        try:
                            first_try = await es_client.search(
                                index=query_data.get("index", ""),
                                query=base_query,
                                size=s,
                                sort=["_doc"],
                                source=source_fields,
                                scroll=scroll_keep_alive,
                                request_cache=False
                            )
                            page_size = s
                            first = first_try
                            break
                        except ESConnectionTimeout:
                            pass
                    if first is None:
                        for s in fallback_sizes:
                            try:
                                first_try = await es_client.search(
                                    index=query_data.get("index", ""),
                                    query=base_query,
                                    size=s,
                                    source=source_fields,
                                    scroll=scroll_keep_alive,
                                    request_cache=False
                                )
                                page_size = s
                                first = first_try
                                break
                            except ESConnectionTimeout:
                                pass
                    if first is None:
                        raise
                total_meta = first.get('hits', {}).get('total')
                total_value = (total_meta.get('value') if isinstance(total_meta, dict) else total_meta) if total_meta is not None else None
                took_total += int(first.get('took', 0) or 0)
                batch_hits = first.get('hits', {}).get('hits', []) or []
                pages_fetched += 1
                scroll_id = first.get('_scroll_id')
                # 初始化进度总数与页面计数
                if task_id in _export_tasks:
                    prog = _export_tasks[task_id].get("progress", {})
                    prog["total"] = total_value
                    prog["pages_fetched"] = pages_fetched
                    prog["percentage"] = 0.0 if isinstance(total_value, int) and total_value > 0 else None
                    _export_tasks[task_id]["progress"] = prog

                # 若首批为空，也保持进度对象存在（已在上面初始化 total 与 pages）

                # 准备CSV写入（从第一批数据确定字段）
                def open_new_csv(file_index: int):
                    nonlocal csv_writer, csv_file, current_file_rows, files_generated
                    filename = f"{package_name}_part_{file_index}.csv"
                    filepath = os.path.join(temp_dir, filename)
                    csv_file = open(filepath, 'w', newline='', encoding='utf-8-sig')
                    csv_writer = csv.DictWriter(csv_file, fieldnames=fields)
                    csv_writer.writeheader()
                    current_file_rows = 0
                    files_generated += 1
                    return filepath

                if batch_hits:
                    if source_fields and isinstance(source_fields, list) and len(source_fields) > 0:
                        fields = list(source_fields)
                    else:
                        all_fields = set()
                        for h in batch_hits:
                            source = h.get('_source', {})
                            all_fields.update(source.keys())
                        fields = sorted(list(all_fields))

                    file_index = 1
                    part_paths = []
                    part_paths.append(open_new_csv(file_index))

                    async def write_rows(hits):
                        """批量写入CSV行，周期性让出事件循环避免阻塞"""
                        nonlocal processed, current_file_rows, file_index
                        yield_every = 1000
                        counter = 0
                        for hit in hits:
                            source = hit.get('_source', {})
                            row_data = {}
                            for f in fields:
                                v = source.get(f, '')
                                if isinstance(v, (dict, list)):
                                    v = json.dumps(v, ensure_ascii=False)
                                row_data[f] = v
                            csv_writer.writerow(row_data)
                            processed += 1
                            current_file_rows += 1
                            counter += 1
                            if current_file_rows >= rows_per_file:
                                csv_file.close()
                                file_index += 1
                                part_paths.append(open_new_csv(file_index))
                            if counter >= yield_every:
                                counter = 0
                                await asyncio.sleep(0)
                        # 更新进度
                        if task_id in _export_tasks:
                            prog = _export_tasks[task_id].get("progress", {})
                            prog["processed"] = processed
                            prog["pages_fetched"] = pages_fetched
                            prog["files_generated"] = files_generated
                            prog["current_file_rows"] = current_file_rows
                            if isinstance(total_value, int) and total_value > 0:
                                prog["percentage"] = round(processed * 100.0 / total_value, 2)
                            _export_tasks[task_id]["progress"] = prog

                    # 写入首批
                    await write_rows(batch_hits)

                    scroll_retry_attempts = 2
                    while scroll_id:
                        try:
                            next_page = await es_client.scroll(scroll_id=scroll_id, scroll=scroll_keep_alive)
                        except ApiError as e:
                            detail = getattr(e, 'body', None) or str(e)
                            logger.error(f"ES滚动查询下一页失败(ApiError): {detail}")
                            break
                        except ESConnectionTimeout:
                            if scroll_retry_attempts > 0:
                                scroll_retry_attempts -= 1
                                try:
                                    next_page = await es_client.scroll(scroll_id=scroll_id, scroll=scroll_keep_alive)
                                except ESConnectionTimeout:
                                    continue
                            else:
                                raise
                        batch_hits = next_page.get('hits', {}).get('hits', []) or []
                        if not batch_hits:
                            break
                        pages_fetched += 1
                        took_total += int(next_page.get('took', 0) or 0)
                        scroll_id = next_page.get('_scroll_id') or scroll_id
                        await write_rows(batch_hits)

                    # 清理滚动上下文
                    if scroll_id:
                        try:
                            await es_client.clear_scroll(scroll_id=scroll_id)
                        except Exception:
                            pass

                    # 关闭最后一个CSV文件句柄
                    if csv_file:
                        csv_file.close()

                    # 如果没有任何数据写入
                    if processed == 0:
                        logger.info("无数据可导出")
                        if task_id in _export_tasks:
                            _export_tasks[task_id]["status"] = "completed"
                            _export_tasks[task_id]["message"] = "无数据可导出"
                            # 进度补充：总数可能为0，处理为0
                            prog = _export_tasks[task_id].get("progress", {})
                            prog["processed"] = 0
                            prog["percentage"] = 0.0 if isinstance(total_value, int) and total_value > 0 else None
                            _export_tasks[task_id]["progress"] = prog
                        return

                    # 打包ZIP（移至线程避免阻塞事件循环）
                    if task_id in _export_tasks:
                        _export_tasks[task_id]["message"] = "正在打包生成ZIP文件"
                    zip_filename_local = os.path.join(temp_dir, f"{package_name}_export.zip")
                    def build_zip(parts, out_path):
                        """构建ZIP文件（阻塞操作）"""
                        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for p in parts:
                                zipf.write(p, os.path.basename(p))
                    await asyncio.to_thread(build_zip, part_paths, zip_filename_local)

                    # 上传到MinIO（使用文件流并传递长度，避免一次性载入内存）
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    zip_filename = f"resource_package_{package_id}_{query_hash}_{timestamp}.zip"
                    object_path = f"resource_packages/{package_id}/exports/{zip_filename}"
                    file_size = os.stat(zip_filename_local).st_size
                    if task_id in _export_tasks:
                        _export_tasks[task_id]["message"] = "正在上传文件到对象存储"
                    def upload_zip(bucket, object_name, local_path, length):
                        """上传ZIP到MinIO（阻塞操作）"""
                        with open(local_path, 'rb') as data_stream:
                            minio_client.put_object(
                                bucket_name=bucket,
                                object_name=object_name,
                                data=data_stream,
                                length=length,
                                content_type='application/zip'
                            )
                    await asyncio.to_thread(
                        upload_zip,
                        settings.MINIO_BUCKET_NAME,
                        object_path,
                        zip_filename_local,
                        file_size
                    )

                    # 写库记录
                    async with get_db_context() as task_db_for_save:
                        file_rec = ResourcePackageFile(
                            package_id=package_id,
                            filename=zip_filename,
                            object_path=object_path,
                            generated_at=datetime.now()
                        )
                        task_db_for_save.add(file_rec)

                    # 生成预签名URL
                    if task_id in _export_tasks:
                        _export_tasks[task_id]["message"] = "正在生成下载链接"
                    presigned_url = minio_client.presigned_get_object(
                        bucket_name=settings.MINIO_BUCKET_NAME,
                        object_name=object_path,
                        expires=timedelta(hours=1)
                    )

                    logger.info(f"异步导出完成，文件已上传: {object_path}")
                    if task_id in _export_tasks:
                        _export_tasks[task_id]["status"] = "completed"
                        _export_tasks[task_id]["message"] = "导出完成"
                        _export_tasks[task_id]["file_url"] = presigned_url
                        _export_tasks[task_id]["file_path"] = object_path
                else:
                    # 没有命中数据
                    logger.info("无数据可导出")
                    if task_id in _export_tasks:
                        _export_tasks[task_id]["status"] = "completed"
                        _export_tasks[task_id]["message"] = "无数据可导出"
                    return

            except ESConnectionTimeout as e:
                logger.error(f"ES健康/查询超时: {e}")
                if task_id in _export_tasks:
                    _export_tasks[task_id]["status"] = "failed"
                    _export_tasks[task_id]["message"] = "ES连接超时"
                raise
            except (ESConnectionError, AuthenticationException) as e:
                logger.error(f"ES连接/认证失败: {e}")
                if task_id in _export_tasks:
                    _export_tasks[task_id]["status"] = "failed"
                    _export_tasks[task_id]["message"] = "ES连接或认证失败"
                raise
            except S3Error as e:
                logger.error(f"MinIO上传失败: {e}")
                if task_id in _export_tasks:
                    _export_tasks[task_id]["status"] = "failed"
                    _export_tasks[task_id]["message"] = f"文件上传失败: {str(e)}"
                raise
            except Exception as e:
                logger.error(f"导出过程异常: {e}")
                if task_id in _export_tasks:
                    _export_tasks[task_id]["status"] = "failed"
                    _export_tasks[task_id]["message"] = f"导出失败: {str(e)}"
                raise
            finally:
                try:
                    await es_client.close()
                except Exception:
                    pass
                # 清理临时目录
                try:
                    temp_dir_ctx.__exit__(None, None, None)
                except Exception:
                    pass
        
        except Exception as e:
            logger.error(f"异步导出任务执行失败: {e}")
            if task_id in _export_tasks:
                _export_tasks[task_id]["status"] = "failed"
                _export_tasks[task_id]["message"] = f"导出失败: {str(e)}"
    
    async def _execute_full_query(self, package: ResourcePackage, query_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """执行ES查询获取全部数据"""
        datasource = None
        datasource_id = 0
        
        try:
            # 获取数据源信息
            from app.services.datasource import DatasourceService
            from elasticsearch import AsyncElasticsearch
            from elasticsearch.exceptions import ConnectionError as ESConnectionError, AuthenticationException, ConnectionTimeout as ESConnectionTimeout
            
            try:
                # ES 8+ 客户端的通用 API 错误类型
                from elasticsearch import ApiError
            except Exception:
                # 兼容旧版本
                from elasticsearch.exceptions import TransportError as ApiError
            
            datasource_service = DatasourceService(db)
            datasource_id = int(str(package.datasource_id)) if package.datasource_id is not None else 0
            datasource = await datasource_service.get_datasource(datasource_id)
            
            if not datasource:
                raise ValueError(f"数据源 ID {datasource_id} 不存在")
            
            # 连接参数（超时/重试/协议）
            timeout = datasource.connection_params.get('timeout', 30) if datasource.connection_params else 30
            # 归一化与最小阈值：避免过低的超时导致频繁失败
            try:
                timeout = int(timeout)
            except Exception:
                timeout = 30
            if timeout < 30:
                logger.info(f"检测到ES超时配置过低({timeout}s)，使用最小超时30s")
                timeout = 30

            max_retries = datasource.connection_params.get('max_retries', 3) if datasource.connection_params else 3
            try:
                max_retries = int(max_retries)
            except Exception:
                max_retries = 3
            scheme = 'http'
            if datasource.connection_params:
                params = datasource.connection_params
                if isinstance(params.get('use_ssl'), bool) and params.get('use_ssl'):
                    scheme = 'https'
                elif params.get('scheme') in ('http', 'https'):
                    scheme = params.get('scheme')
            logger.info(
                f"准备执行ES查询: datasource_id={datasource_id}, host={datasource.host}, port={datasource.port}, scheme={scheme}, "
                f"timeout={timeout}, max_retries={max_retries}, index={query_data.get('index')}"
            )

            # 创建ES客户端
            host_str = str(datasource.host) if datasource.host else 'localhost'
            port_int = int(datasource.port) if datasource.port else 9200
            
            hosts_config = [{
                'scheme': scheme,
                'host': host_str,
                'port': port_int
            }]
            
            if datasource.username and datasource.password:
                es_client = AsyncElasticsearch(
                    hosts=hosts_config,
                    basic_auth=(datasource.username, datasource.password),
                    verify_certs=False,
                    request_timeout=timeout,
                    max_retries=max_retries,
                    retry_on_timeout=True
                )
            else:
                es_client = AsyncElasticsearch(
                    hosts=hosts_config,
                    verify_certs=False,
                    request_timeout=timeout,
                    max_retries=max_retries,
                    retry_on_timeout=True
                )
            
            try:
                # 预检查：集群健康，便于快速定位连接/认证问题
                try:
                    await es_client.cluster.health()
                    logger.info("ES健康检查通过")
                except ESConnectionTimeout as e:
                    logger.error(f"ES健康检查超时 [host={host_str} port={port_int} scheme={scheme} timeout={timeout}] : {e}")
                    raise
                except ESConnectionError as e:
                    logger.error(f"ES连接失败 [host={host_str} port={port_int} scheme={scheme}] : {e}")
                    raise
                except AuthenticationException as e:
                    logger.error(f"ES认证失败 [host={host_str} port={port_int} scheme={scheme}] : {e}")
                    raise

                # 构建查询体
                base_query = query_data.get("query", {"match_all": {}})
                query = base_query
                
                # 滚动查询参数：单页大小与总上限（默认100万，可通过数据源配置覆盖）
                params = datasource.connection_params or {}
                try:
                    export_max_rows = int(params.get('export_max_rows', 1000000))
                except Exception:
                    export_max_rows = 1000000
                try:
                    page_size = int(params.get('export_page_size', 10000))
                except Exception:
                    page_size = 10000

                # 保留用户选择的字段
                source_fields = query_data.get("_source")

                # 执行滚动查询：按 _doc 排序以获得稳定的分页性能
                all_hits = []
                total_value = None
                took_total = 0
                pages_fetched = 0
                scroll_id = None
                scroll_keep_alive = "5m"

                try:
                    first = await es_client.search(
                        index=query_data.get("index", ""),
                        query=query,
                        size=page_size,
                        sort=["_doc"],
                        source=source_fields,
                        scroll=scroll_keep_alive,
                        request_cache=False
                    )
                except ESConnectionTimeout as e:
                    logger.error(f"ES查询超时 [index={query_data.get('index')} host={host_str} port={port_int} scheme={scheme} timeout={timeout}] : {e}")
                    raise
                except ApiError as e:
                    # 详细记录错误信息，并进行一次回退：去掉sort重试
                    detail = getattr(e, 'body', None) or str(e)
                    logger.error(f"ES初始滚动查询失败(ApiError): {detail}")
                    logger.info("尝试回退：移除sort后再次执行初始查询")
                    first = await es_client.search(
                        index=query_data.get("index", ""),
                        query=query,
                        size=page_size,
                        source=source_fields,
                        scroll=scroll_keep_alive,
                        request_cache=False
                    )

                try:
                    total_meta = first.get('hits', {}).get('total')
                    total_value = (total_meta.get('value') if isinstance(total_meta, dict) else total_meta) if total_meta is not None else None
                    took_total += int(first.get('took', 0) or 0)
                    batch_hits = first.get('hits', {}).get('hits', []) or []
                    all_hits.extend(batch_hits)
                    pages_fetched += 1
                    scroll_id = first.get('_scroll_id')
                    logger.info(f"ES滚动查询初始页: hits_count={len(batch_hits)}, total={total_value}, took={first.get('took')}ms, page_size={page_size}, cap={export_max_rows}")
                except Exception:
                    logger.info("ES滚动查询初始页: 无法解析摘要信息")

                # 继续滚动直到达到上限或无更多数据
                try:
                    while scroll_id and len(all_hits) < export_max_rows:
                        try:
                            next_page = await es_client.scroll(scroll_id=scroll_id, scroll=scroll_keep_alive)
                        except ApiError as e:
                            detail = getattr(e, 'body', None) or str(e)
                            logger.error(f"ES滚动查询下一页失败(ApiError): {detail}")
                            break
                        batch_hits = next_page.get('hits', {}).get('hits', []) or []
                        if not batch_hits:
                            logger.info("ES滚动查询：无更多数据，结束滚动")
                            break
                        all_hits.extend(batch_hits)
                        pages_fetched += 1
                        took_total += int(next_page.get('took', 0) or 0)
                        scroll_id = next_page.get('_scroll_id') or scroll_id
                        logger.info(f"ES滚动查询第{pages_fetched}页: 累计={len(all_hits)} / cap={export_max_rows}")
                finally:
                    if scroll_id:
                        try:
                            await es_client.clear_scroll(scroll_id=scroll_id)
                            logger.info("已清理ES滚动上下文")
                        except Exception as ce:
                            logger.warning(f"清理ES滚动上下文失败: {ce}")

                # 截断到上限
                if len(all_hits) > export_max_rows:
                    all_hits = all_hits[:export_max_rows]

                # 汇总返回结构与摘要
                result = {
                    'hits': {
                        'total': total_value,
                        'hits': all_hits
                    },
                    'took': took_total,
                    'scroll_used': True,
                    'pages_fetched': pages_fetched,
                    'page_size': page_size,
                    'export_max_rows': export_max_rows
                }
                logger.info(f"ES滚动查询完成: total={total_value}, returned={len(all_hits)}, pages={pages_fetched}, took_total={took_total}ms")
                return result
                
            finally:
                await es_client.close()
            
        except Exception as e:
            logger.error(
                f"执行ES查询失败: {e} | datasource_id={datasource_id}, host={getattr(datasource, 'host', 'unknown')}, "
                f"port={getattr(datasource, 'port', 'unknown')}, index={query_data.get('index')}"
            )
            raise
    
    async def _generate_csv_zip_files(self, query_result: Dict[str, Any], package_name: str) -> bytes:
        """生成CSV文件并打包为ZIP"""
        try:
            hits = query_result.get('hits', {}).get('hits', [])
            if not hits:
                raise ValueError("无数据可导出")
            
            # 获取所有字段名
            all_fields = set()
            for hit in hits:
                source = hit.get('_source', {})
                all_fields.update(source.keys())
            
            fields = sorted(list(all_fields))
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                csv_files = []
                rows_per_file = 100000  # 每个CSV文件最多10万行
                
                # 分批生成CSV文件
                for i in range(0, len(hits), rows_per_file):
                    batch_hits = hits[i:i + rows_per_file]
                    file_index = i // rows_per_file + 1
                    csv_filename = f"{package_name}_part_{file_index}.csv"
                    csv_filepath = os.path.join(temp_dir, csv_filename)
                    
                    # 生成CSV文件
                    with open(csv_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=fields)
                        writer.writeheader()
                        
                        for hit in batch_hits:
                            source = hit.get('_source', {})
                            # 处理复杂数据类型
                            row_data = {}
                            for field in fields:
                                value = source.get(field, '')
                                if isinstance(value, (dict, list)):
                                    value = json.dumps(value, ensure_ascii=False)
                                row_data[field] = value
                            writer.writerow(row_data)
                    
                    csv_files.append(csv_filepath)
                
                # 创建ZIP文件
                zip_filename = os.path.join(temp_dir, f"{package_name}_export.zip")
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for csv_file in csv_files:
                        zipf.write(csv_file, os.path.basename(csv_file))
                
                # 读取ZIP文件内容到内存
                with open(zip_filename, 'rb') as zip_file:
                    zip_content = zip_file.read()
                
                # 返回ZIP文件内容
                return zip_content
                
        except Exception as e:
            logger.error(f"生成CSV ZIP文件失败: {e}")
            raise