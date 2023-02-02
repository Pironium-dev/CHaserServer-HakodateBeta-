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

config = ReadConfig()

class Game:
    direction: dict[str, tuple[int, int]] = {
        'r': (1, 0), 'l': (-1, 0), 'd': (0, 1), 'u': (0, -1)}

    def __init__(self, lock) -> None:
        self.__lock = lock
        self.__map_path = ''
        self.cool_items = 0
        self.hot_items = 0
        self.cool_name = ''
        self.hot_name = ''

        self.turn = 0
        self.map = []
        self.hot_place = [0, 0]
        self.cool_place = [0, 0]

        for_cool_pipe, self.__cool_pipe = multiprocessing.Pipe()
        for_hot_pipe, self.__hot_pipe = multiprocessing.Pipe()

        self.__cool_receiver = multiprocessing.Process(
            target=Receiver, args=(for_cool_pipe,), name='Cool')
        self.__cool_receiver.daemon = True
        self.__hot_receiver = multiprocessing.Process(
            target=Receiver, args=(for_hot_pipe,), name='Hot')
        self.__hot_receiver.daemon = True

        self.__cool_receiver.start()
        self.__hot_receiver.start()

        self.__reflection_config()

        print(f'map:{config.d["NextStage"]}')
        self.print_map()

        self.cool_connect()
        self.hot_connect()

        while True:
            # Hot
            if self.__hot_pipe.poll():
                match self.__hot_pipe.recv():
                    case 'n':
                        name = self.__hot_pipe.recv()
                        print(f'Hotに{name}が接続しました')
                        self.hot_name = name
            # Cool
            if self.__cool_pipe.poll():
                match self.__cool_pipe.recv():
                    case 'n':
                        name = self.__cool_pipe.recv()
                        print(f'Coolに{name}が接続しました')
                        self.cool_name = name

            if self.cool_name and self.hot_name:
                input('Enter to Start')
                self.__cool_pipe.send('s')
                self.__hot_pipe.send('s')
                break

        for i in range(self.turn):
            print(f'turn: {i + 1}')
            self.cool_items, self.cool_place = self.__action(
                self.cool_items, self.cool_place, self.hot_place, self.__cool_pipe, 'Cool')
            self.print_map()
            self.hot_items, self.hot_place = self.__action(
                self.hot_items, self.hot_place, self.cool_place, self.__hot_pipe, 'Hot')
            self.print_map()
            time.sleep(config.d["GameSpeed"] / 1000)

        self.__game_set('', 0)

    def __output_square(self, is_gr, x, y) -> str:
        output = ''
        before_output = '1'
        for iy in range(-1, 2):
            for ix in range(-1, 2):
                if is_gr and ix == 0 and iy == 0:
                    if self.__in_range(ix + x, iy + y) == 2:
                        before_output = '0'
                    output += '0'
                else:
                    output += str(self.__in_range(ix + x, iy + y))
        return before_output + output

    def __output_line(self, x, y, ix, iy):
        output = '1'
        for i in range(9):
            x += ix
            y += iy
            output += str(self.__in_range(x, y))
        return output

    def __in_range(self, ix, iy) -> int:
        if not (0 <= ix <= 14 and 0 <= iy <= 16):
            return 2
        elif (ix == self.cool_place[0] and iy == self.cool_place[1]) or (ix == self.hot_place[0] and iy == self.hot_place[1]):
            return 1
        else:
            return self.map[iy][ix]

    def __enclosed(self, x, y) -> bool:
        if self.map[y - 1][x] == self.map[y + 1][x] == self.map[y][x - 1] == self.map[y][x + 1] == 2:
            return True
        return False

    def print_map(self):
        self.__lock.acquire()
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
        self.__lock.release()

    def __reflection_config(self):
        if config.d['NextStage'] == 'Random':
            self.__map_path = random.choice(
                glob.glob(config.d['StagePath'] + r'/*.CHmap'))
        else:
            self.__map_path = config.d['StagePath'] + \
                r'/' + config.d['NextStage'] + '.CHmap'

        if config.d['NextStage'] == 'Blank':
            self.map = [[0 for i in range(15)] for i in range(17)]
            self.hot_place = [0, 0]
            self.cool_place = [14, 16]
            self.turn = 100
        else:
            with open(self.__map_path, 'r') as f:
                j = json.load(f)
                self.map = j['Map']
                self.hot_place = j['Hot']
                self.cool_place = j['Cool']
                self.turn = j['Turn']

    def __action(self, item, place: list, enemy_place: list, pipe, cl):
        pipe.send('t')
        pipe.recv()
        pipe.send(self.__output_square(True, *self.cool_place))
        next_place = place.copy()
        r = pipe.recv()
        match r[0]:
            case 'w':
                next_place[0] += Game.direction[r[1]][0]
                next_place[1] += Game.direction[r[1]][1]
                pipe.send(self.__output_square(True, *next_place))
                match self.__in_range(*next_place):
                    case 2:
                        self.__game_set(cl, 4)
                    case 3:
                        item += 1
                        self.map[next_place[1]][next_place[0]] = 0
                        self.map[place[1]][place[0]] = 2

            case 'p':
                place[0] += Game.direction[r[1]][0]
                place[1] += Game.direction[r[1]][1]
                self.cool_place = next_place.copy()
                self.map[place[1]][place[0]] = 2
                pipe.send(self.__output_square(True, *next_place))
                if place == enemy_place:
                    self.__game_set(cl, 1)
                elif self.__enclosed(*enemy_place):
                    self.__game_set(cl, 2)
                elif self.__enclosed(*next_place):
                    self.__game_set(cl, 3)
            case 'l':
                pipe.send(self.__output_square(
                    False, place[0] + Game.direction[r[1]][0] * 2, place[1] + Game.direction[r[1]][1] * 2))
            case 's':
                pipe.send(self.__output_line(
                    place[0], place[1], *Game.direction[r[1]]))
            case 'C':
                self.__game_set(cl, 5)
        return item, next_place

    def __game_set(self, cl: str, state: int) -> NoReturn:
        '''
        state
        0: 通常ゲーム終了
        1: clがput勝ち
        2: clが敵を囲んだ
        3: clが自分を囲んだ
        4: clがブロックと重なった
        5: clが通信エラー
        '''
        self.print_map()
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
        self.__cool_pipe.send('d')
        self.__hot_pipe.send('d')
        input('press enter')
        exit()

    def cool_connect(self, port=2009, timeout=20000, anti_bot_mode='Stay'):
        if self.cool_name == '':
            self.__cool_pipe.send('c')
            self.__cool_pipe.send(port)
            self.__cool_pipe.send(timeout)
            self.__cool_pipe.send(anti_bot_mode)

    def hot_connect(self, port=2010, timeout=20000, anti_bot_mode='User'):
        if self.hot_name == '':
            self.__hot_pipe.send('c')
            self.__hot_pipe.send(port)
            self.__hot_pipe.send(timeout)
            self.__hot_pipe.send(anti_bot_mode)


