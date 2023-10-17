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
        self.port = tk.IntVar()
        self.port.set(2009)
        self.target_address = tk.StringVar(value='127.0.0.1')
        self.process = None
        
        self.start_button = tk.Button(text='Start', command=self.run)
        self.combobox = ttk.Combobox(values=self.list_up_bots(), )
        self.state = tk.Label()
        self.port_button = tk.Button(textvariable=self.port, command=self.reverse)
        self.ipaddress_entry = tk.Entry(textvariable=self.target_address)
        
        self.port_button.grid(column=0, row=0)
        self.combobox.grid(column=1, row=0)
        self.state.grid(column=0, row=1)
        self.ipaddress_entry.grid(column=1, row=1)
        self.start_button.grid(row=2, columnspan=2)
        
        self.check_state()
        atexit.register(self.shutdown)

    def reverse(self):
        if self.port.get() == 2009:
            self.port.set(2010)
        else:
            self.port.set(2009)
    
    def run(self):
        if self.combobox.get() == '':
            return
        if self.state['text'] == 'running':
            self.shutdown()
        else:
            try:
                ipaddress.ip_address(self.target_address.get())
            except ValueError:
                return
            self.execute_client(self.combobox.get(), str(self.port.get()), self.target_address.get())
    
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
    
    def execute_client(self, target:str, port:str, ipaddress:str):
        self.process = subprocess.Popen(os.path.abspath('./Clients/' + target) + ' ' + ' '.join([port, target, ipaddress]), shell=True, stdin=subprocess.PIPE)
    
    def judge_available(self, _=None):
        if self.port.get() or self.combobox.get().strip() == '':
            self.start_button['state'] = 'disable'
        else:
            self.start_button['state'] = 'normal'
    
    def check_state(self):
        if self.process is not None:
            if self.process.poll() is not None:
                self.state['text'] = 'idle'
            else:
                self.state['text'] = 'running'
        else:
            self.state['text'] = 'idle'
            
        self.after(500, self.check_state)
    
    def shutdown(self):
        if self.process is not None:
            self.process.kill()

if __name__ == '__main__':
    master = tk.Tk()
    master.title('handler ver1.0')
    window = Window(master)
    master.resizable(False, False)

    window.mainloop()