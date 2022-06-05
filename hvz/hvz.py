from random import choice
import string
from datetime import datetime

GUILD_ID = 871424085064810516


class HVZ(object):

    def __init__(self, db, config):
        self.db = db
        self.config = config

    def generate_killcode(self, codes):
        code = "".join(choice(string.ascii_lowercase) for _ in range(6))
        while True:
            if code in codes:
                code = "".join(choice(string.ascii_lowercase) for _ in range(6))
            return code

    def create_user(self, username):
        print("Creating user...")
    
        # check to see if the user is already registered
        result = self.check_player(username)
        if result:
            user = result[0]
            killcode = user.killcode
            return "error", killcode

        all_codes = self.db.get_killcodes()
        new_code = self.generate_killcode(all_codes)
        self.db.init_player(username, new_code)

        return "ok", new_code

    def zombieify(self, username, code):
        result = self.db.has_user_code(code)
        if not len(result) > 0:
            return "error", "null"

        result = result[0]
        self.db.human_to_zombie(username, result)    
        return "ok", result

    def stun(self, message_lst):
        if len(message_lst) != 2:
            return "msg_len"
        shooter = message_lst[0]
        victim = message_lst[1]

        verify_shooter = self.db.has_user_id(shooter)
        verify_victim = self.db.has_user_id(victim)

        if len(verify_shooter) == 0 or len(verify_victim) == 0:
             return "f_usr_match"

        shooter = verify_shooter[0]
        victim = verify_victim[0]
       
        if shooter.status == "Zombie" or victim.status == "Human":
            return "f_stun_human"

        self.db.add_stun(shooter, victim)
        return "ok"    

    def check_player(self, username):
        result = self.db.has_user(username)
        if len(result) > 0:
            return result
        return False

    def get_profile(self, server, username):
        for user in server.members:
            if str(user) == username:
                return user

    def get_time_alive(self, player):
        if player.status == "Human":
            old_date = datetime.strptime(player.human_time, "%m%d%H%M%S")
            today = datetime.now().strftime("%m%d%H%M%S")
            today = datetime.strptime(today, "%m%d%H%M%S")
            new_date = str(today-old_date)
            return new_date
        else:
            return player.human_time

    def create_mission(self, text):
        result = self.db.mission_init(text, self.config.mission_path)
        return result

    def get_mission(self, mission_id):
        result = self.db.verify_mission_id(mission_id)
        if result == "error":
            return "error"

        result = self.db.get_mission(mission_id, self.config.mission_path)
        return result

    def name_split(self, username):
        discriminator = username[-4:]
        name = username[:-5]
        return name, discriminator
