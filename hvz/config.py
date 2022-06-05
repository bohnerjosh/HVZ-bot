import json
from pathlib import Path

DEFAULT_CONFIG_FOLDER = Path(".hvz")
DEFAULT_MISSION_FOLDER_NAME = "missions"
DEFAULT_DATA_FILE_NAME = "data.json"
DEFAULT_PREFIX = "!"

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
            with open(str(self.datapath), "w+") as f:
                f.write("{\n\"prefix\": \"" + DEFAULT_PREFIX + "\"\n}") 
    
    def load_data(self):
        with open(str(self.datapath)) as f:
            self.params = json.load(f)
                
