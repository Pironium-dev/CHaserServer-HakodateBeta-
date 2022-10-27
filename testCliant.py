'''
Main.pyのテスト用
'''

import socket
import ipaddress
import os
import time
import sys


class Client:
    def __init__(self, port):
        self.port = port
        self.name = port
        '''if input('ローカルに接続しますか？(y/n)') == 'y':
            self.host = '127.0.0.1'
        else:
            self.host = input('IPアドレスを入力してください ⇒ ')'''
        self.host = '127.0.0.1'

        if not self.__ip_judge(self.host):
            os._exit(1)

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        while True:
            try:
                self.client.connect((self.host, int(self.port)))
            except ConnectionRefusedError:
                if not self.connected:
                    self.connected = True
                    print('サーバーが起動していません')
                continue
            break

        print("port:", self.port)
        print("name:", self.name)
        print("host:", self.host)

        self.__str_send(self.name + "\r\n")

    def __ip_judge(self, host):
        try:
            ipaddress.ip_address(host)
        except Exception as e:
            print("IPアドレスの形式に誤りがあります : {0}".format(e))
            return False
        else:
            return True

    def __str_send(self, send_str):
        try:
            self.client.sendall(send_str.encode("utf-8"))
        except OSError:
            print("send error:{0}\0".format(send_str))

    def __order(self, order_str, gr_flag=False):
        try:
            if gr_flag:
                responce = self.client.recv(4096)

                if b"@" in responce:
                    pass  # Connection completed.
                else:
                    print("Connection failed.")

            self.__str_send(order_str + "\r\n")

            responce = self.client.recv(4096)[0:11].decode("utf-8")

            if not gr_flag:
                self.__str_send("#\r\n")

            if responce[0] == "1":
                return [int(x) for x in responce[1:10]]
            elif responce[0] == "0":
                raise OSError("Game Set!")
            else:
                print("responce[0] = {0} : Response error.".format(responce[0]))
                raise OSError("Responce Error")

        except OSError as e:
            print(e)
            self.client.close()
            os._exit(0)

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


cool = Client(sys.argv[1])

while True:
    cool.get_ready()
    cool.walk_down()
