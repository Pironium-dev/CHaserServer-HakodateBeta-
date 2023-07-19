import json
import os
from tkinter import filedialog

out = {'Map': [], 'Turn': 0, 'Cool': [], 'Hot': []}

file = filedialog.askopenfilename(filetypes=[('CHaserMap', '*.map')], initialdir=__file__)
if file != '':
    with open(file, 'r', encoding='utf-8') as f:
        for i in f.readlines():
            match i[0]:
                case 'T':
                    out['Turn'] = int(i[2:]) 
                case 'D':
                    out['Map'].append([int(j) for j in i[2:].rstrip().split(',')])
                case 'C':
                    out['Cool'] = [int(j) for j in i[2:].rstrip().split(',')]
                case 'H':
                    out['Hot'] = [int(j) for j in i[2:].rstrip().split(',')]


    with open('./maps/' + os.path.splitext(os.path.basename(file))[0] + '.json', 'w') as f:
        json.dump(out, f)