import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # MySQL settings
    SQLALCHEMY_DATABASE_URI = (f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:"
                          f"{os.getenv('MYSQL_PASSWORD')}@127.0.0.1:3308/{os.getenv('MYSQL_DATABASE')}")
    DEBUG = True  # for echo
    # SQLALCHEMY_DATABASE_URI = "mysql+pymysql://<user>:<some_pswd>@172.18.0.2:3306/<db>>?charset=utf8mb4"
    # MySQL database filling
    FILL_MYSQL_IF_EMPTY = True  # fills the mysql database with test data

    # Web settings
    FASTAPI_HOST = "0.0.0.0"
    FASTAPI_PORT = 8000

    # secrets = ...


"""
class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://<user>:<some_pswd>@172.18.0.2:3306/<db>>?charset=utf8mb4"
    secrets = {
        "client_id": 0,
        "client_secret": ""
    }
"""