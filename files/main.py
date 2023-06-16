import tkinter as tk
import tkinter.ttk as ttk
import multiprocessing
import threading
import tkinter.font as tk_f
import socket
import random
import time
from tkinter import filedialog
import os
import json

import ReadConfig
import Game


class Game_Window(tk.Frame):
    def __init__(self, master: tk.Tk):
        self.game_pipe, self.pipe = multiprocessing.Pipe()
        self.condition = threading.Condition()

        self.game = multiprocessing.Process(
            target=Game.Game, name="Server", args=(self.game_pipe,), daemon=True
        )
        self.game.start()

        self.is_game_started = False

        tk.Frame.__init__(self, master=master)
        master.title("CHaser")
        master.protocol("WM_DELETE_WINDOW", self.save_config)

        self.points = {"Cool": 0, "Hot": 0}
        self.labels = {}  # ゲームのポイントのラベルをまとめたもの
        self.names = {"Cool": "", "Hot": ""}

        # big_flame
        self.big_flame_menu = ttk.Frame()

        self.menu_screen()

        self.write_menu_map(None)

        self.big_flame_menu.grid(row=0, column=0, sticky=tk.NSEW)

        self.cool_state = 0
        self.hot_state = 0
        """
        0: 待機開始
        1: 待機中
        2: 接続中
        """

        self.has_game_started = False
        self.receive = threading.Thread(target=self.pipe_receive)
        self.receive.daemon = True
        self.receive.start()
        self.big_flame_menu.tkraise()

    def shutdown(self):
        self.pipe.send("shutdown")

    def game_screen(self):
        # window
        self.game_window = tk.Toplevel()
        self.game_window.title("game")
        self.game_window.protocol("WM_DELETE_WINDOW", self.start_game)

        self.big_flame_game = ttk.Frame(self.game_window)

        # frame
        self.game_frame_status = ttk.Frame(self.big_flame_game)
        self.game_frame_cool = ttk.Labelframe(self.big_flame_game, text="Cool")
        self.game_frame_hot = ttk.Labelframe(self.big_flame_game, text="Hot")

        # picture
        self.wall_image = tk.PhotoImage(file="./resources/wall.png")
        self.item_image = tk.PhotoImage(file="./resources/item.png")
        self.hot_image = tk.PhotoImage(file="./resources/Hot.png")
        self.cool_image = tk.PhotoImage(file="./resources/Cool.png")
        self.sight_image = tk.PhotoImage(file="./resources/Sight.png")

        # canvas

        self.game_canvas = tk.Canvas(
            self.big_flame_game, width=378, height=428, bg="white", borderwidth=0
        )
        self.game_canvas.create_line(0, 2, 378, 2)
        self.game_canvas.create_line(0, 428, 379, 428)
        self.game_canvas.create_line(378, 2, 378, 428)
        self.game_canvas.create_line(2, 2, 2, 428)
        for i in range(1, 17):
            self.game_canvas.create_line(0, 2 + i * 25, 378, 2 + i * 25, dash=(1, 1))
        for i in range(1, 15):
            self.game_canvas.create_line(2 + i * 25, 0, 2 + i * 25, 428, dash=(1, 1))

        # separator
        ttk.Style().configure("black.TSeparator", background="black")
        self.game_separator = ttk.Separator(
            self.big_flame_game, orient="vertical", style="black.TSeparator"
        )

        # font
        self.font_normal = tk_f.Font(family="MSゴシック", size=25)

        # status
        self.var_turn = tk.StringVar()
        self.var_winner = tk.StringVar()
        self.var_reason = tk.StringVar()
        self.var_prog_turn = tk.IntVar()

        self.var_prog_turn.set(0)
        self.var_turn.set("Turn:100")
        self.var_winner.set("")
        self.var_reason.set("")

        self.label_turn = ttk.Label(
            self.game_frame_status, textvariable=self.var_turn, font=self.font_normal
        )
        self.progressbar = ttk.Progressbar(
            self.game_frame_status, length=220, variable=self.var_prog_turn
        )
        self.label_winner = ttk.Label(
            self.game_frame_status,
            textvariable=self.var_winner,
            font=(("MSゴシック", "30")),
        )
        self.label_reason = ttk.Label(
            self.game_frame_status,
            textvariable=self.var_reason,
            font=(("MSゴシック", "20")),
        )

        self.label_turn.pack()
        self.progressbar.pack()
        self.label_winner.pack()
        self.label_reason.pack()

        # Cool

        self.labels["Cool"] = tk.StringVar()
        self.labels["Cool"].set("Item:0(Score:0)")

        self.label_cool_name = ttk.Label(
            self.game_frame_cool, text="自動君", font=self.font_normal
        )
        self.label_cool_score = ttk.Label(
            self.game_frame_cool,
            textvariable=self.labels["Cool"],
            font=self.font_normal,
        )

        self.label_cool_name.pack()
        self.label_cool_score.pack()

        # Hot

        self.labels["Hot"] = tk.StringVar()
        self.labels["Hot"].set("Item:0(Score:0)")

        self.label_hot_name = ttk.Label(
            self.game_frame_hot, text="自動君", font=self.font_normal
        )
        self.label_hot_score = ttk.Label(
            self.game_frame_hot, textvariable=self.labels["Hot"], font=self.font_normal
        )

        self.label_hot_name.pack()
        self.label_hot_score.pack()

        self.game_canvas.grid(column=0, row=0, padx=6, rowspan=3)
        self.game_separator.grid(column=1, row=0, sticky="ns", rowspan=3, padx=6)
        self.game_frame_status.grid(column=2, row=0, padx=6)
        self.game_frame_cool.grid(column=2, row=1, padx=6)
        self.game_frame_hot.grid(column=2, row=2, padx=6)

        self.big_flame_game.pack()

    def menu_screen(self):
        # tk_setting
        self.font = ("", 10)
        self.big_flame_menu.columnconfigure(0, weight=1)
        self.big_flame_menu.columnconfigure(1, weight=1)

        # ver
        self.menu_settings_ver_log = tk.BooleanVar()
        self.menu_settings_ver_log.set(config.d["Log"])

        self.menu_settings_ver_score = tk.BooleanVar()
        self.menu_settings_ver_score.set(config.d["Score"])

        self.menu_settings_timeout_ver = tk.Variable()
        self.menu_settings_timeout_ver.set(config.d["TimeOut"])

        self.menu_settings_speed_ver = tk.Variable()
        self.menu_settings_speed_ver.set(config.d["GameSpeed"])

        self.menu_map_ver = tk.StringVar()
        self.menu_map_ver.set(config.d["NextMap"])

        # Cool
        (
            self.menu_frame_cool,
            self.menu_label_ver_cool,
            self.menu_port_ver_cool,
            self.menu_mode_ver_cool,
            self.menu_button_cool,
            self.menu_cool_spinbox,
            self.menu_cool_combobox,
        ) = self.clients_menu("COOL")
        self.menu_button_cool["command"] = self.cool_wait
        self.menu_cool_combobox.bind("<<ComboboxSelected>>", self.cool_stay)
        self.menu_port_ver_cool.set(config.d["CoolPort"])
        self.menu_mode_ver_cool.set(config.d["CoolMode"])

        # Hot
        (
            self.menu_frame_hot,
            self.menu_label_ver_hot,
            self.menu_port_ver_hot,
            self.menu_mode_ver_hot,
            self.menu_button_hot,
            self.menu_hot_spinbox,
            self.menu_hot_combobox,
        ) = self.clients_menu("HOT")
        self.menu_button_hot["command"] = self.hot_wait
        self.menu_hot_combobox.bind("<<ComboboxSelected>>", self.hot_stay)
        self.menu_port_ver_hot.set(config.d["HotPort"])
        self.menu_mode_ver_hot.set(config.d["HotMode"])

        # picture
        self.swall_image = tk.PhotoImage(file="./resources/Swall.png")
        self.sitem_image = tk.PhotoImage(file="./resources/Sitem.png")
        self.shot_image = tk.PhotoImage(file="./resources/SHot.png")
        self.scool_image = tk.PhotoImage(file="./resources/SCool.png")

        # map_view
        size = 18
        self.menu_canvas = tk.Canvas(
            self.big_flame_menu, width=15 * size, height=17 * size, background="white"
        )

        self.menu_canvas.grid(row=1, column=0, padx=10)

        # map_select
        self.menu_frame_map_select = ttk.Frame(self.big_flame_menu)

        self.menu_combobox = ttk.Combobox(
            self.menu_frame_map_select, textvariable=self.menu_map_ver, state="readonly"
        )
        self.menu_combobox.bind("<<ComboboxSelected>>", self.write_menu_map)
        self.menu_map_randomize = ttk.Button(
            self.menu_frame_map_select, text="ランダム", command=self.map_randomize
        )
        self.menu_combobox.grid(row=0, column=0, pady=5)
        self.menu_map_randomize.grid(row=0, column=1)

        self.list_up_maps()

        # server_address
        self.menu_server_address = ttk.Label(
            self.big_flame_menu,
            text=socket.gethostbyname(socket.gethostname()),
            font=self.font,
        )

        self.menu_server_address.grid(row=4, column=0)

        # settings
        """
        スコア
        ログ保存するか
        ゲーム進行速度
        タイムアウト
        ログ保存場所
        マップ保存場所
        設定リセット
        """
        self.menu_frame_settings = ttk.Labelframe(self.big_flame_menu, text="設定")

        self.menu_settings_box_log = ttk.Checkbutton(
            self.menu_frame_settings, text="ログ保存", variable=self.menu_settings_ver_log
        )

        self.menu_settings_box_score = ttk.Checkbutton(
            self.menu_frame_settings, text="スコア", variable=self.menu_settings_ver_score
        )

        self.menu_settings_label_timeout = ttk.Label(
            self.menu_frame_settings, text="タイムアウト(ms)", font=self.font
        )
        self.menu_settings_spinbox_timeout = ttk.Spinbox(
            self.menu_frame_settings, textvariable=self.menu_settings_timeout_ver
        )
        self.menu_settings_label_speed = ttk.Label(
            self.menu_frame_settings, text="進行速度(ms)", font=self.font
        )
        self.menu_settings_spinbox_speed = ttk.Spinbox(
            self.menu_frame_settings, textvariable=self.menu_settings_speed_ver
        )
        self.menu_settings_spinbox_timeout["from"] = 0
        self.menu_settings_spinbox_timeout["to"] = 10000
        self.menu_settings_spinbox_timeout["increment"] = 10
        self.menu_settings_spinbox_speed["from"] = 0
        self.menu_settings_spinbox_speed["to"] = 10000
        self.menu_settings_spinbox_speed["increment"] = 10

        self.menu_settings_button_log = ttk.Button(
            self.menu_frame_settings, text="ログ保存場所", command=self.change_log
        )
        self.menu_settings_button_log.grid(row=3, column=0)

        self.menu_settings_button_map = ttk.Button(
            self.menu_frame_settings, text="マップ保存場所", command=self.change_map
        )
        self.menu_settings_button_map.grid(row=3, column=1)

        self.menu_settings_button_reset = ttk.Button(
            self.menu_frame_settings, text="設定のリセット", command=self.reset_config
        )
        self.menu_settings_button_reset.grid(row=4, column=0, columnspan=2)

        self.menu_settings_box_log.grid(row=0, column=0)
        self.menu_settings_box_score.grid(row=0, column=1)
        self.menu_settings_label_timeout.grid(row=1, column=0)
        self.menu_settings_spinbox_timeout.grid(row=2, column=0)
        self.menu_settings_label_speed.grid(row=1, column=1)
        self.menu_settings_spinbox_speed.grid(row=2, column=1)

        # game_start
        self.menu_game_start = ttk.Button(
            self.big_flame_menu, text="ゲーム開始", command=self.start_game
        )

        self.menu_game_start.grid(row=2, column=1, sticky=tk.W + tk.E)

        # Frame_grid
        self.menu_frame_cool.grid(row=0, column=0, sticky=tk.W + tk.E, pady=6, padx=5)
        self.menu_frame_hot.grid(row=0, column=1, sticky=tk.W + tk.E)
        self.menu_frame_map_select.grid(row=2, column=0)
        self.menu_frame_settings.grid(row=1, column=1)

    def clients_menu(self, name):
        label_ver = tk.StringVar(value="名前:\nIP:")
        frame = ttk.Labelframe(self.big_flame_menu, text=name)
        frame.columnconfigure(2, weight=1)
        label = ttk.Label(
            frame, textvariable=label_ver, justify="left", anchor=tk.NW, font=self.font
        )
        spinbox_ver = tk.Variable()
        spinbox = ttk.Spinbox(frame, textvariable=spinbox_ver, width=7)
        spinbox["from"] = 1024
        spinbox["to"] = 5000
        combobox_ver = tk.StringVar()
        combobox = ttk.Combobox(
            frame,
            state="readonly",
            textvariable=combobox_ver,
            values=["User", "Stay", "Bot"],
            width=6,
        )
        button = ttk.Button(frame, text="待機開始")
        label.grid(row=0, column=0, sticky=tk.W, columnspan=2)
        spinbox.grid(row=1, column=0)
        combobox.grid(row=1, column=1)
        button.grid(row=1, column=2, sticky=tk.E + tk.W)

        return frame, label_ver, spinbox_ver, combobox_ver, button, spinbox, combobox

    def map_randomize(self):
        self.list_up_maps()
        if len(self.menu_combobox["values"]) != 1:
            while self.menu_map_ver.get() == (
                c := random.choice(self.menu_combobox["values"])
            ):
                pass
            self.menu_map_ver.set(c)
        self.write_menu_map()

    def save_config(self, flag=True):
        # flag が True なら終了
        config.d["CoolPort"] = int(self.menu_port_ver_cool.get())
        config.d["HotPort"] = int(self.menu_port_ver_hot.get())
        config.d["GameSpeed"] = int(self.menu_settings_speed_ver.get())
        config.d["TimeOut"] = int(self.menu_settings_timeout_ver.get())
        config.d["HotMode"] = self.menu_hot_combobox.get()
        config.d["CoolMode"] = self.menu_cool_combobox.get()
        config.d["NextMap"] = self.menu_map_ver.get()
        config.d["Log"] = self.menu_settings_ver_log.get()
        config.d["Score"] = self.menu_settings_ver_score.get()
        config.save()
        if flag:
            self.master.destroy()

    def reset_config(self):
        config.reset()
        self.hot_disconnect()
        self.cool_disconnect()
        self.menu_port_ver_cool.set(config.d["CoolPort"])
        self.menu_port_ver_hot.set(config.d["HotPort"])
        self.menu_settings_speed_ver.set(config.d["GameSpeed"])
        self.menu_settings_timeout_ver.set(config.d["TimeOut"])
        self.menu_hot_combobox.set(config.d["HotMode"])
        self.menu_cool_combobox.set(config.d["CoolMode"])
        self.menu_map_ver.set(config.d["NextMap"])
        self.menu_settings_ver_log.set(config.d["Log"])
        self.menu_settings_ver_score.set(config.d["Score"])

        self.write_menu_map(None)

    def change_log(self):
        if (c := filedialog.askdirectory(initialdir=__file__)) != "":
            config.d["LogPath"] = c

    def change_map(self):
        if (c := filedialog.askdirectory(initialdir=__file__)) != "":
            config.d["StagePath"] = c
            self.list_up_maps()

    def list_up_maps(self):
        l = []
        for i in os.listdir(config.d["StagePath"]):
            if i[-4:] == "json":
                l.append(os.path.basename(i)[:-5])
        l.append("Blank")
        self.menu_combobox["values"] = l

    def cool_stay(self, _=None):
        if self.menu_mode_ver_cool.get() != "User" and self.cool_state == 0:
            self.cool_wait()

    def hot_stay(self, _=None):
        if self.menu_mode_ver_hot.get() != "User" and self.hot_state == 0:
            self.hot_wait()

    def cool_wait(self):
        self.pipe.send("C")
        if self.cool_state == 0:
            self.pipe.send("connect")
            self.pipe.send(self.menu_port_ver_cool.get())
            self.pipe.send(self.menu_mode_ver_cool.get())
            self.cool_state = 1
            self.menu_button_cool["text"] = "接続待ち"
            self.menu_cool_combobox["state"] = "disable"
            self.menu_cool_spinbox["state"] = "disable"
        else:
            self.cool_disconnect()

    def hot_wait(self):
        self.pipe.send("H")
        if self.hot_state == 0:
            self.pipe.send("connect")
            self.pipe.send(self.menu_port_ver_hot.get())
            self.pipe.send(self.menu_mode_ver_hot.get())
            self.hot_state = 1
            self.menu_button_hot["text"] = "接続待ち"
            self.menu_hot_combobox["state"] = "disable"
            self.menu_hot_spinbox["state"] = "disable"
        else:
            self.hot_disconnect()

    def cool_disconnect(self):
        self.pipe.send("disconnect")
        self.cool_state = 0
        self.menu_button_cool["text"] = "待機開始"
        self.menu_cool_combobox["state"] = "readonly"
        self.menu_cool_spinbox["state"] = "normal"
        self.menu_label_ver_cool.set("名前:\nIP:")

    def hot_disconnect(self):
        self.pipe.send("disconnect")
        self.hot_state = 0
        self.menu_button_hot["text"] = "待機開始"
        self.menu_hot_combobox["state"] = "readonly"
        self.menu_hot_spinbox["state"] = "normal"
        self.menu_label_ver_hot.set("名前:\nIP:")

    def start_game(self):
        # ゲームの停止も担当する
        if self.cool_state == self.hot_state == 2:
            if not self.is_game_started:
                self.menu_game_start["text"] = "ゲーム停止"

                self.menu_button_cool["state"] = "disable"  # to do
                self.menu_button_hot["state"] = "disable"
                self.menu_settings_spinbox_speed["state"] = "disable"

                self.is_game_started = True
                self.game_screen()
                self.save_config(False)
                self.has_game_started = True

                self.label_cool_name["text"] = self.names["Cool"]
                self.label_hot_name["text"] = self.names["Hot"]

                self.pipe.send("start")
                self.pipe.send(config.d["StagePath"] + r"/" + self.menu_map_ver.get())
                self.pipe.send(int(self.menu_settings_timeout_ver.get()))
                self.pipe.send(int(self.menu_settings_speed_ver.get()))
                self.write_map()
                self.progressbar["maximum"] = self.whole_turn
            else:
                self.menu_game_start["text"] = "ゲーム開始"
                self.menu_game_start["state"] = "disable"

                self.menu_button_cool["state"] = "normal"
                self.menu_button_hot["state"] = "normal"
                self.menu_settings_spinbox_speed["state"] = "normal"

                self.is_game_started = False
                if self.game.is_alive():
                    self.game.terminate()
                self.game = multiprocessing.Process(
                    target=Game.Game, name="Server", args=(self.game_pipe,), daemon=True
                )
                self.game.start()
                self.cool_disconnect()
                self.hot_disconnect()

                self.game_window.destroy()

    def pipe_receive(self):
        while True:
            if self.cool_state == self.hot_state == 2:
                self.menu_game_start["state"] = "normal"
            else:
                self.menu_game_start["state"] = "disable"

            with self.condition:
                try:
                    match self.pipe.recv():
                        case "Cool":
                            if self.pipe.recv() == "connect":
                                self.cool_state = 2
                                self.menu_button_cool["text"] = "切断"
                                self.menu_label_ver_cool.set(
                                    f"名前:{(c := self.pipe.recv())}\nIP:{self.pipe.recv()}"
                                )
                                self.names["Cool"] = c
                            else:
                                self.cool_state = 0
                                self.menu_button_cool["text"] = "待機開始"
                                self.menu_cool_combobox["state"] = "readonly"
                                self.menu_cool_spinbox["state"] = "normal"
                                self.menu_label_ver_cool.set("名前:\nIP:")
                        case "Hot":
                            if self.pipe.recv() == "connect":
                                self.hot_state = 2
                                self.menu_button_hot["text"] = "切断"
                                self.menu_label_ver_hot.set(
                                    f"名前:{(c := self.pipe.recv())}\nIP:{self.pipe.recv()}"
                                )
                                self.names["Hot"] = c
                            else:
                                self.hot_state = 0
                                self.menu_button_hot["text"] = "待機開始"
                                self.menu_hot_combobox["state"] = "readonly"
                                self.menu_hot_spinbox["state"] = "normal"
                                self.menu_label_ver_hot.set("名前:\nIP:")
                        case "Game":
                            # アニメーション入れる
                            cl = self.pipe.recv()
                            if cl != "gameset":
                                nowpos = self.pipe.recv()

                                first = self.list_up_look(*nowpos)
                                second = []

                                match self.pipe.recv():
                                    case "w":
                                        i, j = self.pipe.recv()
                                        self.game_canvas.moveto(
                                            cl, i * 25 + 3, j * 25 + 3
                                        )
                                        if (c := self.pipe.recv()) == "i":
                                            self.game_canvas.create_image(
                                                15 + nowpos[0] * 25,
                                                15 + nowpos[1] * 25,
                                                image=self.wall_image,
                                            )
                                            self.game_canvas.delete(
                                                self.game_screen_id[j][i]
                                            )
                                            self.points[cl] += 1
                                        elif c == "Gameset":
                                            self.game_set()
                                    case "p":
                                        i, j = self.pipe.recv()
                                        self.game_canvas.create_image(
                                            15 + i * 25,
                                            15 + j * 25,
                                            image=self.wall_image,
                                        )
                                    case "l":
                                        second = self.list_up_look(*self.pipe.recv())
                                    case "s":
                                        second = self.list_up_search(
                                            *self.pipe.recv(), *self.pipe.recv()
                                        )

                                if cl == "Hot":
                                    self.var_prog_turn.set(self.var_prog_turn.get() + 1)
                                    self.var_turn.set(
                                        f"Turn:{self.whole_turn - self.var_prog_turn.get()}"
                                    )
                                    self.point_set(
                                        self.whole_turn - self.var_prog_turn.get()
                                    )

                                self.handle_sight(first, second)

                            else:
                                self.game_set()

                        case "Gameset":
                            self.game_set()
                except EOFError:
                    exit()

    def inverse_client(self, cl) -> str:
        """
        cl と 反対のクライアントを返す
        """
        if cl == "Hot":
            return "Cool"
        else:
            return "Hot"

    def write_map(self):
        game_map = []
        hot = []
        cool = []

        self.game_screen_id = [[-1 for i in range(15)] for i in range(17)]

        game_map, hot, cool = self.read_map()
        for i, x in enumerate(game_map):
            for j, y in enumerate(x):
                if hot == [j, i]:
                    self.game_canvas.create_image(
                        15 + j * 25, 15 + i * 25, image=self.hot_image, tag="Hot"
                    )
                if cool == [j, i]:
                    self.game_canvas.create_image(
                        15 + j * 25, 15 + i * 25, image=self.cool_image, tag="Cool"
                    )
                match y:
                    case 2:
                        self.game_canvas.create_image(
                            15 + j * 25, 15 + i * 25, image=self.wall_image
                        )
                    case 3:
                        self.game_screen_id[i][j] = self.game_canvas.create_image(
                            15 + j * 25, 15 + i * 25, image=self.item_image
                        )

    def write_menu_map(self, _=None):
        game_map, hot, cool = self.read_map()
        padding = 10
        size = 18
        self.menu_canvas.delete("a")
        for i, x in enumerate(game_map):
            for j, y in enumerate(x):
                if hot == [j, i]:
                    self.menu_canvas.create_image(
                        padding + j * size,
                        padding + i * size,
                        image=self.shot_image,
                        tag="a",
                    )
                if cool == [j, i]:
                    self.menu_canvas.create_image(
                        padding + j * size,
                        padding + i * size,
                        image=self.scool_image,
                        tag="a",
                    )
                match y:
                    case 2:
                        self.menu_canvas.create_image(
                            padding + j * size,
                            padding + i * size,
                            image=self.swall_image,
                            tag="a",
                        )
                    case 3:
                        self.menu_canvas.create_image(
                            padding + j * size,
                            padding + i * size,
                            image=self.sitem_image,
                            tag="a",
                        )

    def read_map(self):
        try:
            with open(
                config.d["StagePath"] + r"/" + self.menu_map_ver.get() + ".json", "r"
            ) as f:
                j = json.load(f)
                game_map = j["Map"]
                hot = j["Hot"]
                cool = j["Cool"]
                self.whole_turn = j["Turn"]
        except FileNotFoundError:
            game_map = [[0 for i in range(15)] for i in range(17)]
            hot = [8, 9]
            cool = [6, 7]
            self.whole_turn = 100
            self.menu_map_ver.set("Blank")
        return game_map, hot, cool

    def game_set(self):
        cl = self.pipe.recv()
        self.var_turn.set(f"Turn:{self.whole_turn - self.var_prog_turn.get()}")
        turn = self.whole_turn - self.var_prog_turn.get() - 1
        match self.pipe.recv():  # Game.game_setを参照してください
            case 0:
                if self.points["Cool"] == self.points["Hot"]:
                    self.var_winner.set("DRAW")
                elif self.points["Cool"] > self.points["Hot"]:
                    self.var_winner.set("Cool WIN")
                else:
                    self.var_winner.set("Hot WIN")
            case 1:
                self.var_winner.set(f"{cl} WIN")
                self.point_set(turn, cl)
                self.var_reason.set("put勝ち")
            case 2:
                self.var_winner.set(f"{cl} WIN")
                self.point_set(turn, cl)
                self.var_reason.set("put勝ち(囲み)")
            case 3:
                self.var_winner.set(f"{cl} LOSE")
                self.point_set(turn, self.inverse_client(cl))
                self.var_reason.set("自滅負け(囲み)")
            case 4:
                self.var_winner.set(f"{cl} LOSE")
                self.point_set(turn, self.inverse_client(cl))
                self.var_reason.set("自滅負け")
            case 5:
                self.var_winner.set(f"{cl} LOSE")
                self.point_set(turn, self.inverse_client(cl))
                self.var_reason.set("通信エラー")
        if self.menu_settings_ver_log.get():
            self.pipe.send("ok")
            self.pipe.send(config.d["LogPath"])
        else:
            self.pipe.send("no")

    def point_set(self, turn, cl=None):
        if self.menu_settings_ver_score.get():
            if cl is not None:
                self.labels[cl].set(
                    f"Item:{self.points[cl]}(Score:{self.points[cl] * 3 + turn})"
                )
                cl = self.inverse_client(cl)
                self.labels[cl].set(
                    f"Item:{self.points[cl]}(Score:{self.points[cl] * 3 - turn})"
                )
            else:
                c = "Cool"
                h = "Hot"
                self.labels[c].set(
                    f"Item:{self.points[c]}(Score:{self.points[c] * 3 + turn})"
                )
                self.labels[h].set(
                    f"Item:{self.points[h]}(Score:{self.points[h] * 3 + turn})"
                )
        else:
            if cl is not None:
                self.labels[cl].set(f"Item:{self.points[cl]}")
                cl = self.inverse_client(cl)
                self.labels[cl].set(f"Item:{self.points[cl]}")
            else:
                c = "Cool"
                h = "Hot"
                self.labels[c].set(f"Item:{self.points[c]}")
                self.labels[h].set(f"Item:{self.points[h]}")

    def handle_sight(self, first, second):
        self.write_sight(0, first)
        t1 = threading.Thread(
            target=self.write_sight,
            args=(int(self.menu_settings_speed_ver.get()) // 2, second),
        )

        t1.start()
        """
        self.write_sight(first)
        self.after(self.menu_settings_speed_ver.get())
        # self.write_sight(second)
        """

    def write_sight(self, t, li: list[tuple[int, int]]):
        time.sleep(t / 1000)
        try:
            self.game_canvas.delete("sight")
            for i in li:
                self.game_canvas.create_image(
                    15 + i[0] * 25, 15 + i[1] * 25, image=self.sight_image, tag="sight"
                )
        except tk.TclError as e:
            print(e)

    def delete_sight(self):
        self.game_canvas.delete("sight")

    def list_up_look(self, x, y):
        li = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                li.append((x + i, y + j))
        return li

    def list_up_search(self, x, y, dx, dy):
        li = []
        for i in range(9):
            x += dx
            y += dy
            li.append((x, y))
        return li


if __name__ == "__main__":
    config = ReadConfig.ReadConfig()

    root = tk.Tk()
    root.geometry("680x450")
    root.resizable(False, False)
    game_window = Game_Window(root)

    game_window.mainloop()
