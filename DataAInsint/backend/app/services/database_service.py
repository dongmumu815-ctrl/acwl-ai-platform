import oracledb
import pymysql
from sqlalchemy import create_engine, text
from typing import List, Dict, Any, Tuple
import time
import os
from urllib.parse import quote_plus
from app.models.schemas import (
    ConnectionTestResponse, TableInfo, ColumnInfo, 
    TableDetailResponse, SQLExecuteResponse
)


# 导入Oracle数据库驱动
try:
    import oracledb
    print("✅ 成功导入 oracledb 模块")
except ImportError as e:
    print(f"❌ 导入 oracledb 模块失败: {e}")
    print("ℹ️  Oracle 数据库功能将不可用，但服务器可以正常启动")
    oracledb = None

# Oracle客户端状态跟踪
oracle_thick_mode_available = False
oracle_client_error = None

# 初始化Oracle客户端为thick模式，解决DPY-3010错误
if oracledb:
    try:
        # 检查环境变量
        oracle_home = os.environ.get('ORACLE_HOME')
        ld_library_path = os.environ.get('LD_LIBRARY_PATH')
        print(f"🔍 环境变量检查:")
        print(f"   ORACLE_HOME: {oracle_home or '未设置'}")
        print(f"   LD_LIBRARY_PATH: {ld_library_path or '未设置'}")
        
        # 尝试初始化thick模式
        if oracle_home:
            # 如果设置了ORACLE_HOME环境变量，直接使用它作为客户端库路径
            print(f"🔧 使用ORACLE_HOME路径初始化: {oracle_home}")
            print(f"📁 客户端库搜索路径: {oracle_home}")
            
            # 检查常见的库文件是否存在，帮助诊断路径问题
            import platform
            if platform.system() == "Windows":
                lib_files = ["oci.dll", "oraociei23.dll", "oraociei21.dll", "oraociei19.dll"]
            else:
                lib_files = ["libclntsh.so", "libclntsh.so.23.1", "libclntsh.so.21.1", "libclntsh.so.19.1"]
            
            found_libs = []
            for lib_file in lib_files:
                lib_path = os.path.join(oracle_home, lib_file)
                if os.path.exists(lib_path):
                    found_libs.append(lib_file)
            
            if found_libs:
                print(f"✅ 在 {oracle_home} 中找到库文件: {', '.join(found_libs)}")
            else:
                print(f"⚠️  在 {oracle_home} 中未找到常见的Oracle客户端库文件")
                print(f"   预期的库文件: {', '.join(lib_files)}")
            
            oracledb.init_oracle_client(lib_dir=oracle_home)
        else:
            # 如果没有设置ORACLE_HOME，尝试自动检测
            print("🔧 尝试自动检测Oracle客户端库路径")
            oracledb.init_oracle_client()
        
        oracle_thick_mode_available = True
        print("✅ Oracle客户端成功初始化为thick模式")
    except Exception as e:
        oracle_client_error = str(e)
        print(f"⚠️  Oracle客户端初始化失败，将使用thin模式: {e}")
        print(f"   错误类型: {type(e).__name__}")
        print("ℹ️  服务器将继续启动，Oracle连接将使用thin模式（功能受限）")
else:
    print("ℹ️  oracledb 模块未安装，Oracle数据库功能不可用，但服务器可以正常启动")

