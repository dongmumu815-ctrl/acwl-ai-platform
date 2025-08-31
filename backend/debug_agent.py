import asyncio
import sys
sys.path.append('.')
from app.core.database import get_db
from app.models import Agent, ModelServiceConfig
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def main():
    async for db in get_db():
        query = select(Agent).options(
            selectinload(Agent.model_service_config)
        ).where(Agent.id == 32)
        result = await db.execute(query)
        agent = result.scalar_one_or_none()
        
        if agent:
            print(f'Agent ID: {agent.id}')
            print(f'Agent Name: {agent.name}')
            print(f'Model Config ID: {agent.model_service_config_id}')
            if agent.model_service_config:
                print(f'Provider: {agent.model_service_config.provider}')
                print(f'Model Name: {agent.model_service_config.model_name}')
                print(f'API Endpoint: {agent.model_service_config.api_endpoint}')
            else:
                print('Model config not found')
        else:
            print('Agent not found')
        break

if __name__ == '__main__':
    asyncio.run(main())