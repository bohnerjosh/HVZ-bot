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
    human_time = db.Column(db.String(10), unique=False, nullable=True)
    
    def __init__(self, username, killcode):
        self.username = username
        self.status = "Human"
        self.killcode = killcode
        self.failedcodes = 0
        self.human_time = datetime.now().strftime("%m%d%H%M%S")

    def __repr__(self):
        return self.username

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

class Stun(Base):
    __tablename__ = "Stun"
    id = db.Column(db.Integer, primary_key=True)
    shooter_id = db.Column(db.Integer, db.ForeignKey("Player.id"), nullable=False)
    victim_id = db.Column(db.Integer, db.ForeignKey("Player.id"), nullable=False)

    def __init__(self, shooter_id, victim_id):
        self.shooter_id = shooter_id
        self.victim_id = victim_id

class Tag(Base):
    __tablename__ = "Tag"
    id = db.Column(db.Integer, primary_key=True)
    tagger_id = db.Column(db.Integer, db.ForeignKey("Player.id"), nullable=False)
    victim_id = db.Column(db.Integer, db.ForeignKey("Player.id"), nullable=False)

    def __init__(self, tagger_id, victim_id):
        self.tagger_id = tagger_id
        self.victim_id = victim_id

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

    def has_user_id(self, u_id):
        statement = db.select(Player).filter_by(id=u_id)
        return self.un_tuple(self.session.execute(statement))

    def get_killcodes(self):
        statement = db.select(Player.killcode)
        return self.un_tuple(self.session.execute(statement).all())
        
    def init_player(self, username, killcode):
        player = Player(username, killcode) 
        self.session.add(player)
        self.session.commit()
        print(player.human_time)

    def has_user_code(self, code):
        statement = db.select(Player).filter_by(killcode=code)
        return self.un_tuple(self.session.execute(statement))

    def human_to_zombie(self, tagger_name, victim):
        victim.status = "Zombie"
        self.session.commit()

        old_date = datetime.strptime(victim.human_time, "%m%d%H%M%S")
        today = datetime.now().strftime("%m%d%H%M%S")
        today = datetime.strptime(today, "%m%d%H%M%S")
        new_date = today-old_date
        victim.human_time = str(new_date)

        self.session.commit()
        
        tagger = self.has_user(tagger_name)[0]
        tag = Tag(tagger.id, victim.id)
        self.session.add(tag)
        self.session.commit()

    def add_stun(self, shooter, victim):
        
        stun = Stun(shooter.id, victim.id)
        self.session.add(stun)
        self.session.commit()

    def get_user_ids(self):
        statement = db.select(Player)
        return self.un_tuple(self.session.execute(statement).all())

    def create_dict_stats(self, ids,_dict):
        for _id in ids:
            statement = db.select(Player.username).filter_by(id=_id)
            user = self.un_tuple(self.session.execute(statement))[0]
            if not user in _dict:
                _dict[user] = 1
            else:
                _dict[user] += 1 
        return _dict

    def get_stats(self, username):
        result = self.has_user(username)
        statement = db.select(Player).filter_by(username=username)
        player = self.un_tuple(self.session.execute(statement))[0]
        stuns = {}
        tags = {}
        tagger = ""

        if player.status == "Human":
            statement = db.select(Stun.victim_id).filter_by(shooter_id=player.id)
            s_ids = self.un_tuple(self.session.execute(statement).all())

            stuns = self.create_dict_stats(s_ids, stuns) 
            return player, tags, stuns, tagger
        else:
            statement = db.select(Stun.shooter_id).filter_by(victim_id=player.id)
            s_ids = self.un_tuple(self.session.execute(statement).all())
            
            stuns = self.create_dict_stats(s_ids, stuns)

            statement = db.select(Tag.victim_id).filter_by(tagger_id=player.id)
            t_ids = self.un_tuple(self.session.execute(statement).all())
     
            stuns = self.create_dict_stats(t_ids, stuns)
 
            statement = db.select(Tag.tagger_id).filter_by(victim_id=player.id)
            OG_t_id = self.un_tuple(self.session.execute(statement))[0]
            
            statement = db.select(Player.username).filter_by(id=OG_t_id)
            tagger = self.un_tuple(self.session.execute(statement))[0]

            return player, tags, stuns, tagger
