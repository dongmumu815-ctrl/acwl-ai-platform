#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试导入，找出循环引用问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Auth schemas import...")
try:
    from app.schemas.auth import UserResponse
    print("✓ Auth schemas imported successfully")
except Exception as e:
    print(f"✗ Auth schemas failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Auth schemas import successful!")