import pymysql
import sys
from pypinyin import lazy_pinyin, Style

# 数据库配置
DB_HOST = "10.20.1.200"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "2wsx1QAZaczt"
DB_NAME = "acwl-ai-data"

def get_hostname(name):
    # 将中文转换为拼音
    pinyin_list = lazy_pinyin(name, style=Style.NORMAL)
    hostname = "-".join(pinyin_list)
    # 去除非法字符，只保留字母、数字、连字符
    hostname = "".join(c if c.isalnum() or c == "-" else "-" for c in hostname)
    # 移除多余的连字符
    while "--" in hostname:
        hostname = hostname.replace("--", "-")
    return hostname.strip("-").lower()

def generate_hosts():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection.cursor() as cursor:
            # 查询服务器信息
            sql = "SELECT ip_address, name FROM acwl_servers"
            cursor.execute(sql)
            result = cursor.fetchall()
            
            print("# ACWL AI Servers Hosts")
            print("# IP Address\tHostname\t# Original Name")
            
            seen_hostnames = {}
            
            for server in result:
                ip = server['ip_address']
                name = server['name']
                hostname = get_hostname(name)
                
                # 处理重名
                if hostname in seen_hostnames:
                    seen_hostnames[hostname] += 1
                    hostname = f"{hostname}-{seen_hostnames[hostname]}"
                else:
                    seen_hostnames[hostname] = 1
                
                print(f"{ip}\t{hostname}\t# {name}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    generate_hosts()
