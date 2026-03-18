"""
检查数据库表
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings


async def check_database():
    """检查数据库表"""
    print("数据库 URL:", settings.DATABASE_URL)
    
    # 创建引擎
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # 检查 users 表
        from sqlalchemy import text
        result = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = result.scalars().all()
        
        print("\n数据库中的表:")
        for table in tables:
            print(f"  - {table}")
        
        # 检查 users 表结构
        print("\nusers 表结构:")
        result = await session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))
        columns = result.all()
        for col in columns:
            print(f"  - {col[0]} ({col[1]}, nullable={col[2]})")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_database())
