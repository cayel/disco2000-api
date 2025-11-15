#!/usr/bin/env python3
"""
Script pour appliquer les migrations SQL manuellement.
Usage: python apply_migration.py sql/06-migration_artist_country.sql
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from db import engine

load_dotenv()

async def apply_migration(sql_file: str):
    """Applique une migration SQL à la base de données."""
    sql_path = Path(sql_file)
    
    if not sql_path.exists():
        print(f"❌ Fichier introuvable : {sql_file}")
        sys.exit(1)
    
    print(f"📄 Lecture de {sql_file}...")
    sql_content = sql_path.read_text()
    
    print(f"🔄 Application de la migration...")
    async with engine.begin() as conn:
        await conn.execute(sql_content)
    
    print(f"✅ Migration appliquée avec succès : {sql_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python apply_migration.py <chemin_vers_fichier.sql>")
        print("Exemple: python apply_migration.py sql/06-migration_artist_country.sql")
        sys.exit(1)
    
    sql_file = sys.argv[1]
    asyncio.run(apply_migration(sql_file))
