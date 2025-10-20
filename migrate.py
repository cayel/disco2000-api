
import asyncio
from dotenv import load_dotenv
load_dotenv()
from db import Base, engine

async def migrate():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Migration terminée : tables créées si elles n'existaient pas.")

if __name__ == "__main__":
    asyncio.run(migrate())
