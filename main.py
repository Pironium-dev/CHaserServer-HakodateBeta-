import json
import multiprocessing
import os
import random
import socket
import threading
import time
import tkinter as tk
import tkinter.font as tk_f
import tkinter.ttk as ttk
from tkinter import filedialog
from typing import Dict, NoReturn

from PIL import ImageTk

'''
Bot
通信書き換え
スコア表示
ファイル場所
マップ場所
設定保存
ログ保存
メニューのマップ表示
'''


class Game_Window(tk.Frame):
    def __init__(self, master: tk.Tk):
        self.game_pipe, self.pipe = multiprocessing.Pipe()
        self.condition = threading.Condition()
        
        self.game = multiprocessing.Process(
            target=Game, name='Server', args=(self.game_pipe,), daemon=True)
        self.game.start()
        
        self.is_game_started = False
        
        
        tk.Frame.__init__(self, master=master)
        master.title('CHaser')
        master.protocol('WM_DELETE_WINDOW', self.save_config)

        self.points = {'Cool': 0, 'Hot': 0}
        self.labels = {}  # ゲームのポイントのラベルをまとめたもの
        self.names = {'Cool': '', 'Hot': ''}

        # big_flame
        self.big_flame_menu = ttk.Frame()

        self.menu_screen()

        self.write_menu_map(None)

        self.big_flame_menu.grid(row=0, column=0, sticky=tk.NSEW)

        self.cool_state = 0
        self.hot_state = 0
        '''
        0: 待機開始
        1: 待機中
        2: 接続中
        '''

        self.has_game_started = False
        self.receive = threading.Thread(target=self.pipe_receive)
        self.receive.daemon = True
        self.receive.start()
        self.big_flame_menu.tkraise()

    def shutdown(self):
        self.pipe.send('shutdown')

    def game_screen(self):
        # window
        self.game_window = tk.Toplevel()
        self.game_window.title('game')
        self.game_window.protocol('WM_DELETE_WINDOW', self.start_game)
    
        self.big_flame_game = ttk.Frame(self.game_window)

        # frame
        self.game_frame_status = ttk.Frame(self.big_flame_game)
        self.game_frame_cool = ttk.Labelframe(self.big_flame_game, text='Cool')
        self.game_frame_hot = ttk.Labelframe(self.big_flame_game, text='Hot')

        # picture
        self.wall_image = ImageTk.PhotoImage(file='./画像/wall.png')
        self.item_image = ImageTk.PhotoImage(file='./画像/item.png')
        self.hot_image = ImageTk.PhotoImage(file='./画像/Hot.png')
        self.cool_image = ImageTk.PhotoImage(file='./画像/Cool.png')

        # canvas

        self.game_canvas = tk.Canvas(
            self.big_flame_game, width=378, height=428, bg='white', borderwidth=0)
        self.game_canvas.create_line(0, 2, 378, 2)
        self.game_canvas.create_line(0, 428, 379, 428)
        self.game_canvas.create_line(378, 2, 378, 428)
        self.game_canvas.create_line(2, 2, 2, 428)
        for i in range(1, 17):
            self.game_canvas.create_line(
                0, 2 + i * 25, 378, 2 + i * 25, dash=(1, 1))
        for i in range(1, 15):
            self.game_canvas.create_line(
                2 + i * 25, 0, 2 + i * 25, 428, dash=(1, 1))

        # separator
        ttk.Style().configure('black.TSeparator', background='black')
        self.game_separator = ttk.Separator(
            self.big_flame_game, orient='vertical', style='black.TSeparator')

        # font
        self.font_normal = tk_f.Font(family='MSゴシック', size=25)

        # status
        self.var_turn = tk.StringVar()
        self.var_winner = tk.StringVar()
        self.var_reason = tk.StringVar()
        self.var_prog_turn = tk.IntVar()

        self.var_prog_turn.set(0)
        self.var_turn.set('Turn:100')
        self.var_winner.set('')
        self.var_reason.set('')

        self.label_turn = ttk.Label(
            self.game_frame_status, textvariable=self.var_turn, font=self.font_normal)
        self.progressbar = ttk.Progressbar(
            self.game_frame_status, length=220, variable=self.var_prog_turn)
        self.label_winner = ttk.Label(
            self.game_frame_status, textvariable=self.var_winner, font=(('MSゴシック', '30')))
        self.label_reason = ttk.Label(
            self.game_frame_status, textvariable=self.var_reason, font=(('MSゴシック', '20')))

        self.label_turn.pack()
        self.progressbar.pack()
        self.label_winner.pack()
        self.label_reason.pack()

        # Cool

        self.labels['Cool'] = tk.StringVar()
        self.labels['Cool'].set('Item:0(Score:0)')

        self.label_cool_name = ttk.Label(
            self.game_frame_cool, text='自動君', font=self.font_normal)
        self.label_cool_score = ttk.Label(
            self.game_frame_cool, textvariable=self.labels['Cool'], font=self.font_normal)

        self.label_cool_name.pack()
        self.label_cool_score.pack()

        # Hot

        self.labels['Hot'] = tk.StringVar()
        self.labels['Hot'].set('Item:0(Score:0)')


        self.label_hot_name = ttk.Label(
            self.game_frame_hot, text='自動君', font=self.font_normal)
        self.label_hot_score = ttk.Label(
            self.game_frame_hot, textvariable=self.labels['Hot'], font=self.font_normal)

        self.label_hot_name.pack()
        self.label_hot_score.pack()

        self.game_canvas.grid(column=0, row=0, padx=6, rowspan=3)
        self.game_separator.grid(
            column=1, row=0, sticky='ns', rowspan=3, padx=6)
        self.game_frame_status.grid(column=2, row=0, padx=6)
        self.game_frame_cool.grid(column=2, row=1, padx=6)
        self.game_frame_hot.grid(column=2, row=2, padx=6)

        self.big_flame_game.pack()

    def menu_screen(self):
        # tk_setting
        self.font = ('', 10)
        self.big_flame_menu.columnconfigure(0, weight=1)
        self.big_flame_menu.columnconfigure(1, weight=1)

        # ver
        self.menu_settings_ver_log = tk.BooleanVar()
        self.menu_settings_ver_log.set(config.d['Log'])
        
        self.menu_settings_ver_score = tk.BooleanVar()
        self.menu_settings_ver_score.set(config.d['Score'])

        self.menu_settings_timeout_ver = tk.Variable()
        self.menu_settings_timeout_ver.set(config.d['TimeOut'])

        self.menu_settings_speed_ver = tk.Variable()
        self.menu_settings_speed_ver.set(config.d['GameSpeed'])

        self.menu_map_ver = tk.StringVar()
        self.menu_map_ver.set(config.d['NextMap'])

        # Cool
        self.menu_frame_cool, self.menu_label_ver_cool, self.menu_port_ver_cool, self.menu_mode_ver_cool, self.menu_button_cool, self.menu_cool_spinbox,  self.menu_cool_combobox = self.clients_menu(
            'COOL')
        self.menu_button_cool['command'] = self.cool_wait
        self.menu_cool_combobox.bind('<<ComboboxSelected>>', self.cool_stay)
        self.menu_port_ver_cool.set(config.d['CoolPort'])
        self.menu_mode_ver_cool.set(config.d['CoolMode'])

        # Hot
        self.menu_frame_hot, self.menu_label_ver_hot, self.menu_port_ver_hot, self.menu_mode_ver_hot, self.menu_button_hot, self.menu_hot_spinbox,  self.menu_hot_combobox = self.clients_menu(
            'HOT')
        self.menu_button_hot['command'] = self.hot_wait
        self.menu_hot_combobox.bind('<<ComboboxSelected>>', self.hot_stay)
        self.menu_port_ver_hot.set(config.d['HotPort'])
        self.menu_mode_ver_hot.set(config.d['HotMode'])

        # picture
        self.swall_image = ImageTk.PhotoImage(file='./画像/Swall.png')
        self.sitem_image = ImageTk.PhotoImage(file='./画像/Sitem.png')
        self.shot_image = ImageTk.PhotoImage(file='./画像/SHot.png')
        self.scool_image = ImageTk.PhotoImage(file='./画像/SCool.png')

        # map_view
        size = 18
        self.menu_canvas = tk.Canvas(
            self.big_flame_menu, width=15 * size, height=17 * size, background='white')

        self.menu_canvas.grid(row=1, column=0, padx=10)

        # map_select
        self.menu_frame_map_select = ttk.Frame(self.big_flame_menu)

        self.menu_combobox = ttk.Combobox(
            self.menu_frame_map_select, textvariable=self.menu_map_ver, state='readonly')
        self.menu_combobox.bind('<<ComboboxSelected>>', self.write_menu_map)
        self.menu_map_randomize = ttk.Button(
            self.menu_frame_map_select, text='ランダム', command=self.map_randomize)
        self.menu_combobox.grid(row=0, column=0, pady=5)
        self.menu_map_randomize.grid(row=0, column=1)

        self.list_up_maps()

        # server_address
        self.menu_server_address = ttk.Label(
            self.big_flame_menu, text=socket.gethostbyname(socket.gethostname()), font=self.font)

        self.menu_server_address.grid(row=4, column=0)

        # settings
        '''
        スコア
        ログ保存するか
        ゲーム進行速度
        タイムアウト
        ログ保存場所
        マップ保存場所
        設定リセット
        '''
        self.menu_frame_settings = ttk.Labelframe(
            self.big_flame_menu, text='設定')

        self.menu_settings_box_log = ttk.Checkbutton(
            self.menu_frame_settings, text='ログ保存', variable=self.menu_settings_ver_log)
        
        self.menu_settings_box_score = ttk.Checkbutton(
            self.menu_frame_settings, text='スコア', variable=self.menu_settings_ver_score)

        self.menu_settings_label_timeout = ttk.Label(
            self.menu_frame_settings, text='タイムアウト(ms)', font=self.font)
        self.menu_settings_spinbox_timeout = ttk.Spinbox(
            self.menu_frame_settings, textvariable=self.menu_settings_timeout_ver)
        self.menu_settings_label_speed = ttk.Label(
            self.menu_frame_settings, text='進行速度(ms)', font=self.font)
        self.menu_settings_spinbox_speed = ttk.Spinbox(
            self.menu_frame_settings, textvariable=self.menu_settings_speed_ver)
        self.menu_settings_spinbox_timeout['from'] = 0
        self.menu_settings_spinbox_timeout['to'] = 10000
        self.menu_settings_spinbox_timeout['increment'] = 10
        self.menu_settings_spinbox_speed['from'] = 0
        self.menu_settings_spinbox_speed['to'] = 10000
        self.menu_settings_spinbox_speed['increment'] = 10

        self.menu_settings_button_log = ttk.Button(
            self.menu_frame_settings, text='ログ保存場所', command=self.change_log)
        self.menu_settings_button_log.grid(row=3, column=0)

        self.menu_settings_button_map = ttk.Button(
            self.menu_frame_settings, text='マップ保存場所', command=self.change_map)
        self.menu_settings_button_map.grid(row=3, column=1)

        self.menu_settings_button_reset = ttk.Button(
            self.menu_frame_settings, text='設定のリセット', command=self.reset_config)
        self.menu_settings_button_reset.grid(row=4, column=0, columnspan=2)

        self.menu_settings_box_log.grid(row=0, column=0)
        self.menu_settings_box_score.grid(row=0, column=1)
        self.menu_settings_label_timeout.grid(row=1, column=0)
        self.menu_settings_spinbox_timeout.grid(row=2, column=0)
        self.menu_settings_label_speed.grid(row=1, column=1)
        self.menu_settings_spinbox_speed.grid(row=2, column=1)

        # game_start
        self.menu_game_start = ttk.Button(
            self.big_flame_menu, text='ゲーム開始', command=self.start_game)

        self.menu_game_start.grid(row=2, column=1, sticky=tk.W + tk.E)

        # Frame_grid
        self.menu_frame_cool.grid(
            row=0, column=0, sticky=tk.W + tk.E, pady=6, padx=5)
        self.menu_frame_hot.grid(row=0, column=1, sticky=tk.W + tk.E)
        self.menu_frame_map_select.grid(row=2, column=0)
        self.menu_frame_settings.grid(row=1, column=1)

    def clients_menu(self, name):
        label_ver = tk.StringVar(value='名前:\nIP:')
        frame = ttk.Labelframe(self.big_flame_menu, text=name)
        frame.columnconfigure(2, weight=1)
        label = ttk.Label(frame, textvariable=label_ver,
                          justify='left', anchor=tk.NW, font=self.font)
        spinbox_ver = tk.Variable()
        spinbox = ttk.Spinbox(frame, textvariable=spinbox_ver,
                              width=7)
        spinbox['from'] = 1024
        spinbox['to'] = 5000
        combobox_ver = tk.StringVar()
        combobox = ttk.Combobox(frame, state='readonly', textvariable=combobox_ver, values=[
                                'User', 'Stay', 'Bot'], width=6)
        button = ttk.Button(frame, text='待機開始')
        label.grid(row=0, column=0, sticky=tk.W, columnspan=2)
        spinbox.grid(row=1, column=0)
        combobox.grid(row=1, column=1)
        button.grid(row=1, column=2, sticky=tk.E + tk.W)

        return frame, label_ver, spinbox_ver, combobox_ver, button, spinbox, combobox

    def map_randomize(self):
        self.list_up_maps()
        self.menu_map_ver.set(random.choice(self.menu_combobox['values']))

    def save_config(self, flag=True):
        # flag が True なら終了
        config.d['CoolPort'] = int(self.menu_port_ver_cool.get())
        config.d['HotPort'] = int(self.menu_port_ver_hot.get())
        config.d['GameSpeed'] = int(self.menu_settings_speed_ver.get())
        config.d['TimeOut'] = int(self.menu_settings_timeout_ver.get())
        config.d['HotMode'] = self.menu_hot_combobox.get()
        config.d['CoolMode'] = self.menu_cool_combobox.get()
        config.d['NextMap'] = self.menu_map_ver.get()
        config.d['Log'] = self.menu_settings_ver_log.get()
        config.d['Score'] = self.menu_settings_ver_score.get()
        config.save()
        if flag:
            self.master.destroy()

    def reset_config(self):
        config.reset()
        self.hot_disconnect()
        self.cool_disconnect()
        self.menu_port_ver_cool.set(config.d['CoolPort'])
        self.menu_port_ver_hot.set(config.d['HotPort'])
        self.menu_settings_speed_ver.set(config.d['GameSpeed'])
        self.menu_settings_timeout_ver.set(config.d['TimeOut'])
        self.menu_hot_combobox.set(config.d['HotMode'])
        self.menu_cool_combobox.set(config.d['CoolMode'])
        self.menu_map_ver.set(config.d['NextMap'])
        self.menu_settings_ver_log.set(config.d['Log'])
        self.menu_settings_ver_score.set(config.d['Score'])
        
        self.write_menu_map(None)

    def change_log(self):
        if (c := filedialog.askdirectory(initialdir=__file__)) != '':
            config.d['LogPath'] = c

    def change_map(self):
        if (c := filedialog.askdirectory(initialdir=__file__)) != '':
            config.d['StagePath'] = c
            self.list_up_maps()

    def list_up_maps(self):
        l = []
        for i in os.listdir(config.d['StagePath']):
            if i[-6:] == '.CHmap':
                l.append(os.path.basename(i)[:-6])
        l.append('Blank')
        self.menu_combobox['values'] = l

    def cool_stay(self, _=None):
        if self.menu_mode_ver_cool.get() != 'User' and self.cool_state == 0:
            self.cool_wait()

    def hot_stay(self, _=None):
        if self.menu_mode_ver_hot.get() != 'User' and self.hot_state == 0:
            self.hot_wait()

    def cool_wait(self):
        self.pipe.send('C')
        if self.cool_state == 0:
            self.pipe.send('connect')
            self.pipe.send(self.menu_port_ver_cool.get())
            self.pipe.send(self.menu_mode_ver_cool.get())
            self.cool_state = 1
            self.menu_button_cool['text'] = '接続待ち'
            self.menu_cool_combobox['state'] = 'disable'
            self.menu_cool_spinbox['state'] = 'disable'
        else:
            self.cool_disconnect()

    def hot_wait(self):
        self.pipe.send('H')
        if self.hot_state == 0:
            self.pipe.send('connect')
            self.pipe.send(self.menu_port_ver_hot.get())
            self.pipe.send(self.menu_mode_ver_hot.get())
            self.hot_state = 1
            self.menu_button_hot['text'] = '接続待ち'
            self.menu_hot_combobox['state'] = 'disable'
            self.menu_hot_spinbox['state'] = 'disable'
        else:
            self.hot_disconnect()

    def cool_disconnect(self):
        self.pipe.send('disconnect')
        self.cool_state = 0
        self.menu_button_cool['text'] = '待機開始'
        self.menu_cool_combobox['state'] = 'readonly'
        self.menu_cool_spinbox['state'] = 'normal'
        self.menu_label_ver_cool.set('名前:\nIP:')

    def hot_disconnect(self):
        self.pipe.send('disconnect')
        self.hot_state = 0
        self.menu_button_hot['text'] = '待機開始'
        self.menu_hot_combobox['state'] = 'readonly'
        self.menu_hot_spinbox['state'] = 'normal'
        self.menu_label_ver_hot.set('名前:\nIP:')

    def start_game(self):
        # ゲームの停止も担当する
        if self.cool_state == self.hot_state == 2:
            if not self.is_game_started:
                self.menu_game_start['text'] = 'ゲーム停止'
                
                self.menu_button_cool['state'] = 'disable'
                self.menu_button_hot['state'] = 'disable'
                
                self.is_game_started = True
                self.game_screen()
                self.save_config(False)
                self.big_flame_game.tkraise()
                self.has_game_started = True

                self.label_cool_name['text'] = self.names['Cool']
                self.label_hot_name['text'] = self.names['Hot']

                self.pipe.send('start')
                self.pipe.send(config.d['StagePath'] +
                            r'/' + self.menu_map_ver.get())
                self.pipe.send(int(self.menu_settings_timeout_ver.get()))
                self.pipe.send(int(self.menu_settings_speed_ver.get()))
                self.write_map()
            else:
                self.menu_game_start['text'] = 'ゲーム開始'
                self.menu_game_start['state'] = 'disable'
                
                self.menu_button_cool['state'] = 'normal'
                self.menu_button_hot['state'] = 'normal'
                
                self.is_game_started = False
                if self.game.is_alive():
                    self.game.terminate()
                self.game = multiprocessing.Process(
                    target=Game, name='Server', args=(self.game_pipe,), daemon=True)
                self.game.start()
                self.cool_disconnect()
                self.hot_disconnect()
                
                self.game_window.destroy()

    def pipe_receive(self):
        while True:
            if self.cool_state == self.hot_state == 2:
                self.menu_game_start['state'] = 'normal'
            else:
                self.menu_game_start['state'] = 'disable'

            with self.condition:
                try:
                    match self.pipe.recv():
                        case 'Cool':
                            if self.pipe.recv() == 'connect':
                                self.cool_state = 2
                                self.menu_button_cool['text'] = '切断'
                                self.menu_label_ver_cool.set(
                                    f'名前:{(c := self.pipe.recv())}\nIP:{self.pipe.recv()}')
                                self.names['Cool'] = c
                            else:
                                self.cool_state = 0
                                self.menu_button_cool['text'] = '待機開始'
                                self.menu_cool_combobox['state'] = 'readonly'
                                self.menu_cool_spinbox['state'] = 'normal'
                                self.menu_label_ver_cool.set('名前:\nIP:')
                        case 'Hot':
                            if self.pipe.recv() == 'connect':
                                self.hot_state = 2
                                self.menu_button_hot['text'] = '切断'
                                self.menu_label_ver_hot.set(
                                    f'名前:{(c := self.pipe.recv())}\nIP:{self.pipe.recv()}')
                                self.names['Hot'] = c
                            else:
                                self.hot_state = 0
                                self.menu_button_hot['text'] = '待機開始'
                                self.menu_hot_combobox['state'] = 'readonly'
                                self.menu_hot_spinbox['state'] = 'normal'
                                self.menu_label_ver_hot.set('名前:\nIP:')
                        case 'Game':
                            # アニメーション入れる
                            cl = self.pipe.recv()
                            if cl != 'gameset':
                                nowpos = self.pipe.recv()
                                match self.pipe.recv():
                                    case 'w':
                                        i, j = self.pipe.recv()
                                        self.game_canvas.moveto(
                                            cl, i * 25 + 3, j * 25 + 3)
                                        if (c := self.pipe.recv()) == 'i':
                                            self.game_canvas.create_image(
                                                15 + nowpos[0] * 25, 15 + nowpos[1] * 25, image=self.wall_image)
                                            self.game_canvas.delete(
                                                self.game_screen_id[j][i])
                                            self.points[cl] += 1
                                        elif c == 'Gameset':
                                            self.game_set()
                                    case 'p':
                                        i, j = self.pipe.recv()
                                        self.game_canvas.create_image(
                                            15 + i * 25, 15 + j * 25, image=self.wall_image)

                                if cl == 'Hot':
                                    self.var_prog_turn.set(
                                        self.var_prog_turn.get() + 1)
                                    self.var_turn.set(
                                        f'Turn:{self.whole_turn - self.var_prog_turn.get()}')
                                    self.point_set(self.whole_turn - self.var_prog_turn.get())
                            else:
                                self.game_set()

                        case 'Gameset':
                            self.game_set()
                except EOFError:
                    exit()
    
    def inverse_client(self, cl) -> str:
        '''
        cl と 反対のクライアントを返す
        '''
        if cl == 'Hot':
            return 'Cool'
        else:
            return 'Hot'

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
                        15 + j * 25, 15 + i * 25, image=self.hot_image, tag='Hot')
                if cool == [j, i]:
                    self.game_canvas.create_image(
                        15 + j * 25, 15 + i * 25, image=self.cool_image, tag='Cool')
                match y:
                    case 2:
                        self.game_canvas.create_image(
                            15 + j * 25, 15 + i * 25, image=self.wall_image)
                    case 3:
                        self.game_screen_id[i][j] = self.game_canvas.create_image(
                            15 + j * 25, 15 + i * 25, image=self.item_image)

    def write_menu_map(self, _):
        game_map, hot, cool = self.read_map()
        padding = 10
        size = 18
        self.menu_canvas.delete('a')
        for i, x in enumerate(game_map):
            for j, y in enumerate(x):
                if hot == [j, i]:
                    self.menu_canvas.create_image(
                        padding + j * size, padding + i * size, image=self.shot_image, tag='a')
                if cool == [j, i]:
                    self.menu_canvas.create_image(
                        padding + j * size, padding + i * size, image=self.scool_image, tag='a')
                match y:
                    case 2:
                        self.menu_canvas.create_image(
                            padding + j * size, padding + i * size, image=self.swall_image, tag='a')
                    case 3:
                        self.menu_canvas.create_image(
                            padding + j * size, padding + i * size, image=self.sitem_image, tag='a')

    def read_map(self):
        try:
            with open(config.d['StagePath'] + r'/' + self.menu_map_ver.get() + '.CHmap', 'r') as f:
                j = json.load(f)
                game_map = j['Map']
                hot = j['Hot']
                cool = j['Cool']
                self.whole_turn = j['Turn']
                self.progressbar['maximum'] = self.whole_turn
        except FileNotFoundError:
            if self.menu_map_ver.get() == 'Blank':
                game_map = [[0 for i in range(15)] for i in range(17)]
                hot = [8, 9]
                cool = [6, 7]
                self.whole_turn = 100
            else:
                raise FileNotFoundError
        return game_map, hot, cool

    def game_set(self):
        cl = self.pipe.recv()
        self.var_turn.set(
            f'Turn:{self.whole_turn - self.var_prog_turn.get()}')
        turn = (self.whole_turn - self.var_prog_turn.get() - 1)
        match self.pipe.recv():  # Game.game_setを参照してください
            case 0:
                if self.points['Cool'] == self.points['Hot']:
                    self.var_winner.set('DRAW')
                elif self.points['Cool'] > self.points['Hot']:
                    self.var_winner.set('Cool WIN')
                else:
                    self.var_winner.set('Hot WIN')
            case 1:
                self.var_winner.set(f'{cl} WIN')
                self.point_set(turn, cl)
                self.var_reason.set('put勝ち')
            case 2:
                self.var_winner.set(f'{cl} WIN')
                self.point_set(turn, cl)
                self.var_reason.set('put勝ち(囲み)')
            case 3:
                self.var_winner.set(f'{cl} LOSE')
                self.point_set(turn, self.inverse_client(cl))
                self.var_reason.set('自滅負け(囲み)')
            case 4:
                self.var_winner.set(f'{cl} LOSE')
                self.point_set(turn, self.inverse_client(cl))
                self.var_reason.set('自滅負け')
            case 5:
                self.var_winner.set(f'{cl} LOSE')
                self.point_set(turn, self.inverse_client(cl))
                self.var_reason.set('通信エラー')
        if self.menu_settings_ver_log.get():
            self.pipe.send('ok')
            self.pipe.send(config.d['LogPath'])
        else:
            self.pipe.send('no')
    
    def point_set(self, turn, cl=None):
        if self.menu_settings_ver_score.get():
            if cl is not None:
                self.labels[cl].set(
                    f'Item:{self.points[cl]}(Score:{self.points[cl] * 3 + turn})')
                cl = self.inverse_client(cl)
                self.labels[cl].set(
                    f'Item:{self.points[cl]}(Score:{self.points[cl] * 3 - turn})')
            else:
                c = 'Cool'
                h = 'Hot'
                self.labels[c].set(
                    f'Item:{self.points[c]}(Score:{self.points[c] * 3 + turn})')
                self.labels[h].set(
                    f'Item:{self.points[h]}(Score:{self.points[h] * 3 + turn})')
        else:
            if cl is not None:
                self.labels[cl].set(
                    f'Item:{self.points[cl]}')
                cl = self.inverse_client(cl)
                self.labels[cl].set(
                    f'Item:{self.points[cl]}')
            else:
                c = 'Cool'
                h = 'Hot'
                self.labels[c].set(
                    f'Item:{self.points[c]}')
                self.labels[h].set(
                    f'Item:{self.points[h]}')


