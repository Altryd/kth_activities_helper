class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://<user>:<some_pswd>@172.18.0.2:3306/<db>>?charset=utf8mb4"
    secrets = {
        "client_id": 0,
        "client_secret": ""
    }
