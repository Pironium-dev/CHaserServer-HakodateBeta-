import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tk_f

class Screen(tk.Frame):
    def __init__(self, master:tk.Tk):
        tk.Frame.__init__(self, master=master)
        master.title('MainWindow')
        
        self.canvas = tk.Canvas(width=380, height=430, bg='white')
        self.canvas_frame = [self.canvas.create_line(0, 2, 380, 2), 
                             self.canvas.create_line(0, 430, 380, 430), 
                             self.canvas.create_line(380, 2, 380, 430), 
                             self.canvas.create_line(2, 2, 2, 430)]
        ttk.Style().configure('black.TSeparator', background='black')
        self.separator = ttk.Separator(orient='vertical', style='black.TSeparator')
        
        # font
        self.font_normal = tk_f.Font(family='MSゴシック', size=25)
        
        # status
        self.var_turn = tk.StringVar()
        self.var_winner = tk.StringVar()
        
        self.var_turn.set('Turn:100')
        self.var_winner.set('Draw')
        
        self.frame_status = ttk.Frame()
        self.label_turn = ttk.Label(self.frame_status, textvariable=self.var_turn, font=self.font_normal)
        self.progressbar = ttk.Progressbar(self.frame_status, maximum=100, length=220)
        self.label_winner = ttk.Label(self.frame_status, textvariable=self.var_winner, font=(('MSゴシック', '30')))
        
        self.label_turn.pack()
        self.progressbar.pack()
        self.label_winner.pack()
        
        # Cool
        
        self.var_cool_score = tk.StringVar()
        self.var_cool_score.set('Score:0(Item:0)')
        
        self.frame_cool = ttk.Labelframe(text='Cool')
        
        self.label_cool_name = ttk.Label(self.frame_cool, text='自動君', font=self.font_normal)
        self.label_cool_score = ttk.Label(self.frame_cool, textvariable=self.var_cool_score, font=self.font_normal)
        
        self.label_cool_name.pack()
        self.label_cool_score.pack()
        
        # Hot
        self.var_hot_score = tk.StringVar()
        self.var_hot_score.set('Score:0(Item:0)')
        
        self.frame_hot = ttk.Labelframe(text='Hot')
        
        self.label_hot_name = ttk.Label(self.frame_hot, text='自動君', font=self.font_normal)
        self.label_hot_score = ttk.Label(self.frame_hot, textvariable=self.var_cool_score, font=self.font_normal)
        
        self.label_hot_name.pack()
        self.label_hot_score.pack()
        
        self.canvas.grid(column=0, row=0, padx=6, rowspan=3)
        self.separator.grid(column=1,row=0, sticky='ns', rowspan=3, padx=6)
        self.frame_status.grid(column=2, row=0, padx=6)
        self.frame_cool.grid(column=2, row=1, padx=6)
        self.frame_hot.grid(column=2, row=2, padx=6)

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('680x450')
    root.resizable(False, False)
    screen = Screen(root)
    
    screen.mainloop()