import sys
import os
import logging
import json
import uuid

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.db_service import RouterDBService

logging.basicConfig(level=logging.INFO)

def check_db():
    db = RouterDBService()
    
    # 1. Check Table Schema
    print("\n=== Checking Table Schema ===")
    schema_sql = """
    SELECT column_name, data_type, is_nullable, column_key
    FROM information_schema.columns 
    WHERE table_schema = 'cvs2db' 
    AND table_name = 'import_templates'
    """
    try:
        schema_result = db.execute_sql('task_db', schema_sql)
        print("Schema Result:", json.dumps(schema_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Schema Check Failed: {e}")

    # 2. Check Existing Data
    print("\n=== Checking Existing Data (Limit 5) ===")
    select_sql = "SELECT id, name, created_at FROM cvs2db.import_templates ORDER BY created_at DESC LIMIT 5"
    try:
        data_result = db.execute_sql('task_db', select_sql)
        print("Data Result:", json.dumps(data_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Data Check Failed: {e}")

if __name__ == "__main__":
    check_db()
