import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import glob
import os
import ReadConfig

class change_config(tk.Frame):
    def __init__(self, master):
        self.CONFIG = ReadConfig.ReadConfig()
        self.game_config = self.CONFIG.d
        self.stage_names = []
        
        tk.Frame.__init__(self, master=master)
        master.title('Config')
        
        self.communicate_frame = tk.LabelFrame(master, text='通信', relief='ridge')
        self.game_frame = tk.LabelFrame(master, text='ゲーム')
        self.folder_frame = tk.LabelFrame(master, text='フォルダ')
        
        # 通信の設定
        self.cool_label = tk.Label(self.communicate_frame, text='CoolPort (2009)')
        self.hot_label = tk.Label(self.communicate_frame, text='HotPort (2010)')
        self.time_out_label = tk.Label(self.communicate_frame, text='TimeOut (20000)')
        
        self.cool_entry = tk.Entry(self.communicate_frame, width=5)
        self.cool_entry.insert(0, str(self.game_config['CoolPort']))
        self.hot_entry = tk.Entry(self.communicate_frame, width=5)
        self.hot_entry.insert(0, str(self.game_config['HotPort']))
        
        self.time_out_entry = tk.Entry(self.communicate_frame, width=5)
        self.time_out_entry.insert(0, str(self.game_config['TimeOut']))
        
        self.cool_label.pack()
        self.cool_entry.pack()
        self.hot_label.pack()
        self.hot_entry.pack()
        self.time_out_label.pack()
        self.time_out_entry.pack()
        
        # ゲーム設定
        
        self.speed_label = tk.Label(self.game_frame, text='GameSpeed (100)')
        self.bot_mode_label = tk.Label(self.game_frame, text='BotMode')
        self.stage_label = tk.Label(self.game_frame, text='StageSelect')
        
        self.speed_entry = tk.Entry(self.game_frame, width = 5)
        self.speed_entry.insert(0, str(self.game_config['GameSpeed']))
        self.bot_mode_combobox = ttk.Combobox(self.game_frame, values=['User', 'Stay', 'Bot'], state='readonly')
        self.bot_mode_combobox.set(str(self.game_config['CoolMode']))
        self.stage_combobox = ttk.Combobox(self.game_frame, state='readonly')
        self.stage_combobox.set(self.game_config['NextStage'])
        
        self.speed_label.pack()
        self.speed_entry.pack()
        self.bot_mode_label.pack()
        self.bot_mode_combobox.pack()
        self.stage_label.pack()
        self.stage_combobox.pack()
        
        # ファイル設定
        
        self.log_path = self.game_config['LogPath']
        self.stage_path = self.game_config['StagePath']
        self.stage_select()
        
        self.log_path_button = tk.Button(self.folder_frame, text='Log出力位置の変更', command=self.log_changed)
        self.stage_path_label = tk.Button(self.folder_frame, text='ステージのフォルダの変更', command=self.stage_changed)
        self.log_path_button.pack()
        self.stage_path_label.pack()
        
        self.communicate_frame.grid(column=0,row=0)
        self.game_frame.grid(column=1, row=0)
        self.folder_frame.grid(column=2, row=0)
        
        # セーブ
        
        self.save_button = tk.Button(master, text='Save', command=self.save)
        self.save_button.grid(column=2, row=1)
    
    def save(self):
        self.game_config['CoolPort'] = int(self.cool_entry.get())
        self.game_config['HotPort'] = int(self.hot_entry.get())
        self.game_config['TimeOut'] = int(self.time_out_entry.get())
        self.game_config['GameSpeed'] = int(self.speed_entry.get())
        self.game_config['AntiBotMode'] = self.bot_mode_combobox.get()
        self.game_config['LogPath'] = self.log_path
        self.game_config['StagePath'] = self.stage_path
        self.game_config['NextStage'] = self.stage_combobox.get()
        self.CONFIG.save()
        self.master.destroy()
    
    def log_changed(self):
        self.log_path = filedialog.askdirectory()
    def stage_changed(self):
        self.stage_path = filedialog.askdirectory()
        self.stage_select()
    
    def stage_select(self):
        self.stage_names = []
        for i in glob.glob(self.stage_path + r'/*.CHmap'):
            self.stage_names.append(os.path.basename(i[:-6]))
        self.stage_combobox['values'] = ['Random', 'Blank'] + self.stage_names



if __name__ == '__main__':
    root = tk.Tk()
    change = change_config(root)

    change.mainloop()