from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# The application uses synchronous SQLAlchemy sessions, so normalize the resolved
# async-driver URL to the equivalent synchronous PyMySQL dialect for this engine.
engine_url = settings.database_url.replace("mysql+aiomysql", "mysql+pymysql", 1)
engine = create_engine(engine_url, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
