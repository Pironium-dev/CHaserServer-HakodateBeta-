import socket
import multiprocessing
import time
import glob
import random
import json
from typing import NoReturn

from ReadConfig import ReadConfig


class GameRuleError(Exception):
    pass


config = ReadConfig().output_config()


class Game:
    direction: dict[str, tuple[int, int]] = {'r': (1, 0), 'l': (-1, 0), 'd': (0, 1), 'u': (0, -1)}

    def __init__(self, lock) -> None:
        self.lock = lock
        self.map_path = ''
        self.cool_items = 0
        self.hot_items = 0
        self.cool_name = ''
        self.hot_name = ''

        self.turn = 0
        self.map = []
        self.hot_place = [0, 0]
        self.cool_place = [0, 0]

        for_cool_pipe, self.cool_pipe = multiprocessing.Pipe()
        for_hot_pipe, self.hot_pipe = multiprocessing.Pipe()

        self.cool_receiver = multiprocessing.Process(
            target=Receiver, args=(for_cool_pipe,), name='Cool')
        self.cool_receiver.daemon = True
        self.hot_receiver = multiprocessing.Process(
            target=Receiver, args=(for_hot_pipe,), name='Hot')
        self.hot_receiver.daemon = True

        self.cool_receiver.start()
        self.hot_receiver.start()

        self.reflection_config()
        
        print(f'map:{config["NextStage"]}')
        self.print_map()

        while True:
            # Hot
            if self.hot_pipe.poll():
                match self.hot_pipe.recv():
                    case 'n':
                        name = self.hot_pipe.recv()
                        print(f'Hotに{name}が接続しました')
                        self.hot_name = name
            # Cool
            if self.cool_pipe.poll():
                match self.cool_pipe.recv():
                    case 'n':
                        name = self.cool_pipe.recv()
                        print(f'Coolに{name}が接続しました')
                        self.cool_name = name

            if self.cool_name and self.hot_name:
                input('Enter to Start')
                self.cool_pipe.send('s')
                self.hot_pipe.send('s')
                break

        for i in range(self.turn):
            self.cool_items, self.cool_place = self.action(
                self.cool_items, self.cool_place, self.cool_pipe, 'Cool')
            self.print_map()
            self.hot_items, self.hot_place = self.action(
                self.hot_items, self.hot_place, self.hot_pipe, 'Hot')
            self.print_map()
        
        self.game_set('', 0)

    def __output_square(self, is_gr, x, y) -> str:
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
        elif (ix == self.cool_place[0] and iy == self.cool_place[1]) or (ix == self.hot_place[0] and iy == self.hot_place[1]):
            return '1'
        else:
            return str(self.map[iy][ix])

    def print_map(self):
        self.lock.acquire()
        for i, y in enumerate(self.map):
            for j, x in enumerate(y):
                if self.cool_place[0] == j and self.cool_place[1] == i:
                    print('C', end=' ')
                elif self.hot_place[0] == j and self.hot_place[1] == i:
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
            self.hot_place = [0, 0]
            self.cool_place = [14, 16]

            self.turn = 100
        else:
            with open(self.map_path, 'r') as f:
                j = json.load(f)
                self.map = j['Map']
                self.hot_place = j['Hot']
                self.cool_place = j['Cool']
                self.turn = j['Turn']

        self.cool_pipe.send('c')
        self.cool_pipe.send(config['CoolPort'])
        self.cool_pipe.send(config['TimeOut'])
        self.cool_pipe.send('Off')

        self.hot_pipe.send('c')
        self.hot_pipe.send(config['HotPort'])
        self.hot_pipe.send(config['TimeOut'])
        self.hot_pipe.send(config['AntiBotMode'])

    def cool_disconnect(self):
        self.cool_pipe.send('d')

    def hot_disconnect(self):
        self.hot_pipe.send('d')

    def action(self, item, place, pipe, cl):
        pipe.send('t')
        pipe.recv()
        pipe.send(self.__output_square(True, *self.cool_place))
        r = pipe.recv()
        print(r)
        match r[0]:
            case 'w':
                place[0] += Game.direction[r[1]][0]
                place[1] += Game.direction[r[1]][1]
                pipe.send(self.__output_square(True, *self.cool_place))
                match self.__in_range(*place):
                    case '2':
                        pipe.send('d')
                        self.game_set(cl, 4)
                        
                    case '3':
                        item += 1
                        self.map[place[1]][place[0]] = 0
            case 'p':
                pass
            case 'l':
                pass
            case 's':
                pass
        return item, place
    
    def game_set(self, cl: str, state:int) -> NoReturn:
        '''
        state
        0: 通常ゲーム終了
        1: clがput勝ち
        2: clが敵を囲んだ
        3: clが自分を囲んだ
        4: clがブロックと重なった
        5: clが通信エラー
        '''
        match state:
            case 0:
                print('ゲームが終了しました')
                print(f'Cool: {self.cool_items}')
                print(f'Hot: {self.hot_items}')
            case 1:
                print(f'{cl}がput勝ちしました')
            case 2:
                print(f'{cl}が敵を囲みました')
            case 3:
                print(f'{cl}が自分を囲みました')
            case 4:
                print(f'{cl}がブロックと重なりました')
            case 5:
                print(f'{cl}が通信エラーしました')
        self.cool_pipe.send('d')
        self.hot_pipe.send('d')
        self.cool_pipe.recv()
        self.hot_pipe.recv()
        print('press enter')
        exit()


