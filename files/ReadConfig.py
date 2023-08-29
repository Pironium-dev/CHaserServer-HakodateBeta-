from typing import Dict
import json


class ReadConfig:
    def __init__(self):
        self.d: Dict = {}
        self.__read()

    def __read(self):
        try:
            with open("Config.dt", mode="r", encoding="utf-8") as f:
                self.d = json.load(f)
        except FileNotFoundError:
            self.reset(True)

    def save(self):
        with open("Config.dt", "w") as f:
            json.dump(self.d, f, indent=4)

    def reset(self, f=False):
        with open("Config.dt", mode="w", encoding="utf-8") as f:
            self.d = {
                "GameSpeed": 500,
                "TimeOut": 2000,
                "LogPath": "./log",
                "StagePath": "./maps/",
                "NextMap": "Blank",
                "Score": False,
                "Log": False,
            }
            if f:
                self.d["CoolPort"] = 2009
                self.d["HotPort"] = 2010
                self.d["HotMode"] = "User"
                self.d["CoolMode"] = "User"
            json.dump(self.d, f, indent=4)
