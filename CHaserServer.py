import socket
import multiprocessing
import time
import glob
import random
import json

from ReadConfig import ReadConfig


class GameRuleError(Exception):
    pass


config = ReadConfig().output_config()


def start_game():
    input('Press Enter')
    print('FIGHT')


class Game:
    def __init__(self, lock) -> None:
        self.lock = lock
        self.map_path = ''
        self.cool_items = 0
        self.hot_items = 0
        
        self.pipes = []
        self.receivers = []
        
        for_cool_pipe, self.cool_pipe = multiprocessing.Pipe()
        for_hot_pipe, self.hot_pipe = multiprocessing.Pipe()
        
        
        self.cool_receiver = multiprocessing.Process(target=Receiver, args=(for_cool_pipe,), name='Cool')
        self.hot_receiver = multiprocessing.Process(target=Receiver, args=(for_hot_pipe,), name='Hot')
        
        self.cool_receiver.start()
        self.hot_receiver.start()
        
        self.reflection_config()
        
        while True:
            # Hot
            if self.hot_pipe.poll():
                match self.hot_pipe.recv():
                    case 'n':
                        print(f'Hotに{self.hot_pipe.recv()}が接続しました')
            # Cool
            if self.cool_pipe.poll():
                match self.cool_pipe.recv():
                    case 'n':
                        print(f'Coolに{self.cool_pipe.recv()}が接続しました')

    def __output_square(self, x, y, is_gr=False) -> str:
        output = ''
        before_output = '1'
        for iy in range(-1, 2):
            for ix in range(-1, 2):
                if is_gr and ix == 0 and iy == 0:
                    if self.__in_range(ix + x, iy + y) == '2':
                        before_output = '0'
                    output += '0'
                else:
                    output += self.__in_range(ix + x, iy + y)
        return before_output + output

    def __output_line(self, x, y, ix, iy):
        output = '1'
        for i in range(9):
            x += ix
            y += iy
            output += self.__in_range(x, y)
        return output

    def __in_range(self, ix, iy):
        if not (0 <= ix <= 14 and 0 <= iy <= 16):
            return '2'
        elif (ix == self.posx[0] and iy == self.posy[0]) or (ix == self.posx[1] and iy == self.posy[1]):
            return '1'
        else:
            return str(self.map[iy][ix])

    def print_map(self):
        self.lock.acquire()
        for i, y in enumerate(self.map):
            for j, x in enumerate(y):
                if self.posx[0] == j and self.posy[0] == i:
                    print('C', end=' ')
                elif self.posx[1] == j and self.posy[1] == i:
                    print('H', end=' ')
                else:
                    print(x, end=' ')
            print('')
        print('')
        self.lock.release()
    
    def reflection_config(self):
        if config['NextStage'] == 'Random':
            self.map_path = random.choice(
                glob.glob(config['StagePath'] + r'/*.CHmap'))
        else:
            self.map_path = config['StagePath'] + \
                r'/' + config['NextStage'] + '.CHmap'

        if config['NextStage'] == 'Blank':
            self.map = [[0 for i in range(15)] for i in range(17)]
            self.posx = [0, 14]
            self.posy = [0, 16]
            self.turn = 100

        else:
            with open(self.map_path, 'r') as f:
                j = json.load(f)
                self.map = j['Map']
                self.posx = [j['Cool'][0], j['Hot'][0]]
                self.posy = [j['Cool'][1], j['Hot'][1]]
                self.turn = j['Turn']
        
        self.cool_pipe.send('c')
        self.cool_pipe.send(config['CoolPort'])
        self.cool_pipe.send(config['TimeOut'])
        self.cool_pipe.send('Off')
        
        self.hot_pipe.send('c')
        self.hot_pipe.send(config['HotPort'])
        self.hot_pipe.send(config['TimeOut'])
        self.hot_pipe.send(config['AntiBotMode'])


class Receiver:
    def __init__(self, pipe) -> None:
        self.pipe = pipe
        self.port = 0
        self.timeout = 0
        self.mode = 'Off'
        self.socket = socket.socket()
        self.to_cliant_socket = socket.socket()
        self.flag_socket = False # socket が listenかどうか 
        self.flag_to_cilant_socket = False # to_cliant_socket が つながったかどうか
        self.flag_received_name = False
        
        while True:
            if self.pipe.poll():
                match self.pipe.recv():
                    case 'c': # connect
                        self.port = pipe.recv()
                        self.timeout = pipe.recv()
                        self.mode = pipe.recv()
                        self.socket = socket.socket()
                        self.socket.setblocking(False)
                        self.socket.bind(('', self.port))
                        self.socket.listen()
                        self.flag_socket = True
                    case 'd': # dis-connect
                        self.flag_socket = False
                        self.flag_to_cilant_socket = False
                        self.flag_received_name = False
                        self.to_cliant_socket.close()
                    case 's': # start
                        break
            
            if self.flag_socket:
                try:
                    self.to_cliant_socket, _ = self.socket.accept()
                except BlockingIOError:
                    pass
                else:
                    self.flag_socket = False
                    self.flag_to_cilant_socket = True
            
            if self.flag_to_cilant_socket:
                if not self.flag_received_name:
                    self.pipe.send('n') # Name
                    while True:
                        try:
                            self.pipe.send(self.to_cliant_socket.recv(4096).decode('utf-8').strip())
                        except BlockingIOError:
                            continue
                        break
                    self.flag_received_name = True
                
        
        while True:
            match pipe.recv():
                case 's': # game set
                    break
                case 't': # your turn
                    pass
        
    def socket_receive(self):
        pass


def turn_end():
    pass


if __name__ == '__main__':
    lock = multiprocessing.Lock()

    game = Game(lock)