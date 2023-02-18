from typing import Dict
import json


class ReadConfig:
    def __init__(self):
        self.d: Dict = {}
        self.__read()

    def __read(self):
        with open('Config.dt', mode='r', encoding='utf-8') as f:
            self.d = json.load(f)

    def save(self):
        with open('Config.dt', 'w') as f:
            json.dump(self.d, f, indent=4)


if __name__ == '__main__':
    test = ReadConfig()
    print(test.d)
