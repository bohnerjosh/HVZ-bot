import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import os
from itertools import chain
from datetime import datetime
from pathlib import Path

# class Globals
Base = declarative_base()
DEFAULT_DB_NAME = "db"

######################
###  DEFINE TABLES ###
######################

class Player(Base):
    __tablename__ = "Player"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False) # discord username
    status = db.Column(db.String(6), unique=False, nullable=False) # human or zombie
    killcode = db.Column(db.String(6), unique=True, nullable=False)
    failedcodes = db.Column(db.Integer, primary_key=False)
    human_time = db.Column(db.String(10), unique=False, nullable=True)
    oz_pool = db.Column(db.Integer, nullable=False) # acts as bool
    is_oz = db.Column(db.Integer, nullable=False) # acts as bool
    
    def __init__(self, username, killcode):
        self.username = username
        self.status = "Human"
        self.killcode = killcode
        self.failedcodes = 0
        self.human_time = "0"
        self.oz_pool = 0
        self.is_oz = 0

    def __repr__(self):
        return self.username

class Mission(Base):
    __tablename__ = "Missions"
    id = db.Column(db.Integer, primary_key=True)
    zombie_victory = db.Column(db.Integer) # acts as bool
    human_victory = db.Column(db.Integer) # acts as bool

    def __init__(self):
        self.zombie_victory = 0
        self.human_victory = 0

# keeps track of how many zombies humans have stunned
class Stun(Base):
    __tablename__ = "Stun"
    id = db.Column(db.Integer, primary_key=True)
    shooter_id = db.Column(db.Integer, db.ForeignKey("Player.id"), nullable=False)
    victim_id = db.Column(db.Integer, db.ForeignKey("Player.id"), nullable=False)

    def __init__(self, shooter_id, victim_id):
        self.shooter_id = shooter_id
        self.victim_id = victim_id

# keeps track of how many humans zombies have tagged
class Tag(Base):
    __tablename__ = "Tag"
    id = db.Column(db.Integer, primary_key=True)
    tagger_id = db.Column(db.Integer, db.ForeignKey("Player.id"), nullable=False)
    victim_id = db.Column(db.Integer, db.ForeignKey("Player.id"), nullable=False)

    def __init__(self, tagger_id, victim_id):
        self.tagger_id = tagger_id
        self.victim_id = victim_id