class Receiver:
    def __init__(self, pipe) -> None:
        self.pipe = pipe
        self.port = 0
        self.timeout = 0
        self.mode = 'Off'
        self.socket = socket.socket()
        self.to_cliant_socket = socket.socket()
        self.flag_socket = False  # socket が listenかどうか
        self.flag_to_cilant_socket = False  # to_cliant_socket が つながったかどうか
        self.flag_received_name = False

        while True:
            if self.pipe.poll():
                match self.pipe.recv():
                    case 'c':  # connect
                        self.port = pipe.recv()
                        self.timeout = pipe.recv()
                        self.mode = pipe.recv()
                        self.socket = socket.socket()
                        self.socket.setblocking(False)
                        self.socket.bind(('', self.port))
                        self.socket.listen()
                        self.flag_socket = True
                    case 'd':  # dis-connect
                        self.flag_socket = False
                        self.flag_to_cilant_socket = False
                        self.flag_received_name = False
                        self.to_cliant_socket.close()
                    case 's':  # start
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
                    self.pipe.send('n')  # Name
                    while True:
                        try:
                            self.pipe.send(self.to_cliant_socket.recv(
                                4096).decode('utf-8').strip())
                        except BlockingIOError:
                            continue
                        break
                    self.flag_received_name = True

        while True:
            match pipe.recv():
                case 't':  # your turn
                    self.to_cliant_socket.send(b'@')
                    if self.socket_receive() != 'gr':
                        self.close()
                    self.pipe.send('ok')
                    self.to_cliant_socket.send(
                        self.pipe.recv().encode('utf-8'))
                    self.pipe.send(self.socket_receive())
                    self.to_cliant_socket.send(
                        self.pipe.recv().encode('utf-8'))
                    if self.socket_receive() != '#':
                        self.close()
                case 'd':
                    self.close()

    def socket_receive(self):
        start = time.time()
        while True:
            if self.pipe.poll() and self.pipe.recv() == 'd':
                self.close()
            if time.time() - start >= self.timeout:
                self.close()
            try:
                r = self.to_cliant_socket.recv(4096).decode('utf-8').strip()
            except BlockingIOError:
                continue
            if r == '':
                continue
            return r

    def close(self) -> NoReturn:
        self.pipe.send('cl')  # closed
        self.to_cliant_socket.close()
        exit()


if __name__ == '__main__':
    lock = multiprocessing.Lock()

    game = Game(lock)
