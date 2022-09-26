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


if __name__ == '__main__':
    test = ReadConfig()
    print(test.output_config())
