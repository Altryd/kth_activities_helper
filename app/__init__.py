import os

from sqlalchemy import create_engine, func
from models import Base, Player, Matches
from sqlalchemy.orm import Session
import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from app.config import Config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)


engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=False)

Base.metadata.bind = engine
Base.metadata.create_all(engine)


"""


db = SQLAlchemy(app)
migrate = Migrate(app, db)
db_metadata = db.metadata
login_manager = LoginManager()
login_manager.init_app(app)

CORS(app, resources={r'/*': {'origins': '*'}})"""