import asyncio
import sys
sys.path.append('.')
from app.core.database import get_db
from app.models import User
from sqlalchemy import select

async def main():
    async for db in get_db():
        query = select(User)
        result = await db.execute(query)
        users = result.scalars().all()
        
        print("数据库中的用户:")
        for user in users:
            print(f"ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 激活状态: {user.is_active}")
        break

if __name__ == '__main__':
    asyncio.run(main())