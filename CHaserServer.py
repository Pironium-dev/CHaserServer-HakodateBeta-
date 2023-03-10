import socket
import multiprocessing
import time
import glob
import random
import json
from typing import NoReturn

from ReadConfig import ReadConfig

# 壁:2 クライアント:1 アイテム:3 
class Game:
    direction: dict[str, tuple[int, int]] = {
        'r': (1, 0), 'l': (-1, 0), 'd': (0, 1), 'u': (0, -1)}

    def __init__(self, pipe) -> None:
        self.lock = multiprocessing.Lock()
        self.map_directory = ReadConfig().d['StagePath']
        self.cool_items = 0
        self.hot_items = 0
        self.cool_name = ''
        self.hot_name = ''
        
        self.cool_port = 2009
        self.hot_port = 2010
        self.cool_mode = ''
        self.hot_mode = ''

        self.turn = 0
        self.map = []
        self.hot_place = [0, 0]
        self.cool_place = [0, 0]
        
        self.timeout = 0
        self.map_name = 'Blank'

        for_cool_pipe, self.cool_pipe = multiprocessing.Pipe()
        for_hot_pipe, self.hot_pipe = multiprocessing.Pipe()
        self.window_pipe = pipe

        self.cool_receiver = multiprocessing.Process(
            target=Receiver, args=(for_cool_pipe,), name='Cool')
        self.cool_receiver.daemon = True
        self.hot_receiver = multiprocessing.Process(
            target=Receiver, args=(for_hot_pipe,), name='Hot')
        self.hot_receiver.daemon = True

        self.cool_receiver.start()
        self.hot_receiver.start()

        while True:
            # Hot
            if self.window_pipe.poll():
                match self.window_pipe.recv():
                    case 'C':
                        match self.window_pipe.recv():
                            case 'connect':
                                self.cool_port = self.window_pipe.recv()
                                self.cool_mode = self.window_pipe.recv()
                                self.cool_connect()
                            case 'disconnect':
                                self.cool_disconnect()
                    case 'H':
                        match self.window_pipe.recv():
                            case 'connect':
                                self.hot_port = self.window_pipe.recv()
                                self.hot_mode = self.window_pipe.recv()
                                self.hot_connect()
                            case 'disconnect':
                                self.hot_disconnect()
                    case 'start':
                        self.map_name = self.window_pipe.recv()
                        self.change_map()
                        
                        self.timeout = self.window_pipe.recv()
                        
                        self.cool_pipe.send('s')
                        self.cool_pipe.send(self.timeout)

                        self.hot_pipe.send('s')
                        self.hot_pipe.send(self.timeout)
                        break
            
            if self.hot_pipe.poll():
                match self.hot_pipe.recv():
                    case 'n':
                        name = self.hot_pipe.recv()
                        self.window_pipe.send('H')
                        self.window_pipe.send('name')
                        self.window_pipe.send(name)
                        self.hot_name = name
                    case 'd':
                        self.window_pipe.send('H')
                        self.window_pipe.send('disconnect')
            
            if self.cool_pipe.poll():
                match self.cool_pipe.recv():
                    case 'n':
                        name = self.cool_pipe.recv()
                        self.window_pipe.send('C')
                        self.window_pipe.send('name')
                        self.window_pipe.send(name)
                        self.cool_name = name
                    case 'd':
                        self.window_pipe.send('C')
                        self.window_pipe.send('disconnect')

        self.window_pipe.recv()
        for i in range(self.turn):
            print(f'turn: {i + 1}')
            self.cool_items, self.cool_place = self.action(
                self.cool_items, self.cool_place, self.hot_place, self.cool_pipe, 'Cool')
            self.window_pipe.send('ok')
            self.window_pipe.recv()
            self.hot_items, self.hot_place = self.action(
                self.hot_items, self.hot_place, self.cool_place, self.hot_pipe, 'Hot')
            self.window_pipe.send('ok')
            self.window_pipe.recv()

        self.game_set('', 0)

    def output_square(self, is_gr, x, y) -> str:
        output = ''
        before_output = '1'
        for iy in range(-1, 2):
            for ix in range(-1, 2):
                if is_gr and ix == 0 and iy == 0:
                    if self.in_range(ix + x, iy + y) == 2:
                        before_output = '0'
                    output += '0'
                else:
                    output += str(self.in_range(ix + x, iy + y))
        return before_output + output

    def output_line(self, x, y, ix, iy):
        output = '1'
        for i in range(9):
            x += ix
            y += iy
            output += str(self.in_range(x, y))
        return output

    def in_range(self, ix, iy) -> int:
        if not (0 <= ix <= 14 and 0 <= iy <= 16):
            return 2
        elif (ix == self.cool_place[0] and iy == self.cool_place[1]) or (ix == self.hot_place[0] and iy == self.hot_place[1]):
            return 1
        else:
            return self.map[iy][ix]

    def enclosed(self, x, y) -> bool:
        for _, (i, j) in Game.direction.items():
            try:
                if self.map[y + i][x + j] == 2:
                    continue
            except IndexError:
                continue
            return False
        return True

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

    def change_map(self):
        if self.map_name == 'Blank':
            self.map = [[0 for i in range(15)] for i in range(17)]
            self.hot_place = [8, 9]
            self.cool_place = [6, 7]
            self.turn = 100
        else:
            with open(self.map_directory + r'/' + self.map_name + '.CHmap', 'r') as f:
                j = json.load(f)
                self.map = j['Map']
                self.hot_place = j['Hot']
                self.cool_place = j['Cool']
                self.turn = j['Turn']
        print(f'map:{self.map_name}')
        self.print_map()

    def action(self, item, place: list, enemy_place: list, pipe, cl):
        pipe.send('t')
        pipe.recv()
        pipe.send(self.output_square(True, *self.cool_place))
        next_place = place.copy()
        r = pipe.recv()
        
        # window送信 変数類
        self.window_pipe.send(cl)
        self.window_pipe.send(place)
        self.window_pipe.send(r[0])
        
        is_getted_item = False
        
        match r[0]:
            case 'w':
                next_place[0] += Game.direction[r[1]][0]
                next_place[1] += Game.direction[r[1]][1]
                pipe.send(self.output_square(True, *next_place))
                match self.in_range(*next_place):
                    case 2:
                        self.game_set(cl, 4)
                    case 3:
                        is_getted_item = True
                        item += 1
                        self.map[next_place[1]][next_place[0]] = 0
                        self.map[place[1]][place[0]] = 2
                self.window_pipe.send(next_place)
                if is_getted_item:
                    self.window_pipe.send('i')
                else:
                    self.window_pipe.send('n')

            case 'p':
                place[0] += Game.direction[r[1]][0]
                place[1] += Game.direction[r[1]][1]
                self.cool_place = next_place.copy()
                if 0 <= place[0] <= 14 and 0 <= place[1] <= 16:
                    self.map[place[1]][place[0]] = 2
                pipe.send(self.output_square(True, *next_place))
                if place == enemy_place:
                    self.game_set(cl, 1)
                elif self.enclosed(*enemy_place):
                    self.game_set(cl, 2)
                elif self.enclosed(*next_place):
                    self.game_set(cl, 3)
            case 'l':
                pipe.send(self.output_square(
                    False, place[0] + Game.direction[r[1]][0] * 2, place[1] + Game.direction[r[1]][1] * 2))
            case 's':
                pipe.send(self.output_line(
                    place[0], place[1], *Game.direction[r[1]]))
            case 'C':
                self.game_set(cl, 5)
        return item, next_place

    def game_set(self, cl: str, state: int) -> NoReturn:
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
        self.window_pipe.send('gameset')
        self.cool_disconnect()
        self.hot_disconnect()
        exit()

    def cool_connect(self):
        if self.cool_name == '':
            self.cool_pipe.send('c')
            self.cool_pipe.send(self.cool_port)
            self.cool_pipe.send(self.cool_mode)

    def hot_connect(self):
        if self.hot_name == '':
            self.hot_pipe.send('c')
            self.hot_pipe.send(self.hot_port)
            self.hot_pipe.send(self.hot_mode)
    
    def cool_disconnect(self):
        self.cool_pipe.send('d')
        self.cool_name = ''
    
    def hot_disconnect(self):
        self.hot_pipe.send('d')
        self.hot_name = ''

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
        self.flag_bot_name = False
        self.flag_ended = False

        while True:
            if self.pipe.poll():
                match self.pipe.recv():
                    case 'c':  # connect
                        self.port = pipe.recv()
                        self.mode = pipe.recv()
                        self.socket = socket.socket()
                        if self.mode == 'User':
                            self.socket.setblocking(False)
                            self.socket.bind(('', int(self.port)))
                            self.socket.listen()
                        self.flag_socket = True
                    case 'd':  # dis-connect
                        self.mode = 'User'
                        self.to_cliant_socket.close()
                        self.flag_socket = False
                        self.flag_to_cilant_socket = False
                        self.flag_bot_name = False
                        self.flag_ended = False
                    case 's':  # start
                        break

            if self.mode == 'Stay':  # Bot 作ってない
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
                try:
                    c = self.to_cliant_socket.recv(4096)
                    self.pipe.send('n')  # Name
                    self.pipe.send(c.decode('utf-8').strip())
                except BlockingIOError as e:
                    pass
                except ConnectionResetError:
                    self.pipe.send('d')
                    self.close()

        self.timeout = pipe.recv()
        if self.mode == 'Stay':
            while True:
                if pipe.recv() != 'd':
                    self.pipe.send('ok')
                    pipe.recv()
                    self.pipe.send('su')
                    self.pipe.recv()
                else:
                    exit()
        try:
            while True:
                match pipe.recv():
                    case 't':  # your turn
                        if self.flag_ended:
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
            elif time.time() - start >= self.timeout:
                self.close()
            try:
                c = self.to_cliant_socket.recv(4096)
                r = c.decode('utf-8').strip()
            except BlockingIOError:
                continue
            if r == '':
                continue
            return r

    def close(self):
        self.flag_ended = True
        self.flag_socket = False
        self.flag_to_cilant_socket = False
        self.flag_bot_name = False
        self.to_cliant_socket.shutdown(socket.SHUT_RDWR)
        self.to_cliant_socket.close()
        self.pipe.send('Cl')
        exit()