class Database(object):
    def __init__(self, config):
        self.config = config # reference to config object
        self.path = self.config.path / DEFAULT_DB_NAME
        self.mission_path = self.config.mission_path

        # db objects
        self.engine = None
        self.none_id = None
        self.session = None
        self.init_db()

    # converts the output of a query from a tuple to a list
    def un_tuple(self, data):
        return list(chain(*data))

    # initializes the database engine
    def init_engine(self):
        sqlite_uri = "sqlite:///" + os.path.abspath(self.path) # absolute path of database
        self.engine = db.create_engine(sqlite_uri)
        self.session = Session(self.engine, future=True)

    # initializes the database when the bot starts. Calls init_engine()
    def init_db(self):
        self.init_engine()
        # tests to see if the database exists. if not, a new one is created
        try:
            statement = db.select(Player).filter_by(id=1)
            self.session.execute(statement).all()
        except(Exception):
            Base.metadata.create_all(self.engine)

    # checks database to see if a player exists via username
    def has_user(self, username):
        statement = db.select(Player).filter_by(username=username)
        return self.un_tuple(self.session.execute(statement))

    # checks database to see if a player exists via id
    def has_user_id(self, u_id):
        statement = db.select(Player).filter_by(id=u_id)
        return self.un_tuple(self.session.execute(statement))

    # gets all player killcodes
    def get_killcodes(self):
        statement = db.select(Player.killcode)
        return self.un_tuple(self.session.execute(statement).all())
        
    # initialize player object for db
    def init_player(self, username, killcode):
        player = Player(username, killcode) 
        self.session.add(player)
        self.session.commit()

    # checks to see if the database has a given killcode and returns the matching player object
    def has_user_code(self, code):
        statement = db.select(Player).filter_by(killcode=code)
        return self.un_tuple(self.session.execute(statement))

    # changes a player object's status to zombie to become OZ
    def OZ_status(self, player):
        player.status = "Zombie"
        player.human_time = "0"
        player.is_oz = 1
        self.session.commit()

    # converts a human tagged by a zombie into a zombie after killcode is verified
    def human_to_zombie(self, tagger_name, victim):
        # verify tagger, cannot be a human
        tagger = self.has_user(tagger_name)[0]
        if tagger.status == "Human":
            return "error"

        # change the human into a zombie and update db
        victim.status = "Zombie"
        self.session.commit()

        # update the player's human time (subtract current time from start of game time)
        old_date = datetime.strptime(victim.human_time, "%m%d%H%M%S")
        today = datetime.now().strftime("%m%d%H%M%S")
        today = datetime.strptime(today, "%m%d%H%M%S")
        new_date = today-old_date
        victim.human_time = str(new_date)

        self.session.commit() # update database
        
        # log conversion as a tag
        tag = Tag(tagger.id, victim.id)
        self.session.add(tag)
        self.session.commit()

    # log a stun (human shoots a zombie)
    def add_stun(self, shooter, victim):
        stun = Stun(shooter.id, victim.id)
        self.session.add(stun)
        self.session.commit()

    # returns the internal ids of all Player objects
    def get_users(self):
        statement = db.select(Player)
        return self.un_tuple(self.session.execute(statement).all())

    # generates game statistics (tags and stuns) in human readable form for get_stats
    def create_dict_stats(self, ids,_dict):
        for _id in ids:
            statement = db.select(Player.username).filter_by(id=_id)
            user = self.un_tuple(self.session.execute(statement))[0]
            if not user in _dict:
                _dict[user] = 1
            else:
                _dict[user] += 1 
        return _dict

    # generates game statistics for a user in human readable form
    def get_stats(self, username):
        # get the player object associated with the username
        statement = db.select(Player).filter_by(username=username)
        player = self.un_tuple(self.session.execute(statement))[0]

        # initialize data structures for holding statistics
        stuns = {}
        tags = {}
        tagger = ""

        # process differs between humans and zombies
        if player.status == "Human":

            # get all instances where human stunned zombies and itemize them
            statement = db.select(Stun.victim_id).filter_by(shooter_id=player.id)
            s_ids = self.un_tuple(self.session.execute(statement).all())

            stuns = self.create_dict_stats(s_ids, stuns) 
            return player, tags, stuns, tagger
        else:
            # get all instances where zombie was stunned by humans
            statement = db.select(Stun.shooter_id).filter_by(victim_id=player.id)
            s_ids = self.un_tuple(self.session.execute(statement).all())
            
            # itemize data
            stuns = self.create_dict_stats(s_ids, stuns)

            # get all instances where zombie tagged human
            statement = db.select(Tag.victim_id).filter_by(tagger_id=player.id)
            t_ids = self.un_tuple(self.session.execute(statement).all())
     
            tags = self.create_dict_stats(t_ids, tags)
 
            # find who caused the player to be a zombie
            statement = db.select(Tag.tagger_id).filter_by(victim_id=player.id)
            OG_t_id = self.un_tuple(self.session.execute(statement))[0]
            
            statement = db.select(Player.username).filter_by(id=OG_t_id)
            tagger = self.un_tuple(self.session.execute(statement))[0]

            return player, tags, stuns, tagger

    # modify a existing mission
    def modify_mission(self, mission_text, mission_id, default_path):
        with open(str(self.mission_path / str(mission_id)), "w") as mFile:
            mFile.write(mission_text)
        return mission_id

    # create a new mission file and new mission object
    def mission_init(self, mission_text, default_path):
        mission = Mission()
        self.session.add(mission)
        self.session.commit()

        # create a new mission file in mission folder
        mission_id = str(mission.id)
        with open(str(self.mission_path / mission_id), "w") as mFile:
            mFile.write(mission_text)
        return mission_id

    # check to see if a mission id exists in the database
    def verify_mission_id(self, _id):
        statement = db.select(Mission).filter_by(id=_id)
        mission = self.un_tuple(self.session.execute(statement))
        if len(mission) == 0:
            return "error"
        return mission[0]

    # get all missions from internal db and path
    def get_missions(self):
        statement = db.select(Mission)
        missions = self.un_tuple(self.session.execute(statement).all())
        mission_dict = {}
        text = ""

        # make mission info human readable
        for mission in missions:
            m_id = str(mission.id)
            with open(str(self.mission_path / m_id), "r") as mFile:
                text = mFile.readline()
            mission_dict[m_id] = text
            text = ""

        return mission_dict

    # gets data for a single mission
    def get_mission(self, m_id, default_path):
        text = ""
        # open mission file by name (id)
        with open(str(self.mission_path / m_id), "r") as mFile:
            text = mFile.read()
        return text

    # declare a winner for a particular mission
    def close_mission(self, mission, winner):
        if winner == "Zombie":
            mission.zombie_victory = 1

        elif winner == "Human":
            mission.human_victory = 1

        self.session.commit()
    
    # add a player to the OZpool
    def add_to_OZ_lst(self, username):
        statement = db.select(Player).filter_by(username=username)
        player = self.un_tuple(self.session.execute(statement))[0]

        player.oz_pool = 1
        self.session.commit()

    # get all players in OZ pool
    def get_OZ_pool(self):
        statement = db.select(Player).filter_by(oz_pool=1)
        return self.un_tuple(self.session.execute(statement).all())

    # remove a player from the OZ pool
    def remove_from_OZ_pool(self, player):
        player.oz_pool = 0
        self.session.commit()

    # take OZ status away from player
    def take_OZ(self, player):
        player.is_oz = 0
        player.status = "Human"
        self.session.commit()

    def set_default_human_time(self):
        users = self.get_users()
        for user in users:
            user.human_time = datetime.now().strftime("%m%d%H%M%S")
            self.session.commit()
