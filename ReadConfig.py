from typing import Dict


class ReadConfig:
    def __init__(self):
        self.names: list = ('CoolPort', 'HotPort', 'ProgressOfGame', 'TimeOut', 'AntiBotMode')
        self.config: Dict = {}
        self.__Read()

    def __Read(self):
        with open('Config.dt', mode='r', encoding='utf-8') as f:
            for name, item in zip(self.names, f.readlines()):
                self.config[name] = int(item)

    def output_config(self):
        return self.config


if __name__ == '__main__':
    test = ReadConfig()
    print(test.output_config())
