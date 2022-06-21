import json
from pathlib import Path

# globals that define pathnames for config object
DEFAULT_CONFIG_FOLDER = Path(".hvz")
DEFAULT_MISSION_FOLDER_NAME = "missions"
DEFAULT_DATA_FILE_NAME = "data.json"
DEFAULT_PREFIX = "!"
DEFAULT_DATA_FILE_CONTENTS = {
    "firsttimesetup": "True",
    "prefix" : DEFAULT_PREFIX,
    "mod_channel" : "0", 
    "missions_channel" : "0",
    "mods" : [],
    "gamestart" : ""
}

class Config(object):
    def __init__(self, path):
        self.params = {} # all current config values live in params while the program is running
        self.path = path / DEFAULT_CONFIG_FOLDER
        self.mission_path = self.path / DEFAULT_MISSION_FOLDER_NAME
        self.datapath = self.path / DEFAULT_DATA_FILE_NAME
        self.check_valid()
        self.load_data()

    # if any of the paths are missing, create them
    def check_valid(self):
        if not self.path.exists():
            self.path.mkdir()

        if not self.mission_path.exists():
            self.mission_path.mkdir()

        if not self.datapath.exists():
            # if data file is missing, write to it
            self.params = DEFAULT_DATA_FILE_CONTENTS
            self.write_data()
    
    # stores the contents of the config file in self.params
    def load_data(self):
        with open(str(self.datapath)) as f:
            self.params = json.load(f)
        
        # cast channel ids to ints
        self.params["mod_channel"] = int(self.params["mod_channel"])
        self.params["missions_channel"] = int(self.params["missions_channel"])
    
    # writes contents of self.params to config file
    def write_data(self, data=None):
        # serialize params
        json_obj = json.dumps(self.params, indent=4)

        # write json data to file
        with open(str(self.datapath), "w+") as f:
             f.write(json_obj)

    # update self.params with passed kwarg values
    def update_params(self, **kwargs):
        # if updating mods list, check to see if it is first time setup
        if "mods" in kwargs:
            self.params["mods"].append(kwargs["mods"])
            if self.params["firsttimesetup"] == "True":
                self.params["firsttimesetup"] = "False"
        else:
            for arg in kwargs:
                # cast channel ids to ints
                if arg == "mod_channel" or arg == "missions_channel":
                    self.params[arg] = int(kwargs[arg])
                else:
                    self.params[arg] = kwargs[arg]
        self.write_data()

    # delete the config file and make a new one
    def reset_config(self):
        self.datapath.unlink()
        self.check_valid()
        
