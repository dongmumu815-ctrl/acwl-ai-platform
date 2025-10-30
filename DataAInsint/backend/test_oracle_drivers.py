#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oracle驱动兼容性测试脚本

此脚本用于测试Oracle驱动的安装状态和功能兼容性
支持python-oracledb和cx_Oracle的检测和比较

使用方法:
    python test_oracle_drivers.py
"""

import sys
import os
import platform
import logging
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OracleDriverTester:
    """Oracle驱动测试器"""
    
    def __init__(self):
        self.results = {
            'system_info': {},
            'python_oracledb': {},
            'cx_oracle': {},
            'recommendations': []
        }
        self._collect_system_info()
    
    def _collect_system_info(self):
        """收集系统信息"""
        self.results['system_info'] = {
            'platform': platform.platform(),
            'architecture': platform.machine(),
            'python_version': sys.version,
            'is_arm': 'arm' in platform.machine().lower() or 'aarch64' in platform.machine().lower(),
            'oracle_home': os.environ.get('ORACLE_HOME'),
            'tns_admin': os.environ.get('TNS_ADMIN'),
            'ld_library_path': os.environ.get('LD_LIBRARY_PATH'),
            'path': os.environ.get('PATH')
        }
    
    def test_python_oracledb(self) -> Dict[str, Any]:
        """测试python-oracledb驱动"""
        logger.info("🔍 测试 python-oracledb 驱动...")
        
        result = {
            'available': False,
            'version': None,
            'thin_mode': False,
            'thick_mode': False,
            'error': None
        }
        
        try:
            import oracledb
            result['available'] = True
            result['version'] = getattr(oracledb, '__version__', 'unknown')
            
            # 测试Thin模式
            try:
                result['thin_mode'] = True
                logger.info("✅ Thin模式可用")
            except Exception as e:
                logger.warning(f"⚠️  Thin模式测试失败: {e}")
            
            # 测试Thick模式
            try:
                # 尝试初始化thick模式
                oracledb.init_oracle_client()
                result['thick_mode'] = True
                logger.info("✅ Thick模式可用")
            except Exception as e:
                logger.warning(f"⚠️  Thick模式初始化失败: {e}")
                result['thick_mode'] = False
            
            logger.info(f"✅ python-oracledb v{result['version']} 可用")
            
        except ImportError as e:
            result['error'] = str(e)
            logger.warning("❌ python-oracledb 未安装")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ python-oracledb 测试失败: {e}")
        
        self.results['python_oracledb'] = result
        return result
    
    def test_cx_oracle(self) -> Dict[str, Any]:
        """测试cx_Oracle驱动"""
        logger.info("🔍 测试 cx_Oracle 驱动...")
        
        result = {
            'available': False,
            'version': None,
            'error': None
        }
        
        try:
            import cx_Oracle
            result['available'] = True
            result['version'] = getattr(cx_Oracle, '__version__', 'unknown')
            logger.info(f"✅ cx_Oracle v{result['version']} 可用")
            logger.warning("⚠️  cx_Oracle已停止维护，建议升级到python-oracledb")
            
        except ImportError as e:
            result['error'] = str(e)
            logger.info("ℹ️  cx_Oracle 未安装")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ cx_Oracle 测试失败: {e}")
        
        self.results['cx_oracle'] = result
        return result
    
    def generate_recommendations(self):
        """生成推荐建议"""
        recommendations = []
        
        python_oracledb = self.results['python_oracledb']
        cx_oracle = self.results['cx_oracle']
        system_info = self.results['system_info']
        
        # 基于驱动可用性的建议
        if python_oracledb.get('available'):
            if python_oracledb.get('thin_mode'):
                recommendations.append("✅ 推荐使用python-oracledb Thin模式进行生产部署")
            if python_oracledb.get('thick_mode'):
                recommendations.append("✅ 可以使用python-oracledb Thick模式获得最佳性能")
            else:
                recommendations.append("💡 考虑安装Oracle客户端库以启用Thick模式")
        else:
            recommendations.append("🚀 强烈建议安装python-oracledb: pip install oracledb")
        
        if cx_oracle.get('available'):
            recommendations.append("⚠️  建议从cx_Oracle迁移到python-oracledb")
            recommendations.append("📖 参考迁移指南: ORACLE_DRIVER_UPGRADE_GUIDE.md")
        
        # 基于系统架构的建议
        if system_info.get('is_arm'):
            recommendations.append("🏗️  ARM架构建议优先使用python-oracledb Thin模式")
        
        # 基于环境配置的建议
        if not system_info.get('oracle_home'):
            recommendations.append("🔧 未设置ORACLE_HOME，Thin模式是最佳选择")
        
        self.results['recommendations'] = recommendations
    
    def print_report(self):
        """打印测试报告"""
        print("\n" + "="*60)
        print("🔍 Oracle驱动兼容性测试报告")
        print("="*60)
        
        # 系统信息
        print("\n📋 系统信息:")
        system_info = self.results['system_info']
        print(f"   平台: {system_info['platform']}")
        print(f"   架构: {system_info['architecture']}")
        print(f"   Python: {system_info['python_version'].split()[0]}")
        print(f"   ORACLE_HOME: {system_info['oracle_home'] or '未设置'}")
        
        # python-oracledb状态
        print("\n🔧 python-oracledb 状态:")
        oracledb_info = self.results['python_oracledb']
        if oracledb_info.get('available'):
            print(f"   ✅ 已安装 v{oracledb_info['version']}")
            print(f"   Thin模式: {'✅ 可用' if oracledb_info['thin_mode'] else '❌ 不可用'}")
            print(f"   Thick模式: {'✅ 可用' if oracledb_info['thick_mode'] else '❌ 不可用'}")
        else:
            print(f"   ❌ 未安装 - {oracledb_info.get('error', '未知错误')}")
        
        # cx_Oracle状态
        print("\n🔧 cx_Oracle 状态:")
        cx_info = self.results['cx_oracle']
        if cx_info.get('available'):
            print(f"   ⚠️  已安装 v{cx_info['version']} (已过时)")
        else:
            print(f"   ℹ️  未安装")
        
        # 推荐建议
        print("\n💡 推荐建议:")
        for recommendation in self.results['recommendations']:
            print(f"   {recommendation}")
        
        print("\n" + "="*60)
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始Oracle驱动兼容性测试...")
        
        self.test_python_oracledb()
        self.test_cx_oracle()
        self.generate_recommendations()
        
        self.print_report()
        
        return self.results

def main():
    """主函数"""
    print("Oracle驱动兼容性测试工具")
    print("支持python-oracledb和cx_Oracle的检测")
    
    tester = OracleDriverTester()
    results = tester.run_all_tests()
    
    # 返回退出码
    if results['python_oracledb'].get('available'):
        return 0  # 成功
    else:
        return 1  # 需要安装python-oracledb

if __name__ == "__main__":
    sys.exit(main())