"""
数据库初始化脚本
用于在本地创建数据库表和初始数据
"""
import asyncio
import asyncpg
import os
from pathlib import Path

# 数据库连接信息
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "study_helper")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


async def init_database():
    """初始化数据库"""
    print(f"🔧 开始连接数据库 {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    
    try:
        # 连接到 PostgreSQL
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        print("✅ 数据库连接成功")
        
        # 读取 SQL 文件
        sql_file = Path(__file__).parent / "init-db" / "001_init.sql"
        if not sql_file.exists():
            print(f"❌ SQL 文件不存在：{sql_file}")
            await conn.close()
            return
        
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
        
        print("📄 读取 SQL 文件成功")
        
        # 执行 SQL
        print("🚀 开始执行数据库迁移...")
        await conn.execute(sql_content)
        
        print("✅ 数据库迁移完成")
        
        # 验证表是否创建
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        print(f"\n📊 已创建的表:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        await conn.close()
        print("\n✅ 数据库初始化完成!")
        
    except asyncpg.PostgresError as e:
        print(f"❌ 数据库错误：{e}")
        print("\n💡 请确保:")
        print("  1. PostgreSQL 已启动")
        print("  2. 数据库 'study_helper' 已创建")
        print("  3. 用户名密码正确")
        print("\n💡 可以使用 Docker 启动:")
        print("  docker-compose up -d postgres")
        
    except FileNotFoundError as e:
        print(f"❌ 文件未找到：{e}")
        
    except Exception as e:
        print(f"❌ 未知错误：{e}")


if __name__ == "__main__":
    print("=" * 60)
    print("📚 学习助手 - 数据库初始化脚本")
    print("=" * 60)
    print()
    
    asyncio.run(init_database())
