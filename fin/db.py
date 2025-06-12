from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager
import os


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage/fin.db")
engine = create_engine(DATABASE_URL, echo=False)


def migrate():
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
