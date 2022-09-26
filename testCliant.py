'''
Communication.pyのテスト用
'''
import socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 50001))
while True:
    inp = input().strip()
    client.sendall(inp.encode('utf-8') + b'/r/n')
