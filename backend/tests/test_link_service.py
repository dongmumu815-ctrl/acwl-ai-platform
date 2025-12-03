
import sys
import os
import logging

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取 backend 目录 (tests 的上一级)
backend_dir = os.path.dirname(current_dir)

# 将 backend 目录添加到 sys.path
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print(f"Added {backend_dir} to sys.path")
print(f"sys.path: {sys.path}")

try:
    from app.services.db_service import LinkTaskService
except ImportError as e:
    print(f"ImportError: {e}")
    # 尝试列出 app 目录下的内容
    app_dir = os.path.join(backend_dir, 'app')
    if os.path.exists(app_dir):
        print(f"app directory contents: {os.listdir(app_dir)}")
    else:
        print("app directory not found")
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG)

def test_service():
    print("Testing LinkTaskService...")
    try:
        service = LinkTaskService()
        print("Connecting...")
        service._connect()
        print("Connected. Fetching data...")
        result = service.get_link_menu_types()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service()
