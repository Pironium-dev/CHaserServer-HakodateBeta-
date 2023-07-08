import tkinter as tk
from tkinter.filedialog import asksaveasfile, askopenfile
from tkinter.messagebox import showerror
import json
from itertools import chain
import os


class Window(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.write_screen()
        self.read_config()

        self.map = [[0 for i in range(17)] for j in range(15)]  # XとYは逆
        self.place_hot = [-1, -1]
        self.place_cool = [-1, -1]

        self.file_name = ""

        self.changed_rule_check_button()

    def write_screen(self):
        # image
        self.wall_image = tk.PhotoImage(file="./resources/wall.png")
        self.item_image = tk.PhotoImage(file="./resources/item.png")
        self.hot_image = tk.PhotoImage(file="./resources/Hot.png")
        self.cool_image = tk.PhotoImage(file="./resources/Cool.png")

        # map
        self.canvas = tk.Canvas(width=378, height=428, bg="white", borderwidth=0)
        self.canvas.create_line(0, 2, 378, 2)
        self.canvas.create_line(0, 428, 379, 428)
        self.canvas.create_line(378, 2, 378, 428)
        self.canvas.create_line(2, 2, 2, 428)
        for i in range(1, 17):
            self.canvas.create_line(0, 2 + i * 25, 378, 2 + i * 25, dash=(1, 1))
        for i in range(1, 15):
            self.canvas.create_line(2 + i * 25, 0, 2 + i * 25, 428, dash=(1, 1))

        # setting
        self.setting_frame = tk.Frame(root)

        self.radio_frame = tk.Frame(self.setting_frame)
        self.radio_box_var = tk.IntVar(value=1)
        self.radio_box_client = tk.Radiobutton(
            self.radio_frame,
            variable=self.radio_box_var,
            value=1,
        )
        self.radio_box_wall = tk.Radiobutton(
            self.radio_frame, variable=self.radio_box_var, value=2
        )
        self.radio_box_item = tk.Radiobutton(
            self.radio_frame, variable=self.radio_box_var, value=3
        )

        self.radio_canvas = tk.Canvas(self.radio_frame, height=27, width=87)
        self.radio_canvas.create_image(2, 2, image=self.cool_image, anchor=tk.NW)
        self.radio_canvas.create_image(30, 2, image=self.wall_image, anchor=tk.NW)
        self.radio_canvas.create_image(58, 2, image=self.item_image, anchor=tk.NW)

        self.radio_box_client.grid(row=1, column=0)
        self.radio_box_wall.grid(row=1, column=1)
        self.radio_box_item.grid(row=1, column=2)
        self.radio_canvas.grid(row=0, column=0, columnspan=3)

        self.help_label = tk.Label(self.setting_frame, text="右クリックで削除")

        self.is_symmetry = tk.BooleanVar(value=True)
        self.check_button_symmetry = tk.Checkbutton(
            self.setting_frame, text="対称", variable=self.is_symmetry
        )

        self.is_rule = tk.BooleanVar(value=True)
        self.check_button_rule = tk.Checkbutton(
            self.setting_frame,
            text="ルール",
            variable=self.is_rule,
            command=self.changed_rule_check_button,
        )

        self.turn_var = tk.StringVar(value="100")
        self.turn_label = tk.Label(self.setting_frame, text="TURN")
        self.turn_spinbox = tk.Spinbox(
            self.setting_frame, width=5, from_=1, to=999, textvariable=self.turn_var
        )

        self.loading_button = tk.Button(
            self.setting_frame, text="読み込み", command=self.load
        )
        self.write_button = tk.Button(
            self.setting_frame, text="書き込み", command=self.save
        )

        self.radio_frame.pack()

        self.help_label.pack()

        self.check_button_symmetry.pack()
        self.check_button_rule.pack()

        self.turn_label.pack()
        self.turn_spinbox.pack()

        self.loading_button.pack()
        self.write_button.pack()

        self.canvas.bind("<Button-1>", self.canvas_click_write)
        self.canvas.bind("<B1-Motion>", self.canvas_click_write)
        self.canvas.bind("<Button-3>", self.canvas_click_delete)
        self.canvas.bind("<B3-Motion>", self.canvas_click_delete)
        self.canvas.grid(column=0, row=0)
        self.setting_frame.grid(column=1, row=0)

    def canvas_click_write(self, event):
        x, y = self.coordinate(event)
        if x == -1:
            return
        if self.is_rule.get() and x == 7 and y == 8:
            return
        if [x, y] == self.place_cool or [x, y] == self.place_hot:
            return
        kind = self.radio_box_var.get()
        if kind == 1:
            if self.map[x][y] == 0:
                if self.place_cool[0] != -1:
                    self.canvas.delete("client")
                self.place_chip(x, y, kind)
                self.place_cool = [x, y]
                self.place_hot = list(self.symmetry_place(x, y))
            return
        if kind == 2 and self.is_rule.get():
            if x == 0 or x == 14 or y == 16 or y == 0:
                return
            if x == self.place_cool[0] and abs(y - self.place_cool[1]) == 9:
                return
            if x == self.place_hot[0] and abs(y - self.place_hot[1]) == 9:
                return
        self.place_chip(x, y, kind)
        self.map[x][y] = kind
        if self.is_symmetry.get():
            x, y = self.symmetry_place(x, y)
            self.place_chip(x, y, kind)
            self.map[x][y] = kind

    def canvas_click_delete(self, event):
        x, y = self.coordinate(event)
        if x == -1:
            return
        if self.is_rule.get() and x == 7 and y == 8:
            return
        if [x, y] == self.place_cool or [x, y] == self.place_hot:
            return
        self.delete_chip(x, y)

    def save(self):
        if self.place_cool == [-1, -1] or self.place_hot == [-1, -1]:
            showerror("Map Edit", "クライアントが配置されていません")
            return
        file = asksaveasfile(
            "w",
            initialdir=self.config["StagePath"],
            filetypes=[("マップ", ".json")],
            defaultextension="json",
            initialfile=self.file_name,
        )
        if file is not None:
            d = {
                "Map": self.convert(self.map),
                "Turn": int(self.turn_var.get()),
                "Cool": self.place_cool,
                "Hot": self.place_hot,
            }
            json.dump(d, file)

    def load(self):
        file = askopenfile(
            initialdir=self.config["StagePath"],
            filetypes=[("マップ", ".json")],
            defaultextension="json",
        )
        if file is not None:
            try:
                d = json.load(file)
                self.map = self.convert(d["Map"])
                for i, x in enumerate(self.convert(d["Map"])):
                    for j, y in enumerate(x):
                        self.canvas.delete(f"{i}_{j}")
                        self.place_chip(i, j, y)
                if self.place_cool[0] != -1:
                    self.canvas.delete("client")
                self.place_cool = d["Cool"]
                self.place_chip(*self.place_cool, kind=1)
                self.place_hot = d["Hot"]
                self.turn_var.set(str(d["Turn"]))

                self.file_name = os.path.splitext(os.path.basename(file.name))[0]
            except KeyError:
                showerror("Map Edit", "間違ったファイルを読み込みました。")

    def symmetry_place(self, x, y):
        return 14 - x, 16 - y

    def coordinate(self, event):
        x = event.x
        y = event.y
        x -= 2
        y -= 2
        x //= 25
        y //= 25
        if not (0 <= x <= 14 and 0 <= y <= 16):
            return -1, -1
        return x, y

    def place_chip(self, x, y, kind):
        match kind:
            case 1:
                self.canvas.create_image(
                    15 + x * 25, 15 + y * 25, image=self.cool_image, tag="client"
                )
                x, y = self.symmetry_place(x, y)
                self.canvas.create_image(
                    15 + x * 25, 15 + y * 25, image=self.hot_image, tag="client"
                )
            case 2:
                self.canvas.create_image(
                    15 + x * 25, 15 + y * 25, image=self.wall_image, tag=f"{x}_{y}"
                )
            case 3:
                self.canvas.create_image(
                    15 + x * 25, 15 + y * 25, image=self.item_image, tag=f"{x}_{y}"
                )

    def delete_chip(self, x, y):
        self.canvas.delete(f"{x}_{y}")
        self.map[x][y] = 0
        x, y = self.symmetry_place(x, y)
        if self.is_symmetry.get() and self.map[x][y] != 0:
            self.canvas.delete(f"{x}_{y}")
            self.map[x][y] = 0

    def convert(self, li: list):
        output = [[] for i in li[0]]
        l = len(li[0])
        s = 0
        for i in chain(*li):
            output[s].append(i)
            s += 1
            s %= l
        return output

    def read_config(self):
        with open("Config.dt", "r") as f:
            self.config = json.load(f)

    def changed_rule_check_button(self, _=None):
        if self.is_rule.get():
            self.map[7][8] = 3
            self.place_chip(7, 8, 3)
            self.is_symmetry.set(True)
            self.check_button_symmetry["state"] = "disable"
        else:
            self.check_button_symmetry["state"] = "normal"


if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    root.title("Map Edit")

    window = Window(root)
    window.mainloop()
