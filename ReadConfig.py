from typing import Dict
import json


class ReadConfig:
    def __init__(self):
        self.d: Dict = {}
        self.__read()

    def __read(self):
        try:
            with open('Config.dt', mode='r', encoding='utf-8') as f:
                self.d = json.load(f)
        except FileNotFoundError:
            self.reset()

    def save(self):
        with open('Config.dt', 'w') as f:
            json.dump(self.d, f, indent=4)


    def reset(self):
        with open('Config.dt', mode='w', encoding='utf-8') as f:
            self.d = {"CoolPort": 2009, "HotPort": 2010, "GameSpeed": 100, "TimeOut": 2000, "HotMode": "User",
                 "CoolMode": "User", "LogPath": "./log", "StagePath": "./maps/", "NextMap": "Blank", "Score": False, "Log": False}
            json.dump(self.d, f, indent=4)


if __name__ == '__main__':
    test = ReadConfig()
    test.reset()
