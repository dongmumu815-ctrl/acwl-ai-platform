import sys
import os
import logging
import json

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)

from app.services.db_service import RouterDBService

def get_schema():
    print("Connecting to RouterDBService...")
    try:
        db = RouterDBService()
    except Exception as e:
        print(f"Failed to connect to RouterDBService: {e}")
        return

    # Try to query cvs2db.import_templates columns
    print("\nGetting columns for cvs2db.import_templates...")
    col_sql = """
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_schema = 'cvs2db' 
    AND table_name = 'import_templates'
    """
    try:
        col_result = db.execute_sql('task_db', col_sql)
        if col_result.get('success'):
            cols = col_result.get('data', [])
            print("Columns for cvs2db.import_templates:")
            print(json.dumps(cols, indent=2, default=str))
        else:
            print(f"Failed to get columns: {col_result.get('error')}")
            
    except Exception as e:
        print(f"Error: {e}")

    # Try aliases cvs_db and cvs2db
    for alias in ['cvs_db', 'cvs2db', 'csv2db']:
        print(f"\nTrying database alias: '{alias}'...")
        try:
            result = db.execute_sql(alias, "SELECT 1")
            if result.get('success'):
                print(f"!!! Alias '{alias}' WORKS !!!")
            else:
                print(f"Failed on '{alias}': {result.get('error')}")
        except Exception as e:
            print(f"Error on '{alias}': {e}")

if __name__ == "__main__":
    get_schema()
