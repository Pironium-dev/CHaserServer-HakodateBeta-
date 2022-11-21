import socket
import subprocess
import threading
import time

from ReadConfig import ReadConfig


class GameRuleError(Exception):
    pass


config = ReadConfig().output_config()

def start_game():
    input('Press Enter')
    print('FIGHT')


class Game:
    def __init__(self) -> None:
        self.map = [[0 for i in range(15)] for i in range(17)]
        '''
        Cool: 0
        Hot: 1
        '''
        self.posx = [0, 10]
        self.posy = [0, 10]

    def cliant_act(self, context: str, identifier: int) -> str:
        x, y = 0, 0
        match context[1]:
            case 'u':
                y -= 1
            case 'd':
                y += 1
            case 'l':
                x -= 1
            case 'r':
                x += 1
        match context[0]:
            case 'g':
                return self.__output_square(self.posx[identifier], self.posy[identifier], is_gr=True)
            case 'w':
                self.posy[identifier] += y
                self.posx[identifier] += x
                return self.__output_square(self.posx[identifier], self.posy[identifier], is_gr=True)
            case 'p':
                x *= 2
                y *= 2
                self.map[self.posy[identifier] + y][self.posx[identifier] + x] = 2
                return self.__output_square(self.posx[identifier], self.posy[identifier], is_gr=True)
            case 's':
                return self.__output_line(self.posx[identifier], self.posy[identifier], x, y)
            case _:  # look
                return self.__output_square(self.posx[identifier] + x * 2, self.posy[identifier] + y * 2)

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
        lock.acquire()
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
        time.sleep(config['GameSpeed']/1000)
        lock.release()

def Receiver(pnumber, identifier, bot_type):
    """クライアントからの通信を受け取る

    Args:
        pnumber (int): ポート番号
        identifier (int): 識別用
        0がcool, 1がhot

    """
    global cool_event, hot_event, barrier, is_started
    loc = local()
    mode = 0
    name = ''
    
    def receive(lo):
        s = ''
        while '\r\n' not in s:
            s += tocliant_socket.recv(2048).decode('utf-8')
        lo.output += s[:-2]
    
    if bot_type == 'Bot':
        subprocess.Popen(['start', 'Hot.bat'], shell=True)
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', pnumber))
    tocliant_socket = socket.socket()

    try:
        match bot_type:
            case 'Off' | 'Bot':
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind(('', pnumber))
                server_socket.listen()
                (tocliant_socket, address) = server_socket.accept()
                while True:
                    if mode != 1:
                        loc.output = ''
                        thread = threading.Thread(target=receive, args=(loc,))
                        thread.start()
                        if mode == 0:
                            thread.join()
                        else:
                            thread.join(timeout=config['TimeOut'] / 1000)
                        if not loc.output:
                            raise GameRuleError('タイムアウトしました')
                    '''
                        mode 0:nameの取得
                        mode 1:@送信待ち
                        mode 2:grの取得
                        mode 3:動作の取得
                        mode 4:#の取得
                    '''
                    match mode:
                        case 0:
                            name = loc.output
                            print(f'{name} から接続されました')
                            barrier.wait()
                            mode += 1
                        case 1:
                            if identifier == 0:
                                if is_started:
                                    is_started = False
                                else:
                                    cool_event.clear()
                                cool_event.wait()
                            else:
                                hot_event.clear()
                                hot_event.wait()
                            tocliant_socket.sendall(b'@')
                            mode += 1
                        case 2:
                            if loc.output == 'gr':
                                tocliant_socket.sendall((s := game.cliant_act('gr', identifier)).encode('utf-8'))
                                if s[0] == '0':
                                    raise GameRuleError('ブロックに重なりました')
                                mode += 1
                            else:
                                raise GameRuleError('get_readyをしませんでした')
                        case 3:
                            if (c := loc.output) != 'gr':
                                tocliant_socket.sendall((s := game.cliant_act(c, identifier)).encode('utf-8'))
                                if s[0] == '0':
                                    raise GameRuleError('ブロックに重なりました')
                                game.print_map()
                            else:
                                raise GameRuleError('get_readyを二回連続でしました')
                            mode += 1
                        case 4:
                            if loc.output == '#':
                                if identifier == 0:
                                    hot_event.set()
                                else:
                                    cool_event.set()
                                mode = 1
                            else:
                                raise GameRuleError('行動を二回連続でしました')
            case 'Stay':
                barrier.wait()
                while True:
                    hot_event.clear()
                    hot_event.wait()
                    game.cliant_act('gr', identifier)
                    game.cliant_act('lu', identifier)
                    cool_event.set()
    except OSError:
        server_socket.close()
        tocliant_socket.close()
    except GameRuleError as e:
        print(e)
        exit(0)


class local:
    def __init__(self) -> None:
        self.output = ''


if __name__ == '__main__':
    game = Game()
    is_started = True
    barrier = threading.Barrier(2, action=start_game)

    lock = threading.Lock()

    cool_event = threading.Event()
    hot_event = threading.Event()
    cool_server = threading.Thread(target=Receiver, args=(config['CoolPort'], 0, 'Off'))
    hot_server = threading.Thread(target=Receiver, args=(config['HotPort'], 1, config['AntiBotMode']))

    cool_server.start()
    hot_server.start()
    cool_event.set()
    while True:
        time.sleep(1)
