from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from app.config import Config
from models import Base, Player, Matches

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)


engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=False)

Base.metadata.bind = engine
Base.metadata.create_all(engine)
