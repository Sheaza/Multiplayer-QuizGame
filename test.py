import random
import time
from _thread import *
import socket
from Quiz import Q_A

HOST = 'localhost'
PORT = 1234
players = []
CORRECT_ANSWER = 1
WRONG_ANSWER = -2
max_players = 4
game_on = 0
Q_A2 = random.sample(Q_A, k=10)
a = ""
scores = []
active = [0]
person = ["client", -1]

# Creating a socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket created..")

# Binding a socket

try:
    server.bind((HOST, PORT))
except socket.error as msg:
    print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])

server.listen(4)
print('Waiting for connection. Server started.')


def threaded_client(conn, number_of_players):
    reply = ""
    send_message(conn, 'You are player number ' + str(number_of_players) + '\n')
    time.sleep(2)

    while game_on:
        t = time.time()
        print("waiting for answer\n")
        while time.time() - t < 5:
            print(time.time()-t)
            answer = receive_message(conn)
            if answer:
                if active[0] == 0:
                    print("buzzed\n")
                    person[0] = conn
                    active[0] = 1
                    j = 0
                    for j in range(0, len(players)):
                        print(len(players))
                        print(j)
                        if players[j] == active[0]:
                            break
                    person[1] = j
                elif active[0] == 1 and conn == person[0]:
                    print('answering\n' + str(person[1]))
                    print(answer)
                    if answer == 'tak' or answer == 'nie':
                        isCorrect = (answer == a)
                        if isCorrect:
                            send_message(conn, "Answer correct. 1 point added.\n")
                            scores[j-1] += CORRECT_ANSWER
                            break
                        else:
                            send_message(conn, "Wrong answer. 2 point subtracted\n")
                            scores[j-1] += WRONG_ANSWER
                            active[0] = 0
                    else:
                        send_message(conn, "Invalid answer\n")
                    active[0] = 0
        active[0] = 0
        start_game()

    print('Lost connection')
    #conn.close
    return 0


def send_message(player, message):
    try:
        player.sendall(bytes(message, 'utf-8'))
    except:
        player.close()
        players.remove(player)


def send_message_all(player, message):
    for x in players:
        if x != player and x != server:
            try:
                x.sendall(bytes(message, 'utf-8'))
            except:
                x.close()
                players.remove(x)


def receive_message(player):
    message = player.recv(4).decode('utf-8')
    return message


def start_game():
    print("start game\n")
    time.sleep(2)
    send_question()


def send_question():
    print("sending question\n")
    global a
    print(Q_A2)
    if len(Q_A2) != 0:
        random.shuffle(Q_A2)
        q_a = Q_A2[0]
        q = q_a[0]
        a = q_a[1]
        send_message_all(None, q + '\n')
        Q_A2.pop(0)
    else:
        end_game()


def end_game():
    send_message_all(None, "Game Over, players!\n")
    winner = scores.index(max(scores))
    send_message_all(None, "player " + str(winner + 1) + " Wins!! by scoring " + str(scores[winner]) + " points.")
    for p in range(len(players)):
        send_message(players[p], "You scored " + str(scores[p]) + " points.")
    server.close()


number_of_players = 0
while True:
    if number_of_players < max_players:
        conn, addr = server.accept()
        print('Connected to: ' + str(addr))
        number_of_players += 1
        players.append(conn)
        if number_of_players == 1:
            send_message(conn, 'How many players will play?\n')
            max_players = int(receive_message(conn))
    else:
        conn, addr = server.accept()
        send_message(conn, 'Lobby is full.')
        conn.close()
    if number_of_players == max_players:
        send_message(players[0], 'To start the game press enter.\n')
        if len(receive_message(players[0])) > 0:
            game_on = 1
            i = 1
            for x in players:
                scores.append(0)
                print(scores)
                start_new_thread(threaded_client, (x, i))
                i += 1
            start_game()
        else:
            for x in players:
                print("error")
                x.close()
server.close()
