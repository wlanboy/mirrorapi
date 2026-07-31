import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

DATABASE_DIR = os.environ.get("DATABASE_DIR", "/data")
DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'mirror_data.db')}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def before_scenario(context, scenario):
    try:
        with Session() as session:
            session.execute(text("DELETE FROM mirror_pairs"))
            session.commit()
    except OperationalError:
        # Table might not exist yet, that's OK
        pass


def after_scenario(context, scenario):
    try:
        with Session() as session:
            session.execute(text("DELETE FROM mirror_pairs"))
            session.commit()
    except OperationalError:
        # Table might not exist, that's OK
        pass
