import yaml

from sqlalchemy import create_engine, text
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

def main():
    # read the configs
    with open("config.yaml", "r") as f:
        conf = yaml.safe_load(f)

    #create engine
    db_url = f"postgresql://{conf['db']['user']}:{conf['db']['password']}@{conf['db']['host']}:{conf['db']['port']}/{conf['db']['name']}"
    print(f"Connection to {db_url}")
    db_engine = create_engine(db_url)

    # getting declarative class
    Base = declarative_base()

    class Data_Collection(Base):
        __tablename__ = 'collected_data'

        id = Column(Integer, nullable=False, primary_key=True)
        data_type = Column(String)
        description = Column(String)

    class Users(Base):
        __tablename__ = 'users'

        id = Column(Integer, nullable=False, primary_key=True)
        login = Column(String, nullable=False, unique=True)
        password = Column(String, nullable=False)
        created_at = Column(DateTime, nullable=False, default=text('now()'))
        last_request = Column(DateTime)

    # create the tables
    Base.metadata.create_all(db_engine)
    print("Tables created.")


def _old_main():
    # read the configs
    with open("config.yaml", "r") as f:
        conf = yaml.safe_load(f)

    db_url = f"postgresql://{conf['db']['user']}:{conf['db']['password']}@{conf['db']['host']}:{conf['db']['port']}/{conf['db']['name']}"
    print(f"Connection to {db_url}")
    db_engine = create_engine(db_url)

    with db_engine.connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS collected_data (
                id          Int     NOT NULL PRIMARY KEY,
                data_type   Char    ,
                description Text
            )
        """)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id              Int         NOT NULL PRIMARY KEY,
                login           Char        NOT NULL UNIQUE,
                password        Char        NOT NULL,
                created_at      timestamp   NOT NULL DEFAULT now(),
                last_request    timestamp
            )
        """))

    print("Tables created.")

if __name__ == "__main__":
    main()
