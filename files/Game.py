import multiprocessing
import threading
import json
import time
import ReadConfig
from typing import NoReturn
import os
import socket

class Game:
    direction: dict[str, tuple[int, int]] = {
        "r": (1, 0),
        "l": (-1, 0),
        "d": (0, 1),
        "u": (0, -1),
    }

    def __init__(self, pipe) -> None:
        ReadConfig.ReadConfig().d["StagePath"]
        self.cool_items = 0
        self.hot_items = 0
        self.cool_name = ""
        self.hot_name = ""

        self.cool_port = 2009
        self.hot_port = 2010
        self.cool_mode = ""
        self.hot_mode = ""

        self.turn = 0
        self.map = []
        self.hot_place = [0, 0]
        self.cool_place = [0, 0]

        self.timeout = 0
        self.map_name = "Blank"

        for_cool_pipe, self.cool_pipe = multiprocessing.Pipe()
        for_hot_pipe, self.hot_pipe = multiprocessing.Pipe()
        self.window_pipe = pipe

        self.cool_receiver = threading.Thread(
            target=Receiver, args=(for_cool_pipe,), name="Cool"
        )
        self.cool_receiver.daemon = True
        self.hot_receiver = threading.Thread(
            target=Receiver, args=(for_hot_pipe,), name="Hot"
        )
        self.hot_receiver.daemon = True

        self.log = []

        self.cool_receiver.start()
        self.hot_receiver.start()

        while True:
            # Hot
            if self.window_pipe.poll():
                match self.window_pipe.recv():
                    case "C":
                        match self.window_pipe.recv():
                            case "connect":
                                self.cool_port = self.window_pipe.recv()
                                self.cool_mode = self.window_pipe.recv()
                                self.cool_connect()
                            case "disconnect":
                                self.cool_disconnect()
                    case "H":
                        match self.window_pipe.recv():
                            case "connect":
                                self.hot_port = self.window_pipe.recv()
                                self.hot_mode = self.window_pipe.recv()
                                self.hot_connect()
                            case "disconnect":
                                self.hot_disconnect()
                    case "start":
                        self.map_name = self.window_pipe.recv()
                        self.change_map()

                        self.timeout = self.window_pipe.recv()
                        self.speed = self.window_pipe.recv()

                        self.cool_pipe.send("s")
                        self.cool_pipe.send(self.timeout)

                        self.hot_pipe.send("s")
                        self.hot_pipe.send(self.timeout)
                        break
                    case "shutdown":
                        self.hot_disconnect()
                        self.cool_disconnect()
                        exit()

            self.accept_connection("Cool", self.cool_pipe)
            self.accept_connection("Hot", self.hot_pipe)

        for i in range(self.turn):
            self.log.append(f"Turn:{self.turn - i}")
            self.cool_items, self.cool_place = self.action(
                self.cool_items,
                self.cool_place,
                self.hot_place,
                self.cool_pipe,
                "Cool",
                i,
            )
            time.sleep(self.speed / 1000)
            self.hot_items, self.hot_place = self.action(
                self.hot_items, self.hot_place, self.cool_place, self.hot_pipe, "Hot", i
            )
            time.sleep(self.speed / 1000)

        self.game_set("", 0, self.turn - 1)

    def accept_connection(self, cl, pipe):
        if pipe.poll():
            match pipe.recv():
                case "connect":
                    self.window_pipe.send(cl)
                    self.window_pipe.send("connect")
                    self.window_pipe.send((c := pipe.recv()))
                    if cl == "Hot":
                        self.hot_name = c
                    else:
                        self.cool_name = c
                    self.window_pipe.send(pipe.recv())
                case "d":
                    self.window_pipe.send(cl)
                    self.window_pipe.send("disconnect")

    def output_square(self, is_gr, x, y) -> str:
        output = ""
        before_output = "1"
        for iy in range(-1, 2):
            for ix in range(-1, 2):
                if is_gr and ix == 0 and iy == 0:
                    if self.in_range(ix + x, iy + y) == 2:
                        before_output = "0"
                    output += "0"
                else:
                    output += str(self.in_range(ix + x, iy + y))
        return before_output + output

    def output_line(self, x, y, ix, iy):
        output = "1"
        for i in range(9):
            x += ix
            y += iy
            output += str(self.in_range(x, y))
        return output

    def in_range(self, ix, iy) -> int:
        if not (0 <= ix <= 14 and 0 <= iy <= 16):
            return 2
        elif (ix == self.cool_place[0] and iy == self.cool_place[1]) or (
            ix == self.hot_place[0] and iy == self.hot_place[1]
        ):
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

    def change_map(self):
        if self.map_name[-5:] == "Blank":
            self.map = [[0 for i in range(15)] for i in range(17)]
            self.hot_place = [8, 9]
            self.cool_place = [6, 7]
            self.turn = 100
        else:
            with open(self.map_name + ".json", "r") as f:
                j = json.load(f)
                self.map = j["Map"]
                self.hot_place = j["Hot"]
                self.cool_place = j["Cool"]
                self.turn = j["Turn"]
        self.log.append("MAP")
        l = []
        for i, y in enumerate(self.map):
            l.append([])
            for j, x in enumerate(y):
                if self.cool_place[0] == j and self.cool_place[1] == i:
                    l[-1].append("C")
                elif self.hot_place[0] == j and self.hot_place[1] == i:
                    l[-1].append("H")

                else:
                    l[-1].append(str(x))
        for i in l:
            self.log.append(" ".join(i))

    def action(self, item, place: list, enemy_place: list, pipe, cl, turn: int):
        pipe.send("t")
        if pipe.recv() != "ok":
            self.game_set(cl, 5, turn)
        pipe.send(self.output_square(True, *self.cool_place))
        next_place = place.copy()
        r = pipe.recv()
        self.log.append(f"{cl} {r}")

        self.window_pipe.send("Game")
        self.window_pipe.send(cl)
        self.window_pipe.send(place)
        self.window_pipe.send(r[0])

        is_getted_item = False

        c = ""
        match r[0]:
            case "w":
                next_place[0] += Game.direction[r[1]][0]
                next_place[1] += Game.direction[r[1]][1]
                self.window_pipe.send(next_place)
                pipe.send((c := self.output_square(True, *next_place)))
                match self.in_range(*next_place):
                    case 2:
                        self.game_set(cl, 4, turn)
                    case 3:
                        is_getted_item = True
                        item += 1
                        self.map[next_place[1]][next_place[0]] = 0
                        self.map[place[1]][place[0]] = 2
                if is_getted_item:
                    self.window_pipe.send("i")
                else:
                    self.window_pipe.send("n")

            case "p":
                place[0] += Game.direction[r[1]][0]
                place[1] += Game.direction[r[1]][1]
                self.window_pipe.send(place)
                self.cool_place = next_place.copy()
                if 0 <= place[0] <= 14 and 0 <= place[1] <= 16:
                    self.map[place[1]][place[0]] = 2
                pipe.send((c := self.output_square(True, *next_place)))
                if place == enemy_place:
                    self.game_set(cl, 1, turn)
                elif self.enclosed(*enemy_place):
                    self.game_set(cl, 2, turn)
                elif self.enclosed(*next_place):
                    self.game_set(cl, 3, turn)
            case "l":
                pipe.send(
                    (
                        c := self.output_square(
                            False,
                            place[0] + Game.direction[r[1]][0] * 2,
                            place[1] + Game.direction[r[1]][1] * 2,
                        )
                    )
                )
            case "s":
                pipe.send(
                    (c := self.output_line(place[0], place[1], *Game.direction[r[1]]))
                )
            case "C":
                self.game_set(cl, 5, turn)
        self.log.append(c)
        return item, next_place

    def game_set(self, cl: str, state: int, turn) -> NoReturn:
        """
        state
        0: 通常ゲーム終了
        1: clがput勝ち
        2: clが敵を囲んだ
        3: clが自分を囲んだ
        4: clがブロックと重なった
        5: clが通信エラー
        """
        d = {"Cool": 0, "Hot": 0}
        left_turn = self.turn - turn - 1
        match state:
            case 0:
                self.log.append("試合が通常終了しました")
            case 1:
                self.log.append(f"{cl}がput勝ちしました")
                d[cl] = 1
                d[self.inverse_client(cl)] = -1
            case 2:
                self.log.append(f"{cl}が敵を囲みました")
                d[cl] = 1
                d[self.inverse_client(cl)] = -1
            case 3:
                self.log.append(f"{cl}が自分を囲みました")
                d[cl] = -1
                d[self.inverse_client(cl)] = 1
            case 4:
                self.log.append(f"{cl}がブロックと重なりました")
                d[cl] = -1
                d[self.inverse_client(cl)] = 1
            case 5:
                self.log.append(f"{cl}が通信エラーしました")
                d[cl] = -1
                d[self.inverse_client(cl)] = 1

        self.log.append("ITEM")
        self.log.append(f"Cool: {self.cool_items}")
        self.log.append(f"Hot: {self.hot_items}")
        self.log.append("POINT")
        self.log.append(f'Cool: {self.cool_items * 3 + d["Cool"] * left_turn}')
        self.log.append(f'Hot: {self.hot_items * 3 + d["Hot"] * left_turn}')

        self.window_pipe.send("Gameset")
        self.window_pipe.send(cl)
        self.window_pipe.send(state)
        if self.window_pipe.recv() == "ok":
            path = self.window_pipe.recv()
            serial = 1
            while os.path.exists(
                f"{path}/{self.hot_name} VS {self.cool_name}({serial}).txt"
            ):
                serial += 1
            with open(
                f"{path}/{self.hot_name} VS {self.cool_name}({serial}).txt",
                mode="w",
                encoding="utf-8",
            ) as f:
                for i in self.log:
                    f.write(i + "\n")
        self.cool_disconnect()
        self.hot_disconnect()
        exit()

    def inverse_client(self, cl) -> str:
        """
        cl と 反対のクライアントを返す
        """
        if cl == "Hot":
            return "Cool"
        else:
            return "Hot"

    def cool_connect(self):
        if self.cool_name == "":
            self.cool_pipe.send("c")
            self.cool_pipe.send(self.cool_port)
            self.cool_pipe.send(self.cool_mode)

    def hot_connect(self):
        if self.hot_name == "":
            self.hot_pipe.send("c")
            self.hot_pipe.send(self.hot_port)
            self.hot_pipe.send(self.hot_mode)

    def cool_disconnect(self):
        self.cool_pipe.send("d")
        self.cool_name = ""

    def hot_disconnect(self):
        self.hot_pipe.send("d")
        self.hot_name = ""