class ReadConfig:
    def __init__(self):
        self.d: Dict = {}
        self.__read()

    def __read(self):
        try:
            with open('Config.dt', mode='r', encoding='utf-8') as f:
                self.d = json.load(f)
        except FileNotFoundError:
            self.reset()

    def save(self):
        with open('Config.dt', 'w') as f:
            json.dump(self.d, f, indent=4)

    def reset(self):
        with open('Config.dt', mode='w', encoding='utf-8') as f:
            self.d = {"CoolPort": 2009, "HotPort": 2010, "GameSpeed": 100, "TimeOut": 2000, "HotMode": "User",
                      "CoolMode": "User", "LogPath": "./log", "StagePath": "./maps/", "NextMap": "Blank", "Score": False, "Log": False}
            json.dump(self.d, f, indent=4)


class Game:
    direction: dict[str, tuple[int, int]] = {
        'r': (1, 0), 'l': (-1, 0), 'd': (0, 1), 'u': (0, -1)}

    def __init__(self, pipe) -> None:
        ReadConfig().d['StagePath']
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

        self.cool_receiver = threading.Thread(
            target=Receiver, args=(for_cool_pipe,), name='Cool')
        self.cool_receiver.daemon = True
        self.hot_receiver = threading.Thread(
            target=Receiver, args=(for_hot_pipe,), name='Hot')
        self.hot_receiver.daemon = True

        self.log = []

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
                        self.speed = self.window_pipe.recv()

                        self.cool_pipe.send('s')
                        self.cool_pipe.send(self.timeout)

                        self.hot_pipe.send('s')
                        self.hot_pipe.send(self.timeout)
                        break
                    case 'shutdown':
                        self.hot_disconnect()
                        self.cool_disconnect()
                        exit()

            self.accept_connection('Cool', self.cool_pipe)
            self.accept_connection('Hot', self.hot_pipe)

        for i in range(self.turn):
            self.log.append(f'Turn:{self.turn - i}')
            self.cool_items, self.cool_place = self.action(
                self.cool_items, self.cool_place, self.hot_place, self.cool_pipe, 'Cool', i)
            time.sleep(self.speed / 1000)
            self.hot_items, self.hot_place = self.action(
                self.hot_items, self.hot_place, self.cool_place, self.hot_pipe, 'Hot', i)
            time.sleep(self.speed / 1000)

        self.game_set('', 0, self.turn - 1)

    def accept_connection(self, cl, pipe):
        if pipe.poll():
            match pipe.recv():
                case 'connect':
                    self.window_pipe.send(cl)
                    self.window_pipe.send('connect')
                    self.window_pipe.send((c := pipe.recv()))
                    if cl == 'Hot':
                        self.hot_name = c
                    else:
                        self.cool_name = c
                    self.window_pipe.send(pipe.recv())
                case 'd':
                    self.window_pipe.send(cl)
                    self.window_pipe.send('disconnect')

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

    def change_map(self):
        if self.map_name[-5:] == 'Blank':
            self.map = [[0 for i in range(15)] for i in range(17)]
            self.hot_place = [8, 9]
            self.cool_place = [6, 7]
            self.turn = 100
        else:
            with open(self.map_name + '.CHmap', 'r') as f:
                j = json.load(f)
                self.map = j['Map']
                self.hot_place = j['Hot']
                self.cool_place = j['Cool']
                self.turn = j['Turn']
        self.log.append('MAP')
        l = []
        for i, y in enumerate(self.map):
            l.append([])
            for j, x in enumerate(y):
                if self.cool_place[0] == j and self.cool_place[1] == i:
                    l[-1].append('C')
                elif self.hot_place[0] == j and self.hot_place[1] == i:
                    l[-1].append('H')

                else:
                    l[-1].append(str(x))
        for i in l:
            self.log.append(' '.join(i))

    def action(self, item, place: list, enemy_place: list, pipe, cl, turn: int):
        pipe.send('t')
        if pipe.recv() != 'ok':
            self.game_set(cl, 5, turn)
        pipe.send(self.output_square(True, *self.cool_place))
        next_place = place.copy()
        r = pipe.recv()
        self.log.append(f'{cl} {r}')

        self.window_pipe.send('Game')
        self.window_pipe.send(cl)
        self.window_pipe.send(place)
        self.window_pipe.send(r[0])

        is_getted_item = False

        c = ''
        match r[0]:
            case 'w':
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
                    self.window_pipe.send('i')
                else:
                    self.window_pipe.send('n')

            case 'p':
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
            case 'l':
                pipe.send((c := self.output_square(
                    False, place[0] + Game.direction[r[1]][0] * 2, place[1] + Game.direction[r[1]][1] * 2)))
            case 's':
                pipe.send((c := self.output_line(
                    place[0], place[1], *Game.direction[r[1]])))
            case 'C':
                self.game_set(cl, 5, turn)
        self.log.append(c)
        return item, next_place

    def game_set(self, cl: str, state: int, turn) -> NoReturn:
        '''
        state
        0: 通常ゲーム終了
        1: clがput勝ち
        2: clが敵を囲んだ
        3: clが自分を囲んだ
        4: clがブロックと重なった
        5: clが通信エラー
        '''
        d = {'Cool': 0, 'Hot': 0}
        left_turn = self.turn - turn - 1
        match state:
            case 0:
                self.log.append('試合が通常終了しました')
            case 1:
                self.log.append(f'{cl}がput勝ちしました')
                d[cl] = 1
                d[self.inverse_client(cl)] = -1
            case 2:
                self.log.append(f'{cl}が敵を囲みました')
                d[cl] = 1
                d[self.inverse_client(cl)] = -1
            case 3:
                self.log.append(f'{cl}が自分を囲みました')
                d[cl] = -1
                d[self.inverse_client(cl)] = 1
            case 4:
                self.log.append(f'{cl}がブロックと重なりました')
                d[cl] = -1
                d[self.inverse_client(cl)] = 1
            case 5:
                self.log.append(f'{cl}が通信エラーしました')
                d[cl] = -1
                d[self.inverse_client(cl)] = 1

        self.log.append('ITEM')
        self.log.append(f'Cool: {self.cool_items}')
        self.log.append(f'Hot: {self.hot_items}')
        self.log.append('POINT')
        self.log.append(f'Cool: {self.cool_items * 3 + d["Cool"] * left_turn}')
        self.log.append(f'Hot: {self.hot_items * 3 + d["Hot"] * left_turn}')

        self.window_pipe.send('Gameset')
        self.window_pipe.send(cl)
        self.window_pipe.send(state)
        if self.window_pipe.recv() == 'ok':
            path = self.window_pipe.recv()
            serial = 1
            while os.path.exists(f'{path}/{self.hot_name} VS {self.cool_name}({serial}).txt'):
                serial += 1
            with open(f'{path}/{self.hot_name} VS {self.cool_name}({serial}).txt', mode='w', encoding='utf-8') as f:
                for i in self.log:
                    f.write(i + '\n')
        self.cool_disconnect()
        self.hot_disconnect()
        exit()

    def inverse_client(self, cl) -> str:
        '''
        cl と 反対のクライアントを返す
        '''
        if cl == 'Hot':
            return 'Cool'
        else:
            return 'Hot'

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
        self.to_client_socket = socket.socket()
        self.flag_socket = False  # socket が listenかどうか
        self.flag_to_client_socket = False  # to_client_socket が つながったかどうか
        self.flag_bot_name = False
        self.flag_ended = False

        self.flag_error = False

        while True:
            if self.pipe.poll():
                match self.pipe.recv():
                    case 'c':  # connect
                        self.port = pipe.recv()
                        self.mode = pipe.recv()
                        self.socket = socket.socket()
                        if self.mode != 'Stay':
                            if self.mode == 'Bot':
                                os.system('start Bot.py ' + str(self.port))
                            self.socket.setblocking(False)
                            self.socket.bind(('', int(self.port)))
                            self.socket.listen()
                        self.flag_socket = True
                    case 'd':  # dis-connect
                        self.mode = 'User'
                        self.to_client_socket.close()
                        self.flag_socket = False
                        self.flag_to_client_socket = False
                        self.flag_bot_name = False
                        self.flag_ended = False
                    case 's':  # start
                        break

            if self.mode == 'Stay':
                if not self.flag_bot_name:
                    self.flag_socket = False
                    pipe.send('connect')
                    pipe.send('Stay Bot')
                    pipe.send('Bot')
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
                    self.pipe.send('connect')
                    self.pipe.send(c.decode('utf-8').strip())
                    self.pipe.send(self.client[0])
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
                if self.flag_error:
                    self.close()
                match pipe.recv():
                    case 't':  # your turn
                        self.to_client_socket.send(b'@')
                        if self.socket_receive() != 'gr':
                            self.close()
                        self.pipe.send('ok')
                        self.to_client_socket.send(
                            self.pipe.recv().encode('utf-8'))
                        self.pipe.send(self.socket_receive())
                        self.to_client_socket.send(
                            self.pipe.recv().encode('utf-8'))
                        if self.socket_receive() != '#':
                            self.close()
                    case 'd':
                        self.close()
        except EOFError:  # ゲーム終了時
            pass

    def socket_receive(self):
        start = time.time()
        r = ''
        while True:
            if self.pipe.poll() and self.pipe.recv() == 'd':
                self.close()
            elif time.time() - start >= self.timeout:
                self.close()
            try:
                c = self.to_client_socket.recv(4096)
                r = c.decode('utf-8').strip()
            except BlockingIOError:
                continue
            except ConnectionAbortedError:
                self.close()
            if r == '':
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
            self.pipe.send('Cl')
        except BrokenPipeError:
            pass
        exit()


if __name__ == '__main__':
    config = ReadConfig()

    root = tk.Tk()
    root.geometry('680x450')
    root.resizable(False, False)
    game_window = Game_Window(root)

    game_window.mainloop()
