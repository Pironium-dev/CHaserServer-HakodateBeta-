import tkinter as tk
import tkinter.ttk as ttk
import subprocess
import os
import os.path
import ipaddress
import atexit

class Window(tk.Frame):
    def __init__(self, master:tk.Tk):
        tk.Frame.__init__(self, master=master)
        
        self.process: list = [None, None]
        
        self.left_port = tk.IntVar()
        self.left_port.set(2009)
        self.left_spinbox = tk.Spinbox(width=5, textvariable=self.left_port, command=self.judge_available)
        self.left_spinbox['increment'] = 1
        self.left_spinbox['to'] = 5000
        self.left_spinbox['from'] = 1024
        
        self.right_port = tk.IntVar()
        self.right_port.set(2010)
        self.right_spinbox = tk.Spinbox(width=5, textvariable=self.right_port, command=self.judge_available)
        self.right_spinbox['increment'] = 1
        self.right_spinbox['to'] = 5000
        self.right_spinbox['from'] = 1024
        
        self.target_address = tk.StringVar(value='127.0.0.1')
        self.ipaddress_entry = tk.Entry(textvariable=self.target_address)
        
        self.state = tk.StringVar(value='idle')
        self.state_label = tk.Label(textvariable=self.state)
        
        l = self.list_up_bots()
        self.left_combobox = ttk.Combobox(values=l, state='readonly')
        self.right_combobox = ttk.Combobox(values=l, state='readonly')
        
        self.left_combobox.bind('<<ComboboxSelected>>', self.judge_available)
        self.right_combobox.bind('<<ComboboxSelected>>', self.judge_available)
        
        self.reverse_button = tk.Button(text='Reverse', command=self.reverse)
        self.start_button = tk.Button(text='start', command=self.run)
        
        self.left_spinbox.grid(row=0, column=0)
        self.right_spinbox.grid(row=0, column=1)
        
        self.left_combobox.grid(row=1, column=0)
        self.right_combobox.grid(row=1, column=1)
        
        self.ipaddress_entry.grid(row=2, column=0)
        self.state_label.grid(row=2, column=1)
        
        self.reverse_button.grid(row=3, column=0)
        self.start_button.grid(row=3, column=1)
        
        self.start_button['state'] = 'disable'
        self.check_state()
        atexit.register(self.shutdown)
    
    def reverse(self):
        l = self.left_port.get()
        r = self.right_port.get()
        self.left_port.set(r)
        self.right_port.set(l)
    
    def run(self):
        try:
            ipaddress.ip_address(self.target_address.get())
        except ValueError:
            return
        self.execute_client(self.left_combobox.get(), str(self.left_port.get()), self.left_combobox.get(), self.target_address.get(), 0)
        self.execute_client(self.right_combobox.get(), str(self.right_port.get()), self.right_combobox.get(), self.target_address.get(), 1)
    
    def list_up_bots(self) -> list:
        l = []
        for i in os.listdir('./Clients/'):
            if i[-2:] == 'py':
                l.append(os.path.basename(i))
            if i[-3:] == 'exe':
                l.append(os.path.basename(i))
        if 'CHaser.py' in l:
            l.remove('CHaser.py')
        return l
    
    def execute_client(self, target:str, port:str, name:str, ipaddress:str, b: int):
        self.process[b] = subprocess.Popen(os.path.abspath('./Clients/' + target), shell=True, stdin=subprocess.PIPE)
        lout = [port, name, ipaddress]
        l = ('\n'.join(lout)).encode()
        try:
            self.process[b].communicate(input=l, timeout=0)
        except subprocess.TimeoutExpired:
            pass
    
    def judge_available(self, _=None):
        if (self.left_port.get() == self.right_port.get()) or self.left_combobox.get().strip() == '' or self.right_combobox.get().strip() == '':
            self.start_button['state'] = 'disable'
        else:
            self.start_button['state'] = 'normal'
    
    def check_state(self):
        if self.process[0] is not None:
            if self.process[0].poll() == self.process[1].poll() == 0:
                self.state.set('idle')
            else:
                self.state.set('running')
        
        self.after(500, self.check_state)
    
    def shutdown(self):
        if self.process[0] is not None:
            self.process[0].terminate()
            self.process[1].terminate()

if __name__ == '__main__':
    master = tk.Tk()
    master.title('handler')
    window = Window(master)
    master.resizable(False, False)

    window.mainloop()