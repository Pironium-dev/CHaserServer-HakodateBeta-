import socket
import threading

'''
Cool, Hotのスレッドを立てる
port:10000で二回待つ
mainに渡す
'''


def Receiver(pnumber):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', pnumber))
    server_socket.listen()
    (tocliant_socket, address) = server_socket.accept()

    def receive() -> str:
        s = ''
        while ('/r/n' not in s) and (c := tocliant_socket.recv(2048).decode('utf-8')) != '':
            s += c
        return s

    while True:
        if (out := receive()):
            print(out)


class Communication:
    def __init__(self, cool_port: int, hot_port: int) -> None:
        cool_server = threading.Thread(target=Receiver, args=(cool_port, ))
        hot_server = threading.Thread(target=Receiver, args=(hot_port, ))
        cool_server.start()
        hot_server.start()


if __name__ == '__main__':
    from ReadConfig import ReadConfig
    config = ReadConfig().output_config()
    communication = Communication(config['CoolPort'], config['HotPort'])
