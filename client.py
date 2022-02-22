import socket
import sys
import select
import time


def main():
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"
    port = 1234
    clientSocket.connect((host, port))
    print("Welcome to the quiz!\n")
    while True:
        message = clientSocket.recv(2048).decode('ascii')
        if message:
            if message == 'over1':
                print('Questions deck is empty. Declaring winner(s)..!')
                continue
            if message == 'over':
                print('GameOver!!!')
                time.sleep(0.5)
                break
            elif message == 'hit':
                r, o, e = select.select([sys.stdin, clientSocket], [], [], 5)
                if r:
                    for sock in r:
                        if sys.stdin == sock:
                            p = sys.stdin.readline()
                            msg = p.split()
                            if len(msg) == 2:
                                if (msg[1] == 'tak') or (msg[1] == 'nie'):
                                    clientSocket.send(p.encode())
                                else:
                                    print('(You have to type "*number of question* *answer*".')
                                    clientSocket.send('error'.encode())
                            else:
                                print('You have to type "*number of question* *answer*".')
                                clientSocket.send('error'.encode())
                else:
                    pass
            elif message == 'number':
                print('How many players will play?')
                time.sleep(0.3)
                n = sys.stdin.readline().strip()
                clientSocket.send(n.encode())
            elif message == 'start':
                print('To start the game type "start"')
                s = sys.stdin.readline().strip()
                clientSocket.send(s.encode())
            else:
                print(message)
    clientSocket.close()
    exit()


main()
