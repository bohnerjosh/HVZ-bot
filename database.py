import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import os
from itertools import chain
from datetime import datetime

Base = declarative_base()

class Player(Base):
    __tablename__ = "Player"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(6), unique=False, nullable=False)
    killcode = db.Column(db.String(6), unique=True, nullable=False)
    failedcodes = db.Column(db.Integer, primary_key=False)

    def __init__(self, username, killcode):
        self.username = username
        self.status = "Human"
        self.killcode = killcode
        self.failedcodes = 0

    def __repr__(self):
        return self.username

class Stat(Base):
    __tablename__ = "Stats"
    id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey("Player.id"), nullable=False)
    human_time = db.Column(db.String(10), unique=False, nullable=True)
    stuns = db.Column(db.Integer, nullable=True)
    tagged_humans = db.Column(db.Integer, nullable=True)
    
    def __init__(self, u_id, human_time):
        self.u_id = u_id
        self.human_time = human_time
        self.stuns = 0
        self.tagged_humans = 0

class Mission(Base):
    __tablename__ = "Missions"
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.String(10), unique=False, nullable=True)
    name = db.Column(db.String(20), unique=False, nullable=False)
    path = db.Column(db.String(40), unique=False, nullable=False)
    zombie_victory = db.Column(db.Integer)
    human_victory = db.Column(db.Integer)

    def __init__(self, start_time, name, path):
        self.start_time = start_time
        self.name = name
        self.path = path
        self.zombie_victory = 0
        self.human_victory = 0

class Database(object):
    def __init__(self, path):
        self.path = path
        self.engine = None
        self.none_id = None
        self.session = None
        self.init_db()

    def un_tuple(self, data):
        return list(chain(*data))

    def init_engine(self):
        sqlite_uri = "sqlite:///" + os.path.abspath(self.path)
        self.engine = db.create_engine(sqlite_uri)
        self.session = Session(self.engine, future=True)

    def init_db(self):
        self.init_engine()
        try:
            statement = db.select(Player).filter_by(id=1)
            self.session.execute(statement).all()
        except(Exception):
            Base.metadata.create_all(self.engine)

    def has_user(self, username):
        statement = db.select(Player).filter_by(username=username)
        return self.un_tuple(self.session.execute(statement))

    def get_killcodes(self):
        statement = db.select(Player.killcode)
        return self.un_tuple(self.session.execute(statement).all())
        
    def init_player(self, username, killcode):
        player = Player(username, killcode)
        print(player.id)
        time = datetime.now().strftime("%m-%d-%Y %H:%M")
        
        self.session.add(player)
        self.session.commit()

        stat = Stat(player.id, time)
        self.session.add(stat)
        self.session.commit()
 
    def has_user_code(self, code):
        statement = db.select(Player).filter_by(killcode=code)
        return self.un_tuple(self.session.execute(statement))

    def human_to_zombie(self, player):
        player.status = "Zombie"
        self.session.commit()
