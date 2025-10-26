import os
import subprocess
from datetime import datetime

# Récupère les infos de connexion depuis les variables d'environnement
db_name = os.getenv("POSTGRES_DB")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST", "localhost")
db_port = os.getenv("POSTGRES_PORT", "5432")

# Nom du fichier de dump
date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
dump_file = f"db_backup_{db_name}_{date_str}.sql"

# Commande pg_dump
os.environ["PGPASSWORD"] = db_password or ""
cmd = [
    "pg_dump",
    "-h", db_host,
    "-p", db_port,
    "-U", db_user,
    "-F", "c",  # format custom (compressé, recommandé)
    "-b",       # inclut les blobs
    "-v",       # mode verbeux
    "-f", dump_file,
    db_name
]

print(f"Dump de la base {db_name} vers {dump_file} ...")
try:
    subprocess.run(cmd, check=True)
    print(f"Dump terminé avec succès : {dump_file}")
except subprocess.CalledProcessError as e:
    print("Erreur lors du dump :", e)