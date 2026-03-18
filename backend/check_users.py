"""
检查现有用户
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.user import User


async def check_users():
    """检查用户"""
    print("数据库 URL:", settings.DATABASE_URL)
    
    # 创建引擎
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # 查询所有用户
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"\n共有 {len(users)} 个用户:")
        for user in users:
            print(f"  - ID: {user.id}")
            print(f"    手机号：{user.phone}")
            print(f"    邮箱：{user.email}")
            print(f"    昵称：{user.nickname}")
            print(f"    状态：{'激活' if user.is_active else '禁用'}")
            print(f"    创建时间：{user.created_at}")
            print()
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_users())