class Receiver:
    def __init__(self, pipe) -> None:
        self.pipe = pipe
        self.port = 0
        self.timeout = 0
        self.mode = "User"
        self.socket = socket.socket()
        self.to_client_socket = socket.socket()
        self.flag_socket = False  # socket が listenかどうか
        self.flag_to_client_socket = False  # to_client_socket が つながったかどうか
        self.flag_bot_name = False
        self.flag_ended = False

        self.flag_error = False

        while True:
            if self.pipe.poll():
                match self.pipe.recv():
                    case "c":  # connect
                        self.port = pipe.recv()
                        self.mode = pipe.recv()
                        self.socket = socket.socket()
                        if self.mode != "Stay":
                            if self.mode == "Bot":
                                os.system("start Bot.py " + str(self.port))
                            self.socket.setblocking(False)
                            self.socket.bind(("", int(self.port)))
                            self.socket.listen()
                        self.flag_socket = True
                    case "d":  # dis-connect
                        self.mode = "User"
                        self.to_client_socket.close()
                        self.flag_socket = False
                        self.flag_to_client_socket = False
                        self.flag_bot_name = False
                        self.flag_ended = False
                    case "s":  # start
                        break

            if self.mode == "Stay":
                if not self.flag_bot_name:
                    self.flag_socket = False
                    pipe.send("connect")
                    pipe.send("Stay Bot")
                    pipe.send("Bot")
                    self.flag_bot_name = True

            if self.flag_socket:
                try:
                    self.to_client_socket, self.client = self.socket.accept()
                except BlockingIOError:
                    pass
                else:
                    self.flag_socket = False
                    self.flag_to_client_socket = True

            if self.flag_to_client_socket:
                try:
                    c = self.to_client_socket.recv(4096)
                    self.pipe.send("connect")
                    self.pipe.send(c.decode("utf-8").strip())
                    self.pipe.send(self.client[0])
                except BlockingIOError as e:
                    pass
                except ConnectionResetError:
                    self.pipe.send("d")
                    self.close()

        self.timeout = pipe.recv()
        if self.mode == "Stay":
            while True:
                if pipe.recv() != "d":
                    self.pipe.send("ok")
                    pipe.recv()
                    self.pipe.send("su")
                    self.pipe.recv()
                else:
                    exit()
        try:
            while True:
                if self.flag_error:
                    self.close()
                match pipe.recv():
                    case "t":  # your turn
                        self.to_client_socket.send(b"@")
                        if self.socket_receive() != "gr":
                            self.close()
                        self.pipe.send("ok")
                        self.to_client_socket.send(self.pipe.recv().encode("utf-8"))
                        self.pipe.send(self.socket_receive())
                        self.to_client_socket.send(self.pipe.recv().encode("utf-8"))
                        if self.socket_receive() != "#":
                            self.close()
                    case "d":
                        self.close()
        except EOFError:  # ゲーム終了時
            pass

    def socket_receive(self):
        start = time.time()
        r = ""
        while True:
            if self.pipe.poll() and self.pipe.recv() == "d":
                self.close()
            elif time.time() - start >= self.timeout:
                self.close()
            try:
                c = self.to_client_socket.recv(4096)
                r = c.decode("utf-8").strip()
            except BlockingIOError:
                continue
            except ConnectionAbortedError:
                self.close()
            if r == "":
                self.close()
            return r

    def close(self):
        self.flag_ended = True
        self.flag_socket = False
        self.flag_to_client_socket = False
        self.flag_bot_name = False
        self.to_client_socket.shutdown(socket.SHUT_RDWR)
        self.to_client_socket.close()
        try:
            self.pipe.send("Cl")
        except BrokenPipeError:
            pass
        exit()
