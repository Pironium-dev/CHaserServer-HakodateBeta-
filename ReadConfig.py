from typing import Dict
import json


class ReadConfig:
    def __init__(self):
        self.config: Dict = {}
        self.__read()

    def __read(self):
        with open('Config.dt', mode='r', encoding='utf-8') as f:
            self.config = json.load(f)

    def output_config(self):
        return self.config

    def save(self, ip):
        with open('Config.dt', 'w') as f:
            json.dump(ip, f, indent=4)


if __name__ == '__main__':
    test = ReadConfig()
    print(test.output_config())
