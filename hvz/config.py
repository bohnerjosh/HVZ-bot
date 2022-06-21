import json
from pathlib import Path

DEFAULT_CONFIG_FOLDER = Path(".hvz")
DEFAULT_MISSION_FOLDER_NAME = "missions"
DEFAULT_DATA_FILE_NAME = "data.json"
DEFAULT_PREFIX = "!"
DEFAULT_DATA_FILE_CONTENTS = {
    "firsttimesetup": "True",
    "prefix" : DEFAULT_PREFIX,
    "mod_channel" : "0", 
    "missions_channel" : "0",
    "mods" : []
}

class Config(object):
    def __init__(self, path):
        self.params = {}
        self.path = path / DEFAULT_CONFIG_FOLDER
        self.mission_path = self.path / DEFAULT_MISSION_FOLDER_NAME
        self.datapath = self.path / DEFAULT_DATA_FILE_NAME
        self.check_valid()
        self.load_data()

    def check_valid(self):
        if not self.path.exists():
            self.path.mkdir()

        if not self.mission_path.exists():
            self.mission_path.mkdir()

        if not self.datapath.exists():
            self.params = DEFAULT_DATA_FILE_CONTENTS
            self.write_data()
    
    def load_data(self):
        with open(str(self.datapath)) as f:
            self.params = json.load(f)
        # cast channel ids to ints
        self.params["mod_channel"] = int(self.params["mod_channel"])
        self.params["missions_channel"] = int(self.params["missions_channel"])
    
    def write_data(self, data=None):
        # serialize the dictionary
        json_obj = json.dumps(self.params, indent=4)

        # write json data to file
        with open(str(self.datapath), "w+") as f:
             f.write(json_obj)

    def update_params(self, **kwargs):
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

    def reset_config(self):
        self.datapath.unlink()
        self.check_valid()
        
