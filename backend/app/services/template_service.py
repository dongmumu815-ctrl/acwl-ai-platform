from typing import Dict, Any, List
import json
import logging
import uuid
from app.services.db_service import RouterDBService

logger = logging.getLogger(__name__)

class TemplateService:
    def __init__(self):
        self.db_service = RouterDBService()
        # 使用 task_db 别名并访问 cvs2db.import_templates 表
        self.db_alias = 'task_db'
        self.table_name = 'cvs2db.import_templates'

    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建模板
        """
        try:
            logger.info(f"开始创建模板: {template_data.get('name')}")
            logger.info(f"创建数据: {template_data}")
            
            fields = []
            values = []
            
            # 1. 处理 ID
            # 如果传入了 id 或 template_id，则使用传入的值，否则生成 UUID
            template_id = template_data.get('id') or template_data.get('template_id')
            if not template_id:
                template_id = str(uuid.uuid4())
            
            fields.append("id")
            values.append(f"'{template_id.replace("'", "''").replace("%", "%%")}'")
            
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
                'created_by': ['created_by'],
                'config': ['config']
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
                                    # 数据库enum不支持json，映射为excel或csv，或者如果允许null则为null
                                    # 检查数据库定义，file_type 是 enum('excel','csv','minio')
                                    # 对于API导入，可能没有文件类型，或者我们应该新增一种类型？
                                    # 暂时映射为 minio 或者 excel，或者不存这个字段
                                    # 既然是API映射，其实不涉及文件，file_type 可能不适用
                                    # 但为了避免报错，我们可以不存这个字段，或者存一个合法的默认值
                                    # 如果是API数据源，file_type 可以为空吗？ schema检查显示是 nullable YES
                                    # 所以如果不是允许的值，我们就不存
                                    if val_str not in ['excel', 'csv', 'minio']:
                                        continue
                            
                            # 特殊处理 import_mode
                            if db_field == 'import_mode':
                                val_str = str(val).lower()
                                # 数据库枚举: enum('insert','replace','append','update')
                                if val_str == 'upsert':
                                    # upsert 对应 replace (或者 update，视业务逻辑而定，通常 upsert -> replace)
                                    val = 'replace'
                                elif val_str not in ['insert', 'replace', 'append', 'update']:
                                    # 非法值设为 NULL
                                    val = None
                                    if val is None: # Double check logic flow
                                        continue

                            fields.append(db_field)
                            if isinstance(val, (int, float)):
                                values.append(str(val))
                            else:
                                values.append(f"'{str(val).replace("'", "''").replace("%", "%%")}'")
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
                            values.append("1" if val else "0")
                        break
            
            # 默认 is_active = 1
            if 'is_active' not in fields:
                fields.append("is_active")
                values.append("1")

            # 4. JSON 字段
            json_mappings = {
                'target_database': ['target_database'],
                'field_mappings': ['field_mappings'],
                'custom_fields': ['custom_fields'],
                'validation_rules': ['validation_rules'],
                'global_settings': ['global_settings'],
                'data_transform_config': ['data_transform_config']
            }
            
            for db_field, input_fields in json_mappings.items():
                for input_field in input_fields:
                    if input_field in template_data:
                        val = template_data[input_field]
                        if val is not None:
                            fields.append(db_field)
                            values.append("'{}'".format(json.dumps(val).replace("'", "''").replace("%", "%%")))
                        break

            # 5. 特殊处理 execution_config
            # 优先使用传入的 executionConfig，如果没有，则构建一个
            execution_config = template_data.get('executionConfig', {})
            if not isinstance(execution_config, dict):
                 execution_config = {}
            
            # 将一些额外配置也同步到 execution_config 中，以防万一
            sync_to_config_fields = ['file_type', 'import_mode', 'has_header', 'batch_size']
            for field in sync_to_config_fields:
                if field in template_data:
                    execution_config[field] = template_data[field]
            
            # 如果 execution_config 有内容，则保存
            if execution_config:
                fields.append("execution_config")
                values.append("'{}'".format(json.dumps(execution_config).replace("'", "''").replace("%", "%%")))
                
                # 特殊逻辑：如果 batch_size 在 execution_config 中但没在 template_data 中，也尝试提取到 batch_size 字段
                if 'batchSize' in execution_config and 'batch_size' not in fields:
                    fields.append("batch_size")
                    values.append(str(execution_config['batchSize']))

            # 6. 时间字段
            fields.append("created_at")
            values.append("NOW()")
            
            fields.append("updated_at")
            values.append("NOW()")

            if not fields:
                return {
                    "success": False,
                    "message": "没有需要保存的字段"
                }
            
            insert_sql = f"""
                INSERT INTO {self.table_name} ({', '.join(fields)})
                VALUES ({', '.join(values)})
            """
            
            logger.info(f"执行SQL: {insert_sql}")
            
            # 使用 execute_batch_sql 以确保提交
            # 传入一个空元组作为参数列表，表示执行一次
            result = self.db_service.execute_batch_sql(self.db_alias, insert_sql, [()])
            
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
            logger.info(f"更新数据: {template_data}")
            
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
                'created_by': ['created_by'],
                'config': ['config']
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
            json_mappings = {
                'target_database': ['target_database'],
                'field_mappings': ['field_mappings'],
                'custom_fields': ['custom_fields'],
                'validation_rules': ['validation_rules'],
                'global_settings': ['global_settings'],
                'data_transform_config': ['data_transform_config']
            }
            
            for db_field, input_fields in json_mappings.items():
                for input_field in input_fields:
                    if input_field in template_data:
                        val = template_data[input_field]
                        update_fields.append(f"{db_field} = %s")
                        if val is None:
                            update_params.append(None)
                        else:
                            update_params.append(json.dumps(val))
                        break

            # 4. 特殊处理 execution_config
            execution_config = template_data.get('executionConfig', {})
            if not isinstance(execution_config, dict):
                 execution_config = {}
            
            sync_to_config_fields = ['file_type', 'import_mode', 'has_header', 'batch_size']
            has_extra = False
            for field in sync_to_config_fields:
                if field in template_data:
                    execution_config[field] = template_data[field]
                    has_extra = True
            
            if 'executionConfig' in template_data or has_extra:
                 update_fields.append("execution_config = %s")
                 update_params.append(json.dumps(execution_config))
                 
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
            result = self.db_service.execute_batch_sql(self.db_alias, update_sql, [tuple(update_params)])
            
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
