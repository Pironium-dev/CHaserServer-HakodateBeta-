from CHaser import Client
from pprint import pprint
from collections import deque

BLANK = 0
ENEMY = 1
BROCK = 2
ITEM = 3

DIR = {'u':(-1, 0), 'l':(0, -1), 'd':(1, 0),  'r':(0, 1)}
LOOK_DIR = [(i, j) for i in range(-1, 2) for j in range(-1, 2)]
# 横:15 縦:17

class Extended_client(Client):
    def __init__(self):
        super().__init__()
        self.is_position = False
        self.x = -1
        self.y = -1
        
        self.map = [[4 for i in range(15)] for i in range(17)]
        self.map[8][7] = ITEM
    
    def decide_position(self, li):
        self.x = self.__calc_position(li[0], li[1], 17)
        self.y = self.__calc_position(li[2], li[3], 15)
        
        self.memorize_search(li[0], self.x, self.y, 'u')
        self.memorize_search(li[1], self.x, self.y, 'd')
        self.memorize_search(li[2], self.x, self.y, 'l')
        self.memorize_search(li[3], self.x, self.y, 'r')
        self.is_position = True

    def __calc_position(self, a, b, size):
        c = list(reversed(a)) + [0] + b
        if c[0] == BROCK:
            for i, j in enumerate(c):
                if j != BROCK:
                    return 9 - i
        else:
            for i, j in enumerate(reversed(c)):
                if j != BROCK:
                    return size - 10 + i
    
    def memorize_search(self, li, x, y, dir):
        for i in li:
            x += DIR[dir][0]
            y += DIR[dir][1]
            self.write_map(x, y, i)

    def memorize_look(self, li, x, y, gr_flag = False):
        for i, j in zip(li, LOOK_DIR):
            if j == (0, 0) and gr_flag:
                self.write_map(x + j[0], y + j[1], BLANK)
            else:
                self.write_map(x + j[0], y + j[1], i)

    def write_map(self, x, y, c):
        if 0 <= x <= 16 and 0 <= y <= 14:
            self.map[x][y] = c
            if self.map[16 - x][14 - y] == 4:
                self.map[16 - x][14 - y] = c
    
    def read_map(self, x, y):
        if 0 <= x <= 16 and 0 <= y <= 14:
            return self.map[x][y]
        return BROCK
    
    def __order(self, order_str, gr_flag=False):
        out = super()._Client__order(order_str, gr_flag) # type: ignore
        if self.is_position:
            match order_str[0]:
                case 'g':
                    self.memorize_look(out, self.x, self.y, True)
                case 'l':
                    self.memorize_look(out, self.x + DIR[order_str[1]][0] * 2, self.y + DIR[order_str[1]][1] * 2)
                case 's':
                    self.memorize_search(out, self.x, self.y, order_str[1])
                case 'w':
                    self.x += DIR[order_str[1]][0]
                    self.y += DIR[order_str[1]][1]
                case 'p':
                    self.write_map(self.x + DIR[order_str[1]][0], self.y + DIR[order_str[1]][1], BROCK)
                    self.memorize_look(out, self.x, self.y)
        return out
    
    def get_ready(self):
        return self.__order("gr", True)

    def walk_right(self):
        return self.__order("wr")

    def walk_up(self):
        return self.__order("wu")

    def walk_left(self):
        return self.__order("wl")

    def walk_down(self):
        return self.__order("wd")

    def look_right(self):
        return self.__order("lr")

    def look_up(self):
        return self.__order("lu")

    def look_left(self):
        return self.__order("ll")

    def look_down(self):
        return self.__order("ld")

    def search_right(self):
        return self.__order("sr")

    def search_up(self):
        return self.__order("su")

    def search_left(self):
        return self.__order("sl")

    def search_down(self):
        return self.__order("sd")

    def put_right(self):
        return self.__order("pr")

    def put_up(self):
        return self.__order("pu")

    def put_left(self):
        return self.__order("pl")

    def put_down(self):
        return self.__order("pd")

def kill_enemy(li):
    if li[1] == ENEMY:
        bot.put_up()
    elif li[3] == ENEMY:
        bot.put_left()
    elif li[5] == ENEMY:
        bot.put_right()
    elif li[7] == ENEMY:
        bot.put_down()
    else:
        return True
    return False

def action(s):
    match s:
        case 'wu':
            return bot.walk_up()
        case 'wl':
            return bot.walk_left()
        case 'wr':
            return bot.walk_right()
        case 'wd':
            return bot.walk_down()
        case 'pu':
            return bot.put_up()
        case 'pl':
            return bot.put_left()
        case 'pr':
            return bot.put_right()
        case 'pd':
            return bot.put_down()
        case 'lu':
            return bot.look_up()
        case 'll':
            return bot.look_left()
        case 'lr':
            return bot.look_right()
        case 'ld':
            return bot.look_down()
        case 'su':
            return bot.search_up()
        case 'sl':
            return bot.search_left()
        case 'sr':
            return bot.search_right()
        case 'sd':
            return bot.search_down()

bot = Extended_client()

search_memory = []
for i in ['su', 'sd', 'sl', 'sr']:
    if kill_enemy(bot.get_ready()):
        search_memory.append(action(i))

bot.decide_position(search_memory)

while True:
    if kill_enemy(bot.get_ready()):
        # 幅優先探索
        map = bot.map.copy()
        map[bot.x][bot.y] = 'C' # type: ignore
        pprint(map)
        que = deque()
        place = set()
        place.add((bot.x, bot.y))
        for i, j in DIR.items():
            que.append((i, '', bot.x + j[0], bot.y + j[1], 1))
        item_way = ''
        unknown_way = ''
        unknown_long = 0
        while que:
            dir, b_dir, x, y, c = que.popleft()
            if (x, y) not in place and 0 <= x <= 16 and 0 <= y <= 14:
                place.add((x, y))
                match bot.read_map(x, y):
                    case 0:
                        for i, (dx, dy) in DIR.items():
                            que.append((dir, i, x + dx, y + dy, c + 1))
                    case 3:
                        if not item_way:
                            item_way = dir
                            break
                    case 4:
                        if not unknown_way:
                            unknown_way = dir
                            unknown_long = c
        if item_way:
            action('w' + item_way)
            print(bot.port, 'item')
        elif unknown_way:
            action('w' + unknown_way)
            print(bot.port, 'unknown')
            print('next')
        else:
            bot.look_up()