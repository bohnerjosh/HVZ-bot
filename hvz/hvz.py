from random import choice
import string
from datetime import datetime

# globals for string matching role names
ZOMBIE_WINS = ["Zombie", "Zombies", "zombie", "zombies"]
HUMAN_WINS = ["Human", "Humans", "human", "humans"]

# class that handles general HVZ game logic
class HVZ(object):

    def __init__(self, db, config):
        # internal references to db and config objects
        self.db = db
        self.config = config

    # parses a filename and returns the mission id
    def get_mission_id(self, filename):
        dot = filename.find(".")
        m_id = filename[:dot]
        return m_id

    # generates a random series of characters to represent a secret code for a player
    def generate_killcode(self, codes):
        # randomly choose characters
        code = "".join(choice(string.ascii_lowercase) for _ in range(6))
        while True:
            if code in codes:
                code = "".join(choice(string.ascii_lowercase) for _ in range(6))
            return code

    # creates a player internally and saves their data to the database
    def create_user(self, username):
        print("Creating user...")
    
        # check to see if the user is already registered
        result = self.check_player(username)
        if result:
            user = result[0]
            killcode = user.killcode
            return "error", killcode

        # get codes to make sure the generated killcode is unique
        # then create the killcode and init them in the database
        all_codes = self.db.get_killcodes()
        new_code = self.generate_killcode(all_codes)
        self.db.init_player(username, new_code)

        return "ok", new_code

    # converts a tagged human into a zombie by verifying their killcode
    def zombieify(self, username, code, override=False):
        # verify the authenticity of the killcode
        result = self.db.has_user_code(code)
        if not len(result) > 0:
            return "error", None

        result = result[0]
        
        # change player data in db from human to zombie
        transfer_result = self.db.human_to_zombie(username, result) 
        if transfer_result == "error" and not override:
            return "illegal_zombieify", None
   
        return "ok", result

    # allows humans to track number of stuns they perform on humans
    def stun(self, shooter, victim):
        # verify that shooter and victim are registered
        verify_shooter = self.db.has_user_id(shooter)
        verify_victim = self.db.has_user_id(victim)

        # if not raise an error
        if len(verify_shooter) == 0 or len(verify_victim) == 0:
             return "f_usr_match"

        shooter = verify_shooter[0]
        victim = verify_victim[0]
       
        # humans cannot be stunned, and zombies cannot stun
        if shooter.status == "Zombie" or victim.status == "Human":
            return "f_stun_human"

        # log the stun in a db
        self.db.add_stun(shooter, victim)
        return "ok"    

    # verifies a player is registered in the database by username
    def check_player(self, username):
        result = self.db.has_user(username)
        if len(result) > 0:
            # return the player object
            return result
        return False

    # returns the amount of time a human has been "alive" since the start of the game
    def get_time_alive(self, player):
        if player.status == "Human":
            # player object, strptime converts to a datetime object, strftime converts to string

            # figure out how long the player has been a human by subtracting
            # the amount of time since the beginning of the game and current time
            old_date = datetime.strptime(player.human_time, "%m%d%H%M%S")
            today = datetime.now().strftime("%m%d%H%M%S")
            today = datetime.strptime(today, "%m%d%H%M%S")
            new_date = str(today-old_date)
            return new_date
        else:
            return player.human_time

    # handles the creation and modification of missions
    def handle_mission(self, filename, text):
        # extract mission id from file name and make sure it doesn't already exist
        mission_id = self.get_mission_id(filename)
        result = self.db.verify_mission_id(mission_id)

        # if fail, mission id is unique
        if result == "error":
            m_id = self.db.mission_init(text, self.config.mission_path)
            return m_id, "init"
        else:
            # otherwise, modify existing mission
            m_id = self.db.modify_mission(text, result.id, self.config.mission_path)
            return m_id, "modify"

    # returns info about a single mission
    def get_mission(self, mission_id):
        # verify the mission id, return if it doesn't exist
        result = self.db.verify_mission_id(mission_id)
        if result == "error":
            return "error"

        # get the mission info from db
        result = self.db.get_mission(mission_id, self.config.mission_path)
        return result

    # split a given discord profile name into its username and discriminator
    def name_split(self, username):
        discriminator = username[-4:]
        name = username[:-5]
        return name, discriminator

    # change internal status of a mission to reflect game winner of mission
    def determine_winner(self, mission_id, winner):
        # find mission by given mission id
        mission = self.db.verify_mission_id(mission_id)
        
        # if it doesn't exist, return
        if mission == "error":
            return "invalid_mission"

        # award proper team the victory and update db
        if winner in ZOMBIE_WINS:
            self.db.close_mission(mission, "Zombie")       
            result = "Zombie"    
        elif winner in HUMAN_WINS:
            self.db.close_mission(mission, "Human")
            result = "Human"
        else:
            return "invalid_winner"

        return result

    # chooses an OZ with random library 
    def choose_OZ(self):
        # get list of all players in OZ pool
        volunteers = self.db.get_OZ_pool()

        # if pool is empty, return none
        if len(volunteers) == 0:
            return None

        # return a random player
        return choice(volunteers)

    # remove player from OZ pool via db
    def remove_from_OZ_pool(self, player):
        self.db.rempve_OZ_pool(player)

  
