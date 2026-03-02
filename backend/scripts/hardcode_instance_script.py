import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.application import AppInstance, AppTemplate
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Get Template
        stmt = select(AppTemplate).where(AppTemplate.id == 4)
        result = await session.execute(stmt)
        template = result.scalar_one_or_none()
        
        if not template:
            print("Template 4 not found!")
            return
            
        script = template.default_config.get('pre_deploy_script')
        if not script:
            print("Template 4 has no pre_deploy_script!")
            return
            
        print(f"Original script length: {len(script)}")
        
        # 2. Hardcode Variables (Bypass Jinja2 issues)
        # Replace Jinja2 placeholders with actual values
        script = script.replace('{{ external_url }}', 'http://10.20.1.204:5000')
        script = script.replace('{{ http_port }}', '5000')
        script = script.replace('{{ https_port }}', '443')
        script = script.replace('{{ hostname }}', '10.20.1.204')
        script = script.replace('{{ harbor_admin_password }}', 'Harbor12345')
        script = script.replace('{{ data_volume }}', '/data/harbor')
        
        # 3. Fix Private Key Generation (Force PKCS#1)
        # Find the line generating private key
        gen_key_cmd = "openssl genrsa -out $INSTALL_PATH/common/config/core/private_key.pem 4096"
        # Add conversion command after it
        convert_cmd = """
        openssl genrsa -out $INSTALL_PATH/common/config/core/private_key.pem 4096
        # Convert to PKCS#1 (Traditional) format for Harbor Core compatibility
        # Try with -traditional first (OpenSSL 3.0+)
        if openssl rsa -help 2>&1 | grep -q "traditional"; then
            openssl rsa -in $INSTALL_PATH/common/config/core/private_key.pem -out $INSTALL_PATH/common/config/core/private_key.pem.tmp -traditional
            mv $INSTALL_PATH/common/config/core/private_key.pem.tmp $INSTALL_PATH/common/config/core/private_key.pem
        else
            # Older OpenSSL defaults to PKCS#1 usually, or just rsa command works
            openssl rsa -in $INSTALL_PATH/common/config/core/private_key.pem -out $INSTALL_PATH/common/config/core/private_key.pem.tmp
            mv $INSTALL_PATH/common/config/core/private_key.pem.tmp $INSTALL_PATH/common/config/core/private_key.pem
        fi
        """
        script = script.replace(gen_key_cmd, convert_cmd)
        
        # 4. Update Instance
        stmt = select(AppInstance).where(AppInstance.id == 96)
        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if not instance:
            print("Instance 96 not found!")
            return
            
        new_config = dict(instance.config)
        new_config['pre_deploy_script'] = script
        new_config['http_port'] = 5000
        new_config['external_url'] = "http://10.20.1.204:5000"
        
        instance.config = new_config
        session.add(instance)
        await session.commit()
        
        print("Instance 96 updated with HARDCODED script.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
