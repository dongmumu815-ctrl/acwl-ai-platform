import sys
import os
import logging
import json

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.template_service import TemplateService

logging.basicConfig(level=logging.INFO)

def test_create_and_update():
    service = TemplateService()
    
    # Test Data 1: Using 'header_row' directly
    data_1 = {
        "name": "Template Test 1",
        "description": "Test direct field mapping",
        "excel_filename": "test1.xlsx",
        "header_row": 1,
        "data_start_row": 2,
        "file_type": "xlsx",
        "import_mode": "append",
        "executionConfig": {
            "batchSize": 100
        }
    }
    
    print("\n--- Creating Template 1 ---")
    result_1 = service.create_template(data_1)
    print("Result 1:", json.dumps(result_1, indent=2, ensure_ascii=False))
    
    # Test Data 2: Using 'header_row_index' alias
    data_2 = {
        "name": "Template Test 2",
        "description": "Test alias field mapping",
        "excel_filename": "test2.xlsx",
        "header_row_index": 5,
        "data_start_row_index": 6,
        "executionConfig": {
            "batchSize": 200
        }
    }
    
    print("\n--- Creating Template 2 ---")
    result_2 = service.create_template(data_2)
    print("Result 2:", json.dumps(result_2, indent=2, ensure_ascii=False))

    if result_1.get("success"):
        tid = result_1["data"]["id"]
        print(f"\n--- Updating Template 1 ({tid}) ---")
        update_data = {
            "header_row_index": 10, # Updating using alias
            "file_type": "csv"      # Updating direct field
        }
        update_res = service.update_template(tid, update_data)
        print("Update Result:", json.dumps(update_res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_create_and_update()
