'''
Main.pyのテスト用
'''
import socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
address = ('127.0.0.1', 50001)
client.connect((address))
while True:
    inp = input().strip()
    client.sendto((inp + '\r\n').encode('utf-8'), ('127.0.0.1', 50001))
    print(client.recv(2048).decode('utf-8'))