class Receiver:
    def __init__(self, pipe) -> None:
        self.pipe = pipe
        self.port = 0
        self.timeout = 0
        self.mode = 'User'
        self.socket = socket.socket()
        self.to_cliant_socket = socket.socket()
        self.flag_socket = False  # socket が listenかどうか
        self.flag_to_cilant_socket = False  # to_cliant_socket が つながったかどうか
        self.flag_received_name = False
        self.flag_bot_name = False
        self.flag_ended = False

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
                        self.flag_bot_name = False
                        self.to_cliant_socket.close()
                    case 's':  # start
                        break

            if self.mode == 'Stay':
                if not self.flag_bot_name:
                    self.flag_socket = False
                    pipe.send('n')
                    pipe.send('Stay Bot')
                    self.flag_bot_name = True

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

        if self.mode == 'Stay':
            while True:
                if pipe.recv() != 'd':
                    self.pipe.send('ok')
                    pipe.recv()
                    self.pipe.send('lu')
                    self.pipe.recv()
                else:
                    exit()
        try:
            while True:
                match pipe.recv():
                    case 't':  # your turn
                        if self.flag_ended:
                            self.pipe.send('ok')
                            self.pipe.recv()
                            pipe.send('Cl')
                            exit()
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
        except EOFError:  # ゲーム終了時
            pass

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

    def close(self):
        self.flag_ended = True
        self.to_cliant_socket.close()


if __name__ == '__main__':
    lock = multiprocessing.Lock()
    game = Game(lock)
