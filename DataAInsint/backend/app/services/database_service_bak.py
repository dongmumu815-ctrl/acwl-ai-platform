import oracledb
import pymysql
from sqlalchemy import create_engine, text
from typing import List, Dict, Any, Tuple
import time
import os
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
        if db_type.lower() == 'oracle':
            # 根据连接类型构建连接字符串
            if oracle_connection_type == "sid":
                return f"oracle+oracledb://{username}:{password}@{host}:{port}:{database_name}"  # SID方式
            else:
                return f"oracle+oracledb://{username}:{password}@{host}:{port}/{database_name}"  # Service Name方式
        elif db_type.lower() == 'mysql':
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}?charset=utf8mb4"
        elif db_type.lower() == 'doris':
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}?charset=utf8mb4"
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    @staticmethod
    def get_tables(db_type: str, host: str, port: int, 
                  database_name: str, username: str, password: str,
                  oracle_connection_type: str = "service_name") -> List[TableInfo]:
        """获取数据库中的表和视图列表"""
        try:
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(conn_str)
            
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
            elif db_type.lower() in ['mysql', 'doris']:
                query = """
                    SELECT table_name, table_type, table_comment
                    FROM information_schema.tables 
                    WHERE table_schema = :database_name
                    ORDER BY table_name
                """
            
            with engine.connect() as conn:
                if db_type.lower() == 'oracle':
                    result = conn.execute(text(query))
                else:
                    result = conn.execute(text(query), {"database_name": database_name})
                
                tables = []
                for row in result:
                    tables.append(TableInfo(
                        table_name=row[0],
                        table_type=row[1],
                        table_comment=row[2] if len(row) > 2 else None
                    ))
                return tables
        except Exception as e:
            raise Exception(f"获取表列表失败: {str(e)}")
    
    @staticmethod
    def get_table_detail(db_type: str, host: str, port: int, 
                        database_name: str, username: str, password: str, 
                        table_name: str, oracle_connection_type: str = "service_name") -> TableDetailResponse:
        """获取表的详细信息"""
        try:
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(conn_str)
            
            # 获取列信息
            if db_type.lower() == 'oracle':
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
                   sql: str, limit: int = 1000, oracle_connection_type: str = "service_name") -> SQLExecuteResponse:
        """执行SQL查询"""
        try:
            start_time = time.time()
            
            conn_str = DatabaseService.get_connection_string(
                db_type, host, port, database_name, username, password, oracle_connection_type
            )
            engine = create_engine(conn_str)
            
            with engine.connect() as conn:
                # 添加LIMIT限制（如果SQL中没有）
                sql_lower = sql.lower().strip()
                if sql_lower.startswith('select') and 'limit' not in sql_lower:
                    if db_type.lower() == 'oracle':
                        sql = f"SELECT * FROM ({sql}) WHERE ROWNUM <= {limit}"
                    else:
                        sql = f"{sql} LIMIT {limit}"
                
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
    def get_table_data(db_type: str, host: str, port: int, 
                      database_name: str, username: str, password: str, 
                      table_name: str, limit: int = 100, offset: int = 0, 
                      oracle_connection_type: str = "service_name") -> SQLExecuteResponse:
        """获取表数据"""
        try:
            if db_type.lower() == 'oracle':
                sql = f"""
                    SELECT * FROM (
                        SELECT a.*, ROWNUM rnum FROM (
                            SELECT * FROM {table_name}
                        ) a WHERE ROWNUM <= {offset + limit}
                    ) WHERE rnum > {offset}
                """
            else:
                sql = f"SELECT * FROM `{table_name}` LIMIT {limit} OFFSET {offset}"
            
            return DatabaseService.execute_sql(
                db_type, host, port, database_name, username, password, sql, limit, oracle_connection_type
            )
        except Exception as e:
            return SQLExecuteResponse(
                success=False,
                error_message=str(e)
            )