class DatabaseService:
    """数据库连接和操作服务"""
    
    @staticmethod
    def _format_default_value(default_value: str, column_type: str) -> str:
        """格式化DEFAULT值，根据数据类型添加适当的引号"""
        if not default_value:
            return "NULL"
        
        # 转换为小写进行比较
        default_lower = default_value.lower().strip()
        column_type_lower = column_type.lower()
        
        # 特殊值处理
        if default_lower in ['null', 'current_timestamp', 'current_date', 'now()']:
            return default_value.upper() if default_lower == 'null' else default_value
        
        # 数字类型不需要引号
        if any(t in column_type_lower for t in ['int', 'integer', 'bigint', 'smallint', 'tinyint', 
                                               'decimal', 'numeric', 'float', 'double', 'real']):
            # 检查是否为有效数字
            try:
                float(default_value)
                return default_value
            except ValueError:
                # 如果不是数字，按字符串处理
                return f"'{default_value}'"
        
        # 布尔类型
        if 'bool' in column_type_lower or 'bit' in column_type_lower:
            if default_lower in ['true', '1', 'yes']:
                return 'TRUE'
            elif default_lower in ['false', '0', 'no']:
                return 'FALSE'
            else:
                return f"'{default_value}'"
        
        # 字符串类型需要引号
        return f"'{default_value}'"
    
    @staticmethod
    def test_connection(db_type: str, host: str, port: int, 
                      database_name: str, username: str, password: str, 
                      oracle_connection_type: str = "service_name") -> ConnectionTestResponse:
        """测试数据库连接"""
        try:
            if db_type.lower() == 'oracle':
                if not oracledb:
                    raise Exception("❌ oracledb 模块未安装，无法连接Oracle数据库")
                
                print(f"🔗 Oracle连接参数: host={host}, port={port}, database={database_name}, user={username}")
                print(f"🔧 Oracle连接类型: {oracle_connection_type}")
                
                # 显示Oracle客户端状态
                if oracle_thick_mode_available:
                    print(f"✅ Oracle客户端状态: Thick模式已启用")
                else:
                    print(f"⚠️  Oracle客户端状态: Thin模式（功能受限）")
                    if oracle_client_error:
                        print(f"   Thick模式初始化失败原因: {oracle_client_error}")
                
                # 根据连接类型构建DSN
                if oracle_connection_type == "sid":
                    dsn = f"{host}:{port}:{database_name}"  # SID方式
                    print(f"🔗 使用SID方式连接，DSN: {dsn}")
                else:
                    dsn = f"{host}:{port}/{database_name}"  # Service Name方式（默认）
                    print(f"🔗 使用Service Name方式连接，DSN: {dsn}")
                
                print(f"🚀 尝试连接Oracle数据库...")
                connection = oracledb.connect(
                    user=username,
                    password=password,
                    dsn=dsn
                )
                print(f"Oracle连接成功！")
                
                # 获取数据库版本信息
                cursor = connection.cursor()
                cursor.execute("SELECT banner FROM v$version WHERE rownum = 1")
                version = cursor.fetchone()[0]
                print(f"Oracle数据库版本: {version}")
                cursor.close()
                
                connection.close()
                print(f"Oracle连接已关闭")
            elif db_type.lower() == 'mysql':
                connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=database_name,
                    charset='utf8mb4'
                )
                connection.close()
            elif db_type.lower() == 'doris':
                # Doris 使用 MySQL 协议
                connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=database_name,
                    charset='utf8mb4'
                )
                connection.close()
            else:
                return ConnectionTestResponse(success=False, message=f"不支持的数据库类型: {db_type}")
            
            return ConnectionTestResponse(success=True, message="连接成功")
        except Exception as e:
            error_msg = f"连接失败: {str(e)}"
            print(f"数据库连接错误详情: {error_msg}")
            print(f"错误类型: {type(e).__name__}")
            
            # 对于Oracle连接错误，提供额外的诊断信息
            if db_type.lower() == 'oracle':
                print("🔍 Oracle连接诊断信息:")
                print(f"   📡 检查Oracle服务器是否运行在 {host}:{port}")
                print(f"   🗄️  检查数据库名称 '{database_name}' 是否正确")
                print(f"   👤 检查用户名 '{username}' 和密码是否正确")
                print(f"   🔧 检查连接类型 '{oracle_connection_type}' 是否匹配数据库配置")
                
                # 显示当前Oracle客户端状态
                if oracle_thick_mode_available:
                    print(f"   ✅ Oracle客户端状态: Thick模式已启用")
                else:
                    print(f"   ⚠️  Oracle客户端状态: Thin模式（功能受限）")
                
                if "DPY-3010" in str(e):
                    print("   ❌ DPY-3010错误: thin模式不支持此Oracle版本")
                    print("   💡 解决方案:")
                    print("      1. 安装Oracle Instant Client")
                    print("      2. 设置环境变量 ORACLE_HOME")
                    print("      3. 重启应用程序")
                    print("   🔍 当前环境变量状态:")
                    oracle_home = os.environ.get('ORACLE_HOME')
                    ld_library_path = os.environ.get('LD_LIBRARY_PATH')
                    print(f"      ORACLE_HOME: {oracle_home or '❌ 未设置'}")
                    print(f"      LD_LIBRARY_PATH: {ld_library_path or '❌ 未设置'}")
                    
                if "DPY-6005" in str(e):
                    print("   ❌ DPY-6005错误: 无法连接到数据库")
                    print("   💡 可能原因:")
                    print("      • 网络连接问题")
                    print("      • Oracle服务器未运行")
                    print("      • 端口被防火墙阻塞")
                    print("      • 连接参数错误")
            
            return ConnectionTestResponse(success=False, message=error_msg)
    
    @staticmethod
    def get_connection_string(db_type: str, host: str, port: int, 
                            database_name: str, username: str, password: str,
                            oracle_connection_type: str = "service_name") -> str:
        """获取数据库连接字符串"""
        # 对用户名和密码进行URL编码，处理特殊字符
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        
        if db_type.lower() == 'oracle':
            # 使用 oracle+oracledb 驱动（新版）
            if oracle_connection_type == "sid":
                return f"oracle+oracledb://{encoded_username}:{encoded_password}@{host}:{port}/{database_name}"
            else:
                return f"oracle+oracledb://{encoded_username}:{encoded_password}@{host}:{port}/?service_name={database_name}"
        elif db_type.lower() in ['mysql', 'doris']:
            return f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/{database_name}?charset=utf8mb4"
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    @staticmethod
    def get_schemas(db_type: str, host: str, port: int, 
                   database_name: str, username: str, password: str,
                   oracle_connection_type: str = "service_name") -> List[dict]:
        """获取数据库模式列表"""
        try:
            if db_type.lower() not in ['oracle', 'mysql', 'doris']:
                raise ValueError("该数据库类型不支持模式查询")
            
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(
                conn_str,
                pool_size=10,
        max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # 根据数据库类型选择不同的查询语句
            if db_type.lower() == 'oracle':
                # Oracle查询所有可访问的模式
                query = """
                SELECT USERNAME 
                FROM ALL_USERS 
                ORDER BY USERNAME
                """
            elif db_type.lower() in ['mysql', 'doris']:
                # MySQL/Doris查询所有数据库（schema）
                query = """
                SELECT SCHEMA_NAME as USERNAME
                FROM INFORMATION_SCHEMA.SCHEMATA 
                WHERE SCHEMA_NAME NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
                ORDER BY SCHEMA_NAME
                """
            
            with engine.connect() as conn:
                result = conn.execute(text(query))
                schemas = []
                for row in result:
                    schemas.append({
                        'username': row[0]
                    })
                return schemas
                
        except Exception as e:
            print(f"❌ 获取模式列表失败: {e}")
            return []
    
    @staticmethod
    def get_tables_by_schema(db_type: str, host: str, port: int, 
                            database_name: str, username: str, password: str,
                            schema: str, oracle_connection_type: str = "service_name") -> List[dict]:
        """根据模式获取数据库表列表"""
        try:
            if db_type.lower() not in ['oracle', 'mysql', 'doris']:
                raise ValueError("该数据库类型不支持按模式查询表")
            
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(
                conn_str,
                pool_size=10,
            max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # 根据数据库类型选择不同的查询语句
            if db_type.lower() == 'oracle':
                # Oracle根据模式查询表和视图
                query = f"""
                SELECT 
                    t.TABLE_NAME AS NAME, 
                    'TABLE' AS TYPE, 
                    c.COMMENTS AS COMMENTS 
                FROM ALL_TABLES t 
                LEFT JOIN ALL_TAB_COMMENTS c 
                  ON t.OWNER = c.OWNER 
                 AND t.TABLE_NAME = c.TABLE_NAME 
                WHERE t.OWNER = '{schema}'
                
                UNION
                
                SELECT 
                    v.VIEW_NAME AS NAME, 
                    'VIEW' AS TYPE, 
                    c.COMMENTS AS COMMENTS 
                FROM ALL_VIEWS v 
                LEFT JOIN ALL_TAB_COMMENTS c 
                  ON v.OWNER = c.OWNER 
                 AND v.VIEW_NAME = c.TABLE_NAME 
                WHERE v.OWNER = '{schema}'
                ORDER BY NAME
                """
            elif db_type.lower() in ['mysql', 'doris']:
                # MySQL/Doris根据数据库名查询表和视图
                query = f"""
                SELECT TABLE_NAME AS NAME, 
                       CASE WHEN TABLE_TYPE = 'BASE TABLE' THEN 'TABLE' ELSE 'VIEW' END AS TYPE,
                       TABLE_COMMENT AS COMMENTS
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = '{schema}'
                ORDER BY TABLE_NAME
                """
            
            with engine.connect() as conn:
                 result = conn.execute(text(query))
                 tables = []
                 for row in result:
                     tables.append({
                         'table_name': row[0],
                         'table_type': row[1],
                         'table_comment': row[2] if len(row) > 2 else None
                     })
                 return tables
                
        except Exception as e:
            print(f"❌ 根据模式获取表列表失败: {e}")
            return []
    
    @staticmethod
    def get_tables(db_type: str, host: str, port: int, 
                   database_name: str, username: str, password: str,
                   oracle_connection_type: str = "service_name") -> List[dict]:
        """获取数据库中的表和视图列表"""
        try:
            # ✅ 构建连接字符串
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(
                conn_str,
                pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
            )
    
            # ✅ 构建查询语句
            if db_type.lower() == 'oracle':
                query = """
                    SELECT table_name, 'TABLE' as table_type, comments as table_comment
                    FROM user_tab_comments 
                    WHERE table_type = 'TABLE'
                    UNION ALL
                    SELECT view_name as table_name, 'VIEW' as table_type, '' as table_comment
                    FROM user_views
                    ORDER BY table_name
                """
                print(f"🔍 执行Oracle表查询: 用户: {username.upper()}")
            elif db_type.lower() in ['mysql', 'doris']:
                query = """
                    SELECT table_name, table_type, table_comment
                    FROM information_schema.tables 
                    WHERE table_schema = :database_name
                    ORDER BY table_name
                """
    
            # ✅ 执行查询
            with engine.connect() as conn:
                print(f"🔗 已建立数据库连接")
                if db_type.lower() == 'oracle':
                    print(f"🚀 执行查询...")
                    result = conn.execute(text(query))
                else:
                    result = conn.execute(text(query), {"database_name": database_name})
                print(f"✅ 查询成功执行")
                tables = []
                for row in result:
                    tables.append(TableInfo(
                        table_name=row[0],
                        table_type=row[1],
                        table_comment=row[2] if len(row) > 2 else None
                    ))
                return tables
    
        except Exception as e:
            print(f"❌ 获取表失败: {e}")
            return []
    
    @staticmethod
    def get_table_detail(db_type: str, host: str, port: int, 
                        database_name: str, username: str, password: str, 
                        table_name: str, oracle_connection_type: str = "service_name", 
                        schema: str = None) -> TableDetailResponse:
        """获取表的详细信息"""
        try:
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(
            conn_str,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
            
            # 获取列信息
            if db_type.lower() == 'oracle':
                # 根据是否提供schema参数选择不同的查询方式
                if schema:
                    # 查询指定schema的表信息
                    columns_query = """
                        SELECT 
                            c.column_name,
                            c.data_type || 
                            CASE 
                                WHEN c.data_type IN ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR') 
                                THEN '(' || c.data_length || ')'
                                WHEN c.data_type = 'NUMBER' AND c.data_precision IS NOT NULL
                                THEN '(' || c.data_precision || 
                                     CASE WHEN c.data_scale > 0 THEN ',' || c.data_scale ELSE '' END || ')'
                                ELSE ''
                            END as data_type,
                            CASE WHEN c.nullable = 'Y' THEN 1 ELSE 0 END as is_nullable,
                            c.data_default as column_default,
                            cc.comments as column_comment,
                            CASE WHEN pk.column_name IS NOT NULL THEN 1 ELSE 0 END as is_primary_key
                        FROM all_tab_columns c
                        LEFT JOIN all_col_comments cc ON c.owner = cc.owner AND c.table_name = cc.table_name AND c.column_name = cc.column_name
                        LEFT JOIN (
                            SELECT col.column_name, col.table_name, col.owner
                            FROM all_constraints con, all_cons_columns col
                            WHERE con.constraint_name = col.constraint_name
                            AND con.owner = col.owner
                            AND con.constraint_type = 'P'
                            AND col.table_name = :table_name
                            AND col.owner = :schema
                        ) pk ON c.column_name = pk.column_name AND c.table_name = pk.table_name AND c.owner = pk.owner
                        WHERE c.table_name = :table_name AND c.owner = :schema
                        ORDER BY c.column_id
                    """
                else:
                    # 查询当前用户的表信息
                    columns_query = """
                        SELECT 
                            c.column_name,
                            c.data_type || 
                            CASE 
                                WHEN c.data_type IN ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR') 
                                THEN '(' || c.data_length || ')'
                                WHEN c.data_type = 'NUMBER' AND c.data_precision IS NOT NULL
                                THEN '(' || c.data_precision || 
                                     CASE WHEN c.data_scale > 0 THEN ',' || c.data_scale ELSE '' END || ')'
                                ELSE ''
                            END as data_type,
                            CASE WHEN c.nullable = 'Y' THEN 1 ELSE 0 END as is_nullable,
                            c.data_default as column_default,
                            cc.comments as column_comment,
                            CASE WHEN pk.column_name IS NOT NULL THEN 1 ELSE 0 END as is_primary_key
                        FROM user_tab_columns c
                        LEFT JOIN user_col_comments cc ON c.table_name = cc.table_name AND c.column_name = cc.column_name
                        LEFT JOIN (
                            SELECT col.column_name, col.table_name
                            FROM user_constraints con, user_cons_columns col
                            WHERE con.constraint_name = col.constraint_name
                            AND con.constraint_type = 'P'
                            AND col.table_name = :table_name
                        ) pk ON c.column_name = pk.column_name AND c.table_name = pk.table_name
                        WHERE c.table_name = :table_name
                        ORDER BY c.column_id
                    """
                
                # 获取行数
                if schema:
                    count_query = f"SELECT COUNT(*) FROM {schema}.{table_name}"
                else:
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                
            elif db_type.lower() in ['mysql', 'doris']:
                columns_query = """
                    SELECT 
                        column_name,
                        column_type as data_type,
                        CASE WHEN is_nullable = 'YES' THEN 1 ELSE 0 END as is_nullable,
                        column_default,
                        column_comment,
                        CASE WHEN column_key = 'PRI' THEN 1 ELSE 0 END as is_primary_key
                    FROM information_schema.columns 
                    WHERE table_schema = :database_name AND table_name = :table_name
                    ORDER BY ordinal_position
                """
                
                count_query = f"SELECT COUNT(*) FROM `{database_name}`.`{table_name}`"
            
            with engine.connect() as conn:
                # 获取列信息
                if db_type.lower() == 'oracle':
                    if schema:
                        columns_result = conn.execute(text(columns_query), {"table_name": table_name.upper(), "schema": schema.upper()})
                    else:
                        columns_result = conn.execute(text(columns_query), {"table_name": table_name.upper()})
                else:
                    columns_result = conn.execute(text(columns_query), {
                        "database_name": database_name, 
                        "table_name": table_name
                    })
                
                columns = []
                for row in columns_result:
                    columns.append(ColumnInfo(
                        column_name=row[0],
                        data_type=row[1],
                        is_nullable=bool(row[2]),
                        column_default=row[3],
                        column_comment=row[4],
                        is_primary_key=bool(row[5])
                    ))
                
                # 获取行数
                try:
                    count_result = conn.execute(text(count_query))
                    row_count = count_result.scalar()
                except:
                    row_count = None
                
                return TableDetailResponse(
                    table_name=table_name,
                    table_type="TABLE",  # 简化处理
                    columns=columns,
                    row_count=row_count
                )
        except Exception as e:
            raise Exception(f"获取表详情失败: {str(e)}")
    
    @staticmethod
    def execute_sql(db_type: str, host: str, port: int, 
                   database_name: str, username: str, password: str, 
                   sql: str, limit: int = 1000, oracle_connection_type: str = "service_name", 
                   schema: str = None) -> SQLExecuteResponse:
        """执行SQL查询"""
        try:
            start_time = time.time()
            
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(
                conn_str,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            with engine.connect() as conn:
                # 添加LIMIT限制（如果SQL中没有）
                sql_clean = sql.strip()
                # 移除末尾的分号
                if sql_clean.endswith(';'):
                    sql_clean = sql_clean[:-1]
                
                sql_lower = sql_clean.lower()
                if sql_lower.startswith('select'):
                    if db_type.lower() == 'oracle':
                        # Oracle数据库：检查是否已经有ROWNUM限制
                        if 'rownum' not in sql_lower:
                            sql = f"SELECT * FROM ({sql_clean}) WHERE ROWNUM <= {limit}"
                        else:
                            sql = sql_clean
                    else:
                        # 其他数据库：检查是否已经有LIMIT限制
                        if 'limit' not in sql_lower:
                            sql = f"{sql_clean} LIMIT {limit}"
                        else:
                            sql = sql_clean
                else:
                    sql = sql_clean
                
                result = conn.execute(text(sql))
                
                # 获取列名
                columns = list(result.keys()) if result.keys() else []
                
                # 获取数据
                data = []
                row_count = 0
                for row in result:
                    # 使用row._mapping来正确转换SQLAlchemy Row对象
                    data.append(dict(row._mapping))
                    row_count += 1
                
                execution_time = time.time() - start_time
                
                return SQLExecuteResponse(
                    success=True,
                    columns=columns,
                    data=data,
                    row_count=row_count,
                    execution_time=execution_time
                )
        except Exception as e:
            execution_time = time.time() - start_time
            return SQLExecuteResponse(
                    success=False,
                    execution_time=execution_time,
                    error_message=str(e)
                )
    
    @staticmethod
    def check_column_has_data(db_type: str, host: str, port: int, 
                             database_name: str, username: str, password: str,
                             table_name: str, column_name: str,
                             oracle_connection_type: str = "service_name", 
                             schema: str = None) -> bool:
        """检查指定列是否有非空数据"""
        try:
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(
                conn_str,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            with engine.connect() as conn:
                # 构建表引用和查询SQL
                if db_type.lower() == 'oracle':
                    table_ref = f"{schema}.{table_name}" if schema else table_name
                    check_sql = f"SELECT COUNT(*) FROM {table_ref} WHERE {column_name} IS NOT NULL AND ROWNUM <= 1"
                else:
                    table_ref = f"`{table_name}`"
                    if schema:
                        table_ref = f"`{schema}`.{table_ref}"
                    check_sql = f"SELECT COUNT(*) FROM {table_ref} WHERE `{column_name}` IS NOT NULL LIMIT 1"
                
                result = conn.execute(text(check_sql))
                count = result.scalar()
                return count > 0
                
        except Exception as e:
            # 如果检查失败，默认认为有数据（保守策略）
            print(f"检查列数据失败: {str(e)}")
            return True
    
    @staticmethod
    def modify_table_structure(db_type: str, host: str, port: int, 
                              database_name: str, username: str, password: str,
                              table_name: str, operation_type: str, column_data: dict,
                              oracle_connection_type: str = "service_name", 
                              schema: str = None) -> SQLExecuteResponse:
        """修改表结构"""
        try:
            start_time = time.time()
            
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(
                conn_str,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            with engine.connect() as conn:
                # 构建表引用
                if db_type.lower() == 'oracle':
                    table_ref = f"{schema}.{table_name}" if schema else table_name
                else:
                    table_ref = f"`{table_name}`"
                
                # 根据操作类型构建SQL
                if operation_type == "add_column":
                    if db_type.lower() == 'oracle':
                        sql = f"ALTER TABLE {table_ref} ADD {column_data['name']} {column_data['type']}"
                        if not column_data.get('nullable', True):
                            sql += " NOT NULL"
                        if column_data.get('default'):
                            default_value = DatabaseService._format_default_value(column_data['default'], column_data['type'])
                            sql += f" DEFAULT {default_value}"
                    else:
                        sql = f"ALTER TABLE {table_ref} ADD COLUMN `{column_data['name']}` {column_data['type']}"
                        if not column_data.get('nullable', True):
                            sql += " NOT NULL"
                        if column_data.get('default'):
                            default_value = DatabaseService._format_default_value(column_data['default'], column_data['type'])
                            sql += f" DEFAULT {default_value}"
                        if column_data.get('comment'):
                            sql += f" COMMENT '{column_data['comment']}'"
                
                elif operation_type == "drop_column":
                    # 检查列是否有数据
                    column_name = column_data['name']
                    has_data = DatabaseService.check_column_has_data(
                        db_type, host, port, database_name, username, password,
                        table_name, column_name, oracle_connection_type, schema
                    )
                    
                    if has_data:
                        return SQLExecuteResponse(
                            success=False,
                            error_message="列中包含数据，禁止删除",
                            data=None,
                            affected_rows=0
                        )
                    
                    if db_type.lower() == 'oracle':
                        sql = f"ALTER TABLE {table_ref} DROP COLUMN {column_data['name']}"
                    else:
                        sql = f"ALTER TABLE {table_ref} DROP COLUMN `{column_data['name']}`"
                
                elif operation_type == "drop_column_force":
                    # 强制删除列，不检查数据
                    if db_type.lower() == 'oracle':
                        sql = f"ALTER TABLE {table_ref} DROP COLUMN {column_data['name']}"
                    else:
                        sql = f"ALTER TABLE {table_ref} DROP COLUMN `{column_data['name']}`"
                
                elif operation_type == "modify_column":
                    # 获取原始列名和新列名
                    original_name = column_data.get('original_name', column_data['name'])
                    new_name = column_data['name']
                    
                    # 先获取当前列信息，检查是否真的需要修改
                    if db_type.lower() == 'doris':
                        # 获取当前列信息
                        check_sql = f"DESCRIBE {table_ref}"
                        result = conn.execute(text(check_sql))
                        current_columns = {row[0]: row for row in result.fetchall()}
                        
                        if original_name not in current_columns:
                            raise ValueError(f"列 '{original_name}' 不存在")
                        
                        current_column = current_columns[original_name]
                        current_type = current_column[1].upper()
                        current_nullable = current_column[2] == 'YES'
                        current_default = current_column[4] if current_column[4] != 'NULL' else None
                        current_comment = current_column[5] if len(current_column) > 5 else None
                        
                        # 检查是否需要修改
                        needs_change = False
                        changes = []
                        
                        # 检查列名
                        if original_name != new_name:
                            needs_change = True
                            changes.append("列名")
                        
                        # 检查数据类型
                        new_type = column_data['type'].upper()
                        # Doris数据库特殊处理：标准化int类型进行比较
                        normalized_current_type = current_type
                        normalized_new_type = new_type
                        
                        if normalized_current_type.startswith('INT('):
                            normalized_current_type = 'INT'
                        elif normalized_current_type.startswith('BIGINT('):
                            normalized_current_type = 'BIGINT'
                        elif normalized_current_type.startswith('SMALLINT('):
                            normalized_current_type = 'SMALLINT'
                        elif normalized_current_type.startswith('TINYINT('):
                            normalized_current_type = 'TINYINT'
                        
                        if normalized_new_type.startswith('INT('):
                            normalized_new_type = 'INT'
                        elif normalized_new_type.startswith('BIGINT('):
                            normalized_new_type = 'BIGINT'
                        elif normalized_new_type.startswith('SMALLINT('):
                            normalized_new_type = 'SMALLINT'
                        elif normalized_new_type.startswith('TINYINT('):
                            normalized_new_type = 'TINYINT'
                        
                        if normalized_current_type != normalized_new_type:
                            needs_change = True
                            changes.append("数据类型")
                        
                        # 检查可空性
                        new_nullable = column_data.get('nullable', True)
                        if current_nullable != new_nullable:
                            needs_change = True
                            changes.append("可空性")
                        
                        # 检查默认值
                        new_default = column_data.get('default')
                        if str(current_default) != str(new_default):
                            needs_change = True
                            changes.append("默认值")
                        
                        # 检查注释
                        new_comment = column_data.get('comment')
                        if current_comment != new_comment:
                            needs_change = True
                            changes.append("注释")
                        
                        if not needs_change:
                            execution_time = time.time() - start_time
                            return SQLExecuteResponse(
                                success=True,
                                columns=[],
                                data=[],
                                row_count=0,
                                affected_rows=0,
                                execution_time=execution_time,
                                generated_sql=None,
                                message=f"列 '{original_name}' 无需修改，所有属性都相同"
                            )
                        
                        # Doris数据库的列修改
                        if original_name != new_name:
                            # Doris不支持CHANGE语法，需要分两步：先重命名，再修改属性
                            # 第一步：重命名列
                            sql = f"ALTER TABLE {table_ref} RENAME COLUMN `{original_name}` `{new_name}`"
                            conn.execute(text(sql))
                            
                            # 检查除了列名外是否还有其他属性需要修改
                            other_changes = [change for change in changes if change != "列名"]
                            if other_changes:
                                # 第二步：修改列属性
                                # 检查是否真的需要修改类型
                                type_changed = "数据类型" in other_changes
                                
                                # 构建SQL - 只有在类型真正改变时才包含类型信息
                                if type_changed:
                                    # Doris数据库特殊处理：去掉int类型的长度规范
                                    column_type = column_data['type']
                                    if column_type.lower().startswith('int('):
                                        column_type = 'int'
                                    elif column_type.lower().startswith('bigint('):
                                        column_type = 'bigint'
                                    elif column_type.lower().startswith('smallint('):
                                        column_type = 'smallint'
                                    elif column_type.lower().startswith('tinyint('):
                                        column_type = 'tinyint'
                                    
                                    sql = f"ALTER TABLE {table_ref} MODIFY COLUMN `{new_name}` {column_type}"
                                else:
                                    # 如果类型没有改变，只修改其他属性
                                    sql = f"ALTER TABLE {table_ref} MODIFY COLUMN `{new_name}`"
                                
                                if not column_data.get('nullable', True):
                                    sql += " NOT NULL"
                                if column_data.get('default'):
                                    default_value = DatabaseService._format_default_value(column_data['default'], column_data['type'])
                                    sql += f" DEFAULT {default_value}"
                                if column_data.get('comment'):
                                    sql += f" COMMENT '{column_data['comment']}'"
                                # 执行第二步修改
                                conn.execute(text(sql))
                            
                            # 重命名操作完成，提交事务并返回
                            conn.commit()
                            execution_time = time.time() - start_time
                            return SQLExecuteResponse(
                                success=True,
                                columns=[],
                                data=[],
                                row_count=0,
                                affected_rows=1,
                                execution_time=execution_time,
                                generated_sql=f"ALTER TABLE {table_ref} RENAME COLUMN `{original_name}` `{new_name}`",
                                message=f"成功将列 '{original_name}' 重命名为 '{new_name}'{' 并修改属性' if other_changes else ''}"
                            )
                        else:
                            # 只修改列属性
                            # 检查是否真的需要修改类型
                            type_changed = "数据类型" in changes
                            
                            # 构建SQL - 只有在类型真正改变时才包含类型信息
                            if type_changed:
                                # Doris数据库特殊处理：去掉int类型的长度规范
                                column_type = column_data['type']
                                if column_type.lower().startswith('int('):
                                    column_type = 'int'
                                elif column_type.lower().startswith('bigint('):
                                    column_type = 'bigint'
                                elif column_type.lower().startswith('smallint('):
                                    column_type = 'smallint'
                                elif column_type.lower().startswith('tinyint('):
                                    column_type = 'tinyint'
                                
                                sql = f"ALTER TABLE {table_ref} MODIFY COLUMN `{original_name}` {column_type}"
                            else:
                                # 如果类型没有改变，只修改其他属性
                                sql = f"ALTER TABLE {table_ref} MODIFY COLUMN `{original_name}`"
                            
                            if not column_data.get('nullable', True):
                                sql += " NOT NULL"
                            if column_data.get('default'):
                                default_value = DatabaseService._format_default_value(column_data['default'], column_data['type'])
                                sql += f" DEFAULT {default_value}"
                            if column_data.get('comment'):
                                sql += f" COMMENT '{column_data['comment']}'"
                            
                            # 执行SQL
                            conn.execute(text(sql))
                            conn.commit()
                            execution_time = time.time() - start_time
                            return SQLExecuteResponse(
                                success=True,
                                columns=[],
                                data=[],
                                row_count=0,
                                affected_rows=1,
                                execution_time=execution_time,
                                generated_sql=sql,
                                message=f"成功修改列 '{original_name}' 的属性"
                            )
                    
                    elif db_type.lower() == 'oracle':
                        # Oracle数据库的列修改
                        if original_name != new_name:
                            # 如果列名发生变化，需要先重命名列
                            sql = f"ALTER TABLE {table_ref} RENAME COLUMN {original_name} TO {new_name}"
                            conn.execute(text(sql))
                            # 然后修改列的其他属性
                            sql = f"ALTER TABLE {table_ref} MODIFY {new_name} {column_data['type']}"
                        else:
                            # 只修改列属性
                            sql = f"ALTER TABLE {table_ref} MODIFY {original_name} {column_data['type']}"
                        
                        if not column_data.get('nullable', True):
                            sql += " NOT NULL"
                    else:
                        # MySQL等其他数据库的列修改
                        if original_name != new_name:
                            # 如果列名发生变化，使用CHANGE语法
                            sql = f"ALTER TABLE {table_ref} CHANGE COLUMN `{original_name}` `{new_name}` {column_data['type']}"
                        else:
                            # 只修改列属性，使用MODIFY语法
                            sql = f"ALTER TABLE {table_ref} MODIFY COLUMN `{original_name}` {column_data['type']}"
                        
                        if not column_data.get('nullable', True):
                            sql += " NOT NULL"
                        if column_data.get('default'):
                            default_value = DatabaseService._format_default_value(column_data['default'], column_data['type'])
                            sql += f" DEFAULT {default_value}"
                        if column_data.get('comment'):
                            sql += f" COMMENT '{column_data['comment']}'"
                
                else:
                    raise ValueError(f"不支持的操作类型: {operation_type}")
                
                # 执行SQL
                conn.execute(text(sql))
                conn.commit()
                
                execution_time = time.time() - start_time
                
                return SQLExecuteResponse(
                    success=True,
                    columns=[],
                    data=[],
                    row_count=0,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return SQLExecuteResponse(
                success=False,
                execution_time=execution_time,
                error_message=f"修改表结构失败: {str(e)}"
            )
    
    @staticmethod
    def create_table(db_type: str, host: str, port: int, 
                    database_name: str, username: str, password: str,
                    table_name: str, columns: List[dict],
                    oracle_connection_type: str = "service_name", 
                    schema: str = None) -> SQLExecuteResponse:
        """创建表"""
        try:
            start_time = time.time()
            
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(
                conn_str,
                pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
            )
            
            with engine.connect() as conn:
                # 构建表引用
                if db_type.lower() == 'oracle':
                    table_ref = f"{schema}.{table_name}" if schema else table_name
                else:
                    table_ref = f"`{table_name}`"
                
                # 构建列定义
                column_definitions = []
                primary_keys = []
                
                for col in columns:
                    col_name = col.get('column_name') or col.get('name')
                    col_type = col.get('data_type') or col.get('type')
                    col_nullable = col.get('is_nullable', col.get('nullable', True))
                    col_default = col.get('column_default') or col.get('default')
                    col_comment = col.get('column_comment') or col.get('comment')
                    
                    col_def = f"`{col_name}` {col_type}" if db_type.lower() != 'oracle' else f"{col_name} {col_type}"
                    
                    if not col_nullable:
                        col_def += " NOT NULL"
                    
                    if col_default:
                        default_value = DatabaseService._format_default_value(col_default, col_type)
                        col_def += f" DEFAULT {default_value}"
                    
                    if db_type.lower() != 'oracle' and col_comment:
                        col_def += f" COMMENT '{col_comment}'"
                    
                    column_definitions.append(col_def)
                    
                    if col.get('is_primary_key'):
                        primary_keys.append(col_name)
                
                # 添加主键约束
                if primary_keys:
                    if db_type.lower() == 'oracle':
                        pk_def = f"PRIMARY KEY ({', '.join(primary_keys)})"
                    else:
                        pk_def = f"PRIMARY KEY (`{'`, `'.join(primary_keys)}`)"
                    column_definitions.append(pk_def)
                
                # 构建CREATE TABLE语句
                sql = f"CREATE TABLE {table_ref} (\n  {',\n  '.join(column_definitions)}\n)"
                
                # 为支持分布式数据库（如DorisDB/StarRocks）添加副本数量设置
                if db_type.lower() in ['mysql', 'doris', 'starrocks']:
                    # 检查是否是分布式数据库，添加单副本配置
                    sql += " PROPERTIES (\"replication_num\" = \"1\")"
                
                # 执行SQL
                conn.execute(text(sql))
                conn.commit()
                
                execution_time = time.time() - start_time
                
                return SQLExecuteResponse(
                    success=True,
                    columns=[],
                    data=[],
                    row_count=0,
                    execution_time=execution_time,
                    message=f"表 {table_name} 创建成功"
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return SQLExecuteResponse(
                success=False,
                execution_time=execution_time,
                error_message=f"创建表失败: {str(e)}"
            )
    
    @staticmethod
    def execute_ddl(db_type: str, host: str, port: int, 
                   database_name: str, username: str, password: str,
                   ddl_sql: str, oracle_connection_type: str = "service_name") -> SQLExecuteResponse:
        """执行DDL语句"""
        try:
            start_time = time.time()
            
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(
                conn_str,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            with engine.connect() as conn:
                # 清理SQL语句
                sql_clean = ddl_sql.strip()
                if sql_clean.endswith(';'):
                    sql_clean = sql_clean[:-1]
                
                # 执行DDL
                conn.execute(text(sql_clean))
                conn.commit()
                
                execution_time = time.time() - start_time
                
                return SQLExecuteResponse(
                    success=True,
                    columns=[],
                    data=[],
                    row_count=0,
                    execution_time=execution_time,
                    message="DDL语句执行成功"
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return SQLExecuteResponse(
                success=False,
                execution_time=execution_time,
                error_message=f"DDL执行失败: {str(e)}"
            )
    
    @staticmethod
    def get_table_data(db_type: str, host: str, port: int, 
                      database_name: str, username: str, password: str, 
                      table_name: str, limit: int = 100, offset: int = 0, 
                      oracle_connection_type: str = "service_name", 
                      schema: str = None) -> SQLExecuteResponse:
        """获取表数据"""
        try:
            start_time = time.time()
            
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(
                conn_str,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            with engine.connect() as conn:
                # 构建数据查询SQL
                if db_type.lower() == 'oracle':
                    # 对于Oracle，如果提供了schema，则使用schema.table_name格式
                    table_ref = f"{schema}.{table_name}" if schema else table_name
                    data_sql = f"""
                        SELECT * FROM (
                            SELECT a.*, ROWNUM rnum FROM (
                                SELECT * FROM {table_ref}
                            ) a WHERE ROWNUM <= {offset + limit}
                        ) WHERE rnum > {offset}
                    """
                else:
                    data_sql = f"SELECT * FROM `{table_name}` LIMIT {limit} OFFSET {offset}"
                
                # 执行数据查询
                result = conn.execute(text(data_sql))
                
                # 获取列名
                columns = list(result.keys()) if result.keys() else []
                
                # 获取数据
                data = []
                row_count = 0
                for row in result:
                    data.append(dict(row._mapping))
                    row_count += 1
                
                # 如果是第一次请求(offset=0)，获取总行数
                total_count = None
                if offset == 0:
                    try:
                        if db_type.lower() == 'oracle':
                            count_sql = f"SELECT COUNT(*) FROM {table_ref}"
                        else:
                            count_sql = f"SELECT COUNT(*) FROM `{table_name}`"
                        
                        count_result = conn.execute(text(count_sql))
                        total_count = count_result.scalar()
                    except Exception as count_error:
                        print(f"获取总行数失败: {count_error}")
                        total_count = None
                
                execution_time = time.time() - start_time
                
                return SQLExecuteResponse(
                    success=True,
                    columns=columns,
                    data=data,
                    row_count=row_count,
                    total_count=total_count,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return SQLExecuteResponse(
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )