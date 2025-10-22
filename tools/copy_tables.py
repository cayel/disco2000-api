import os
from dotenv import load_dotenv
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

load_dotenv()
SOURCE_DB = os.getenv("SOURCE_DATABASE_URL")
DEST_DB = os.getenv("DEST_DATABASE_URL")

if not SOURCE_DB or not DEST_DB:
    raise RuntimeError("SOURCE_DATABASE_URL et DEST_DATABASE_URL doivent être définies dans .env")

async def copy_table(table_name):
    src_engine = create_async_engine(SOURCE_DB, future=True)
    dest_engine = create_async_engine(DEST_DB, future=True)
    async with src_engine.connect() as src_conn, dest_engine.connect() as dest_conn:
        result = await src_conn.execute(text(f'SELECT * FROM {table_name}'))
        rows = result.fetchall()
        if not rows:
            print(f"Aucune donnée à copier pour {table_name}")
            return
        columns = result.keys()
        values_str = ", ".join([f":{col}" for col in columns])
        insert_sql = f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES ({values_str})'
        for row in rows:
            await dest_conn.execute(text(insert_sql), dict(zip(columns, row)))
        await dest_conn.commit()
        print(f"Copié {len(rows)} lignes dans {table_name}")
    await src_engine.dispose()
    await dest_engine.dispose()

async def main():
    for table in ["labels", "artists", "albums"]:
        await copy_table(table)

if __name__ == "__main__":
    asyncio.run(main())
