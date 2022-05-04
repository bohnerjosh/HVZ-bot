import sqlalchemy as db
from sqlalchemy.ext.declarative import delarative_base

class Player(Base):
    __tablename__ = "player"
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
    __tablename__ = "stats"
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
    __tablename__ = "missions"
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.String(10), unique=False, nullable=True)
    name = db.Column(db.String(20), unique=False, nullable=False)
    path = db.Column(db.string(40), unique=False, nullable=False)
    zombie_victory = db.Column(db.Integer)
    human_victory = db.Column(db.Integer)

    def __init__(self, start_time, name, path):
        self.start_time = start_time
        self.name = name
        self.path = path
        self.zombie_victory = 0
        self.human_victory = 0
