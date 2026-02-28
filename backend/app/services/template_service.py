from typing import Dict, Any, List
import json
import uuid
from datetime import datetime
from loguru import logger
import pymysql
from app.services.db_service import RouterDBService
from app.services.minio_service import minio_service
from app.core.config import settings
from app.core.security import decrypt_datasource_password

def _sanitize_template_data_for_log(template_data: Any) -> Any:
    if not isinstance(template_data, dict):
        return template_data
    sanitized = dict(template_data)

    target_db = sanitized.get("target_database")
    if isinstance(target_db, dict):
        target_db = dict(target_db)
        if "password" in target_db and target_db["password"] is not None:
            target_db["password"] = "******"
        sanitized["target_database"] = target_db

    config = sanitized.get("config")
    if isinstance(config, dict):
        config = dict(config)
        minio_cfg = config.get("minioConfig")
        if isinstance(minio_cfg, dict):
            minio_cfg = dict(minio_cfg)
            if "access_key" in minio_cfg and minio_cfg["access_key"] is not None:
                minio_cfg["access_key"] = "******"
            if "secret_key" in minio_cfg and minio_cfg["secret_key"] is not None:
                minio_cfg["secret_key"] = "******"
            config["minioConfig"] = minio_cfg
        sanitized["config"] = config

    return sanitized

# 定义 JSON 字段映射 (模块级常量)
JSON_MAPPINGS = {
    'target_database': ['target_database'],
    'field_mappings': ['field_mappings'],
    'custom_fields': ['custom_fields'],
    'validation_rules': ['validation_rules'],
    'global_settings': ['global_settings'],
    'data_transform_config': ['data_transform_config'],
    'config': ['config']
}

