import asyncio
from db import Base, engine

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables créées avec succès.")

if __name__ == "__main__":
    asyncio.run(create_tables())
