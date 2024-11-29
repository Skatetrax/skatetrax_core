from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os


db_url = os.environ.get('pgdb_host', -1)
db_name = os.environ.get('pgdb_name', -1)
db_user = os.environ.get('pgdb_user', -1)
passwd = os.environ.get('pgdb_password', -1)

engine = create_engine(f'postgresql://{db_user}:{passwd}@{db_url}/{db_name}')
Session = sessionmaker(bind=engine)