class TemplateService:
    def __init__(self):
        self.db_service = RouterDBService()
        # 使用 task_db 别名并访问 cvs2db.import_templates 表
        self.db_alias = 'task_db'
        self.table_name = 'cvs2db.import_templates'

    def _process_and_upload_config(self, template_data: Dict[str, Any]) -> str:
        """
        处理非自定义字段并上传配置到MinIO
        Returns:
            str: MinIO对象路径 (如果成功) 或 None
        """
        try:
            def _safe_segment(value: Any, default: str) -> str:
                if value is None:
                    return default
                s = str(value).strip()
                if not s:
                    return default
                return ''.join(ch if (ch.isalnum() or ch in '-_.') else '_' for ch in s)

            field_mappings = template_data.get('field_mappings')
            if not field_mappings or not isinstance(field_mappings, list):
                return None
            
            # 过滤非自定义字段
            non_custom_field_names: List[str] = []
            for mapping in field_mappings:
                is_custom = mapping.get('isCustom')
                # 只处理非自定义字段，且必须有 sourceName 和 targetName
                if not is_custom and mapping.get('sourceName') and mapping.get('targetName'):
                    non_custom_field_names.append(str(mapping.get('sourceName')))
            
            if not non_custom_field_names:
                return None
                
            now = datetime.now()

            batch_id = (
                template_data.get('batch_id')
                or template_data.get('batchId')
                or template_data.get('link_read_id')
                or template_data.get('linkReadId')
                or (template_data.get('executionConfig') or {}).get('batch_id')
                or str(uuid.uuid4())
            )
            api_code = template_data.get('api_code') or template_data.get('apiCode') or ''
            api_id = template_data.get('api_id') or template_data.get('apiId')
            request_id = template_data.get('request_id') or template_data.get('requestId')
            customer_id = template_data.get('customer_id') or template_data.get('customerId')

            batch_id_seg = _safe_segment(batch_id, 'unknown')
            api_code_seg = _safe_segment(api_code, 'api')
            request_id_seg = _safe_segment(request_id, 'None')
            ts_seg = now.strftime('%Y%m%d_%H%M%S')
            date_seg = now.strftime('%Y/%m/%d')

            object_path = f"batchfile/{date_seg}/{batch_id_seg}/{api_code_seg}_{request_id_seg}_{ts_seg}.json"

            data_item: Dict[str, Any] = {name: "" for name in non_custom_field_names}

            json_data = {
                "data": {
                    "data_list": [data_item]
                }
            }
            
            # 上传
            return minio_service.upload_json_data(json_data, object_path)
            
        except Exception as e:
            logger.error(f"处理并上传配置失败: {e}")
            return None

    def _fill_target_database_from_datasource(self, template_data: Dict[str, Any]) -> None:
        execution_config = template_data.get('executionConfig') or template_data.get('execution_config') or {}
        if not isinstance(execution_config, dict):
            return
        datasource_id = (
            (template_data.get('target_database') or {}).get('datasource_id')
            or (template_data.get('target_database') or {}).get('datasourceId')
            or execution_config.get('datasource_id')
            or execution_config.get('datasourceId')
            or template_data.get('datasource_id')
            or template_data.get('datasourceId')
        )
        if not datasource_id:
            return
        try:
            datasource_id_int = int(str(datasource_id).strip())
            schema_from_execution = execution_config.get('schema')
            if schema_from_execution is not None:
                schema_from_execution = str(schema_from_execution).strip() or None
            sql_select_fields = """
                SELECT
                    name,
                    description,
                    datasource_type,
                    host,
                    port,
                    database_name,
                    username,
                    password,
                    connection_params,
                    pool_config,
                    is_enabled,
                    status,
                    last_test_time,
                    last_test_result,
                    created_by,
                    created_at,
                    updated_at
                FROM acwl_datasources
                WHERE id = %s
                LIMIT 1
            """

            try:
                conn = pymysql.connect(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    database=settings.DB_NAME,
                    charset=settings.DB_CHARSET,
                    cursorclass=pymysql.cursors.DictCursor,
                )
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(sql_select_fields, (datasource_id_int,))
                        row = cursor.fetchone()
                finally:
                    conn.close()

                if row:
                    password_encrypted = row.get('password')
                    decrypted_password = decrypt_datasource_password(password_encrypted) if password_encrypted else None
                    datasource_type = row.get('datasource_type')
                    normalized_type = 'mysql' if str(datasource_type).lower() in ('mysql', 'doris') else datasource_type
                    database_value = schema_from_execution or row.get('database_name')
                    target_db = {
                        "host": row.get('host'),
                        "port": str(row.get('port')) if row.get('port') is not None else None,
                        "type": normalized_type,
                        "database": database_value,
                        "username": row.get('username'),
                        "password": decrypted_password,
                    }

                    template_data['target_database'] = target_db
                    password_to_log = target_db.get('password')
                    if password_to_log not in (None, '', '******'):
                        logger.info(str(password_to_log))
                    return
            except Exception:
                pass

            sql = f"""
                SELECT
                    name,
                    description,
                    datasource_type,
                    host,
                    port,
                    database_name,
                    username,
                    password,
                    connection_params,
                    pool_config,
                    is_enabled,
                    status,
                    last_test_time,
                    last_test_result,
                    created_by,
                    created_at,
                    updated_at
                FROM acwl_datasources
                WHERE id = {datasource_id_int}
                LIMIT 1
            """

            result = None
            rows: List[Any] = []
            for db_alias in ("cloud_db", "api_system", "task_db"):
                result = self.db_service.execute_sql(db_alias, sql)
                if result and result.get('success') and (result.get('data') or []):
                    rows = result.get('data') or []
                    break

            if not result or not result.get('success'):
                logger.error(f"加载数据源配置失败: {result.get('error') if isinstance(result, dict) else result}")
                return

            if not rows:
                logger.warning(f"未找到数据源: {datasource_id}")
                return

            row = rows[0]
            if isinstance(row, dict):
                password_encrypted = row.get('password')
                decrypted_password = decrypt_datasource_password(password_encrypted) if password_encrypted else None
                datasource_type = row.get('datasource_type')
                normalized_type = 'mysql' if str(datasource_type).lower() in ('mysql', 'doris') else datasource_type
                database_value = schema_from_execution or row.get('database_name')
                target_db = {
                    "host": row.get('host'),
                    "port": str(row.get('port')) if row.get('port') is not None else None,
                    "type": normalized_type,
                    "database": database_value,
                    "username": row.get('username'),
                    "password": decrypted_password,
                }
            else:
                password_encrypted = row[7] if len(row) > 7 else None
                decrypted_password = decrypt_datasource_password(password_encrypted) if password_encrypted else None
                datasource_type = row[2] if len(row) > 2 else None
                normalized_type = 'mysql' if str(datasource_type).lower() in ('mysql', 'doris') else datasource_type
                database_value = schema_from_execution or (row[5] if len(row) > 5 else None)
                target_db = {
                    "host": row[3] if len(row) > 3 else None,
                    "port": str(row[4]) if len(row) > 4 and row[4] is not None else None,
                    "type": normalized_type,
                    "database": database_value,
                    "username": row[6] if len(row) > 6 else None,
                    "password": decrypted_password,
                }

            template_data['target_database'] = target_db
            password_to_log = target_db.get('password')
            if password_to_log not in (None, '', '******'):
                logger.info(str(password_to_log))
        except Exception as e:
            logger.error(f"根据数据源ID补全target_database失败: {e}")

    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建模板 (使用参数化查询)
        """
        try:
            logger.info(f"开始创建模板: {template_data.get('name')}")
            logger.info(f"创建数据: {json.dumps(_sanitize_template_data_for_log(template_data), ensure_ascii=False, default=str)}")
            
            # 0. 检查模板是否存在
            template_id = template_data.get('id') or template_data.get('template_id')
            if not template_id:
                api_id = template_data.get('api_id') or template_data.get('apiId')
                try:
                    api_id_int = int(str(api_id).strip()) if api_id is not None else None
                except Exception:
                    api_id_int = None

                if api_id_int:
                    mapping_sql = f"SELECT mapping_config_id FROM custom_apis WHERE id = {api_id_int} LIMIT 1"
                    mapping_result = self.db_service.execute_sql("api_system", mapping_sql)
                    if mapping_result and mapping_result.get("success") and (mapping_result.get("data") or []):
                        row = (mapping_result.get("data") or [None])[0]
                        if isinstance(row, dict):
                            template_id = row.get("mapping_config_id")
                        elif isinstance(row, (list, tuple)) and row:
                            template_id = row[0]
                        if template_id is not None:
                            template_id = str(template_id).strip() or None

            if template_id:
                # 尝试查询是否存在
                check_sql = f"SELECT id FROM {self.table_name} WHERE id = '{template_id}'"
                check_result = self.db_service.execute_sql(self.db_alias, check_sql)
                if check_result.get('success') and check_result.get('data'):
                    return self.update_template(template_id, template_data)

            # 先尝试根据数据源ID补全 target_database（含解密密码）
            self._fill_target_database_from_datasource(template_data)

            fields = []
            placeholders = []
            params = []
            
            # 1. 处理 ID
            # 如果传入了 id 或 template_id，则使用传入的值，否则生成 UUID
            if not template_id:
                template_id = str(uuid.uuid4())
            
            fields.append("id")
            placeholders.append("%s")
            params.append(template_id)
            
            # 2. 基础字段映射 (DB字段 -> 传入字段列表)
            # 支持多种传入字段名，优先匹配第一个存在的
            field_mappings = {
                'name': ['name'],
                'description': ['description'],
                'excel_filename': ['excel_filename'],
                'sheet_name': ['sheet_name'],
                'target_table': ['target_table'],
                'header_row': ['header_row', 'header_row_index'],
                'data_start_row': ['data_start_row', 'data_start_row_index'],
                'batch_size': ['batch_size'],
                'file_type': ['file_type'],
                'import_mode': ['import_mode'],
                'created_by': ['created_by']
            }
            
            for db_field, input_fields in field_mappings.items():
                for input_field in input_fields:
                    if input_field in template_data:
                        val = template_data[input_field]
                        if val is not None:
                            # 特殊处理 file_type
                            if db_field == 'file_type':
                                val_str = str(val).lower()
                                if val_str in ['xlsx', 'xls']:
                                    val = 'excel'
                                elif val_str == 'json':
                                    if val_str not in ['excel', 'csv', 'minio']:
                                        continue
                            
                            # 特殊处理 import_mode
                            if db_field == 'import_mode':
                                val_str = str(val).lower()
                                if val_str == 'upsert':
                                    val = 'replace'
                                elif val_str not in ['insert', 'replace', 'append', 'update']:
                                    val = None
                                    if val is None:
                                        continue

                            fields.append(db_field)
                            placeholders.append("%s")
                            params.append(val)
                        
                        break # Found a match, stop looking for other aliases

            # 3. Boolean 字段 (需要转换为 1/0)
            bool_mappings = {
                'has_header': ['has_header'],
                'is_active': ['is_active']
            }
            
            for db_field, input_fields in bool_mappings.items():
                for input_field in input_fields:
                    if input_field in template_data:
                        val = template_data[input_field]
                        if val is not None:
                            fields.append(db_field)
                            placeholders.append("%s")
                            params.append(1 if val else 0)
                        break
            
            # 默认 is_active = 1
            if 'is_active' not in fields:
                fields.append("is_active")
                placeholders.append("%s")
                params.append(1)

            # 4. JSON 字段
            # json_mappings 已在上面定义
            
            for db_field, input_fields in JSON_MAPPINGS.items():
                for input_field in input_fields:
                    if input_field in template_data:
                        val = template_data[input_field]
                        if val is not None:
                            # 安全处理：如果字段是 target_database，确保写入解密后的密码
                            if db_field == 'target_database' and isinstance(val, dict):
                                pwd = val.get('password')
                                filled = None
                                if (pwd is None) or (pwd == '******'):
                                    self._fill_target_database_from_datasource(template_data)
                                    filled = template_data.get('target_database')
                                    if isinstance(filled, dict):
                                        val = filled
                                        pwd = val.get('password')

                                if not (pwd and pwd != '******'):
                                    val = val.copy()
                                    if 'password' in val:
                                        del val['password']
                            
                            fields.append(db_field)
                            placeholders.append("%s")
                            params.append(json.dumps(val, ensure_ascii=False, default=str))
                        break

            # 5. 特殊处理 execution_config
            # 优先使用传入的 executionConfig，如果没有，则构建一个
            execution_config = template_data.get('executionConfig', {})
            if not isinstance(execution_config, dict):
                 execution_config = {}
            
            # 上传非自定义字段配置到 MinIO
            minio_path = self._process_and_upload_config(template_data)
            if minio_path:
                execution_config['object'] = minio_path
                
                # 构造 minioConfig 并保存到 config 字段
                minio_config = {
                    "endpoint": settings.MINIO_ENDPOINT,
                    "access_key": settings.MINIO_ACCESS_KEY,
                    "secret_key": settings.MINIO_SECRET_KEY,
                    "secure": settings.MINIO_SECURE,
                    "region": settings.MINIO_REGION,
                    "bucket": settings.MINIO_BUCKET_NAME,
                    "object": minio_path,
                    "sheet": "",
                    "hasHeader": template_data.get('has_header', True),
                    "headerRow": template_data.get('header_row', 1),
                    "dataStartRow": template_data.get('data_start_row', 2),
                    "json_path": template_data.get('sheet_name', 'data.data_list')
                }
                template_data['config'] = {"minioConfig": minio_config}
                config_json = json.dumps(template_data['config'])
                if "config" in fields:
                    params[fields.index("config")] = config_json
                else:
                    fields.append("config")
                    placeholders.append("%s")
                    params.append(config_json)
            
            # 将一些额外配置也同步到 execution_config 中，以防万一
            sync_to_config_fields = ['file_type', 'import_mode', 'has_header', 'batch_size']
            for field in sync_to_config_fields:
                if field in template_data:
                    execution_config[field] = template_data[field]
            
            # 如果 execution_config 有内容，则保存
            if execution_config:
                fields.append("execution_config")
                placeholders.append("%s")
                params.append(json.dumps(execution_config, ensure_ascii=False, default=str))
                
                # 特殊逻辑：如果 batch_size 在 execution_config 中但没在 template_data 中，也尝试提取到 batch_size 字段
                if 'batchSize' in execution_config and 'batch_size' not in fields:
                    fields.append("batch_size")
                    placeholders.append("%s")
                    params.append(execution_config['batchSize'])

            # 6. 时间字段
            fields.append("created_at")
            placeholders.append("NOW()")
            
            fields.append("updated_at")
            placeholders.append("NOW()")

            # Safety Check: Ensure params match placeholders
            s_count = sum(1 for p in placeholders if p == '%s')
            if s_count != len(params):
                logger.error(f"CRITICAL: Placeholder count ({s_count}) does not match params count ({len(params)})")
                logger.error(f"Placeholders: {placeholders}")
                logger.error(f"Params: {params}")
                return {
                    "success": False,
                    "message": f"内部错误: 参数数量不匹配 ({s_count} vs {len(params)})"
                }

            if not fields:
                return {
                    "success": False,
                    "message": "没有需要保存的字段"
                }
            
            insert_sql = f"""
                INSERT INTO {self.table_name} ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
            """
            
            logger.info(f"执行SQL: {insert_sql}")
            
            # 使用 execute_batch_sql 以确保提交
            # 传入参数列表，这里只有一组参数，所以包裹在列表中
            # 注意：某些 RPC 机制可能对 tuple 支持不好，尝试使用 list
            result = self.db_service.execute_batch_sql(self.db_alias, insert_sql, [params])
            
            logger.info(f"SQL执行结果: {result}")
            
            if not result.get('success'):
                return {
                    "success": False,
                    "message": f"创建模板失败: {result.get('error')}"
                }
            
            # 构造完整的返回数据
            # 既然已经知道 ID 和所有输入数据，我们可以直接构造返回对象，避免再次查询
            # 注意：这里我们尽可能返回前端可能需要的字段
            response_data = {
                "id": template_id,
                **template_data
            }
            # 确保 JSON 字段是对象而不是字符串（如果输入是对象的话）
            # template_data 中的 executionConfig 等本来就是对象，所以直接返回即可
            
            return {
                "success": True,
                "message": "模板创建成功",
                "data": response_data
            }
            
        except Exception as e:
            logger.error(f"创建模板失败: {str(e)}")
            return {
                "success": False,
                "message": f"创建模板失败: {str(e)}"
            }

    def get_template(self, template_id: str) -> Dict[str, Any]:
        """
        获取单个模板详情
        """
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE id = '{template_id}'"
            result = self.db_service.execute_sql(self.db_alias, sql)
            
            if not result.get('success'):
                return {
                    "success": False,
                    "message": f"查询失败: {result.get('error')}"
                }
            
            data = result.get('data')
            if not data or len(data) == 0:
                return {
                    "success": False,
                    "message": "模板不存在"
                }
            
            template = data[0]
            self._process_template_fields(template)
            
            return {
                "success": True,
                "data": template
            }
            
        except Exception as e:
            logger.error(f"获取模板失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取模板失败: {str(e)}"
            }

    def get_template_list(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取模板列表
        """
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE 1=1"
            
            if filters:
                if filters.get('id'):
                    safe_id = str(filters['id']).replace("'", "''")
                    sql += f" AND id = '{safe_id}'"
                if filters.get('name'):
                    safe_name = str(filters['name']).replace("'", "''")
                    sql += f" AND name LIKE '%{safe_name}%'"
                if filters.get('is_active') is not None:
                    # Handle boolean or string representation of boolean
                    is_active = filters['is_active']
                    if isinstance(is_active, str):
                        is_active = is_active.lower() == 'true' or is_active == '1'
                    sql += f" AND is_active = {1 if is_active else 0}"
                if filters.get('file_type'):
                    safe_type = str(filters['file_type']).replace("'", "''")
                    sql += f" AND file_type = '{safe_type}'"

            sql += " ORDER BY created_at DESC"
            
            result = self.db_service.execute_sql(self.db_alias, sql)
            
            if not result.get('success'):
                return {
                    "success": False,
                    "message": f"查询失败: {result.get('error')}"
                }
            
            templates = result.get('data', [])
            for template in templates:
                self._process_template_fields(template)
            
            return {
                "success": True,
                "data": templates
            }
            
        except Exception as e:
            logger.error(f"获取模板列表失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取模板列表失败: {str(e)}"
            }

    def _process_template_fields(self, template: Dict[str, Any]):
        """
        处理模板字段：JSON反序列化，布尔值转换等
        """
        # JSON 字段
        json_fields = ['target_database', 'field_mappings', 'custom_fields', 'validation_rules', 'global_settings', 'data_transform_config', 'execution_config', 'config']
        for field in json_fields:
            if template.get(field):
                try:
                    if isinstance(template[field], str):
                        template[field] = json.loads(template[field])
                except Exception as e:
                    logger.warning(f"Failed to parse JSON for field {field}: {e}")
        
        # Boolean 字段
        bool_fields = ['has_header', 'is_active']
        for field in bool_fields:
            if field in template:
                # Mysql TINYINT(1) returns 0/1, convert to bool if needed
                # But frontend might expect 0/1 or true/false. Usually 0/1 is fine for JS, but true/false is better.
                val = template[field]
                if val == 1:
                    template[field] = True
                elif val == 0:
                    template[field] = False
        
        # DateTime fields usually handled by driver or return as string/datetime obj. 
        # If datetime obj, might need serialization.
        # RouterDBService/DataService likely returns standard python types.
        # FastAPI will handle JSON serialization of datetime objects.

    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新模板 (使用参数化查询)
        """
        try:
            logger.info(f"开始更新模板: {template_id}")
            logger.info(f"更新数据: {json.dumps(_sanitize_template_data_for_log(template_data), ensure_ascii=False, default=str)}")

            # 更新前同样根据数据源ID补全 target_database（含解密密码）
            self._fill_target_database_from_datasource(template_data)
            
            # 构建更新SQL
            update_fields = []
            update_params = []
            
            # 1. 基础字段映射
            field_mappings = {
                'name': ['name'],
                'description': ['description'],
                'excel_filename': ['excel_filename'],
                'sheet_name': ['sheet_name'],
                'target_table': ['target_table'],
                'header_row': ['header_row', 'header_row_index'],
                'data_start_row': ['data_start_row', 'data_start_row_index'],
                'batch_size': ['batch_size'],
                'file_type': ['file_type'],
                'import_mode': ['import_mode'],
                'created_by': ['created_by']
            }

            for db_field, input_fields in field_mappings.items():
                for input_field in input_fields:
                    if input_field in template_data:
                        val = template_data[input_field]
                        
                        # 特殊处理 file_type
                        if db_field == 'file_type' and val is not None:
                             val_str = str(val).lower()
                             if val_str in ['xlsx', 'xls']:
                                 val = 'excel'
                             elif val_str not in ['excel', 'csv', 'minio']:
                                 val = None

                        # 特殊处理 import_mode
                        if db_field == 'import_mode' and val is not None:
                             val_str = str(val).lower()
                             if val_str == 'upsert':
                                 val = 'replace'
                             elif val_str not in ['insert', 'replace', 'append', 'update']:
                                 val = None

                        update_fields.append(f"{db_field} = %s")
                        update_params.append(val)
                        break # Found match

            # 2. Boolean 字段
            bool_mappings = {
                'has_header': ['has_header'],
                'is_active': ['is_active']
            }
            
            for db_field, input_fields in bool_mappings.items():
                for input_field in input_fields:
                    if input_field in template_data:
                        val = template_data[input_field]
                        update_fields.append(f"{db_field} = %s")
                        update_params.append(1 if val else 0)
                        break

            # 3. JSON 字段
            
            for db_field, input_fields in JSON_MAPPINGS.items():
                for input_field in input_fields:
                    if input_field in template_data:
                        val = template_data[input_field]
                        
                        # 安全处理：如果字段是 target_database，确保写入解密后的密码
                        if db_field == 'target_database' and isinstance(val, dict):
                            pwd = val.get('password')
                            if (pwd is None) or (pwd == '******'):
                                self._fill_target_database_from_datasource(template_data)
                                filled = template_data.get('target_database')
                                if isinstance(filled, dict):
                                    val = filled
                                    pwd = val.get('password')

                            if not (pwd and pwd != '******'):
                                val = val.copy()
                                if 'password' in val:
                                    del val['password']

                        update_fields.append(f"{db_field} = %s")
                        if val is None:
                            update_params.append(None)
                        else:
                            update_params.append(json.dumps(val, ensure_ascii=False, default=str))
                        break

            # 4. 特殊处理 execution_config
            execution_config = template_data.get('executionConfig', {})
            if not isinstance(execution_config, dict):
                 execution_config = {}
            
            # 上传非自定义字段配置到 MinIO
            minio_path = self._process_and_upload_config(template_data)
            has_extra = False
            if minio_path:
                execution_config['object'] = minio_path
                has_extra = True
                
                # 构造 minioConfig 并保存到 config 字段
                minio_config = {
                    "endpoint": settings.MINIO_ENDPOINT,
                    "access_key": settings.MINIO_ACCESS_KEY,
                    "secret_key": settings.MINIO_SECRET_KEY,
                    "secure": settings.MINIO_SECURE,
                    "region": settings.MINIO_REGION,
                    "bucket": settings.MINIO_BUCKET_NAME,
                    "object": minio_path,
                    "sheet": "",
                    "hasHeader": template_data.get('has_header', True),
                    "headerRow": template_data.get('header_row', 1),
                    "dataStartRow": template_data.get('data_start_row', 2),
                    "json_path": template_data.get('sheet_name', 'data.data_list')
                }
                template_data['config'] = {"minioConfig": minio_config}
                config_json = json.dumps(template_data['config'], ensure_ascii=False, default=str)
                for i, field in enumerate(update_fields):
                    if field.split("=")[0].strip() == "config":
                        update_params[i] = config_json
                        break
                else:
                    update_fields.append("config = %s")
                    update_params.append(config_json)

            sync_to_config_fields = ['file_type', 'import_mode', 'has_header', 'batch_size']
            for field in sync_to_config_fields:
                if field in template_data:
                    execution_config[field] = template_data[field]
                    has_extra = True
            
            if 'executionConfig' in template_data or has_extra:
                 update_fields.append("execution_config = %s")
                 update_params.append(json.dumps(execution_config, ensure_ascii=False, default=str))
                 
                 # 如果 batch_size 没有被直接更新，尝试从 execution_config 同步
                 if 'batchSize' in execution_config and 'batch_size' not in [f.split('=')[0].strip() for f in update_fields]:
                      update_fields.append("batch_size = %s")
                      update_params.append(execution_config['batchSize'])

            if not update_fields:
                return {
                    "success": False,
                    "message": "没有需要更新的字段"
                }
            
            update_fields.append("updated_at = NOW()")
            
            update_sql = f"""
                UPDATE {self.table_name}
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            update_params.append(template_id)
            
            logger.info(f"执行SQL: {update_sql}")
            
            # 使用 execute_batch_sql 以确保提交，传入参数列表
            # 同 create_template，使用 list 包裹参数
            result = self.db_service.execute_batch_sql(self.db_alias, update_sql, [update_params])
            
            if not result.get('success'):
                return {
                    "success": False,
                    "message": f"更新模板失败: {result.get('error')}"
                }
            
            # 为了满足前端接口定义，尝试返回更新后的完整对象
            # 这需要再进行一次查询
            updated_template = self.get_template(template_id)
            if updated_template.get('success'):
                 return {
                    "success": True,
                    "message": "模板更新成功",
                    "data": updated_template.get('data')
                }
            
            # 如果查询失败（不太可能），至少返回成功状态
            return {
                "success": True,
                "message": "模板更新成功"
            }
            
        except Exception as e:
            logger.error(f"更新模板失败: {str(e)}")
            return {
                "success": False,
                "message": f"更新模板失败: {str(e)}"
            }

template_service = TemplateService()
