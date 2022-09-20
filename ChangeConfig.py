import json

with open('Config.dt', 'r') as f:
    dic = json.load(f)
li = [[i, j] for i, j in dic.items()]


def output():
    for i, j in enumerate(li):
        print(i, *j)


print('コンフィグ設定です')
print('end でセーブせず終了')
print('save でセーブして終了')
print('')
while True:
    output()
    match (ip := input().strip()):
        case 'end':
            exit()
        case 'save':
            with open('Config.dt', 'w') as f:
                json.dump(dict(li), f, indent=4)
                exit()
        case _:
            inp = int(ip)
            li[inp][1] = int(input('変更を入力してください :'))
