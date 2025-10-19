import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger("db")
logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("La variable d'environnement DATABASE_URL n'est pas définie !")
else:
    logger.info(f"Chaîne de connexion PostgreSQL utilisée : {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL, echo=True)
    logger.info("Engine SQLAlchemy créé.")
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    Base = declarative_base()
    logger.info(f"Chaîne de connexion PostgreSQL utilisée : {DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, echo=True)
logger.info("Engine SQLAlchemy créé.")

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
