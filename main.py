import socket
import select
import time
import random
import threading
from Quiz import *

deck = list(range(1, 11))
random.shuffle(deck)

clients = []
current_client_num = -1
current_client = 0
scores = []
strikes = []
num_of_clients = 0
others_blocked = 0
max_players = 5
question_num = 0
paused = -1
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
started = 0

hit = 'hit'
start = 'start'
number = 'number'

questions = []
answers = []
message = ""
i = 0


def accept_socket():
    global num_of_clients, max_players, started
    while True:
        conn, addr = server_socket.accept()
        print("Connected with " + str(addr[1]))
        if num_of_clients == max_players:
            conn.close()
            print('Max players achieved. Disconnecting client..')
        else:
            conn.send('You are connected.\n'.encode())
            clients.append(conn)
            scores.append(0)
            strikes.append(0)
            num_of_clients += 1
            conn.send(('You are Player ' + str(num_of_clients) + '.\n').encode())
            time.sleep(0.3)
            if num_of_clients == 1:
                while max_players > 4 or max_players < 2:
                    clients[1].send(number.encode())
                    time.sleep(0.3)
                    player_msg = clients[1].recv(1024).decode('ascii')
                    try:
                        max_players = int(player_msg)
                    except Exception as e:
                        print(e)
                    if max_players > 4 or max_players < 2:
                        clients[1].send('Wrong number. It should be between 2 and 4.\n'.encode())
                        time.sleep(0.5)
                        continue
                    else:
                        print('PLayer 1 set max players number to ' + str(max_players))
                        break
            conn.sendall('Waiting to start the game..\n'.encode())

            if num_of_clients == max_players and started != 1:
                while True:
                    time.sleep(0.3)
                    clients[1].send(start.encode())
                    start_msg = clients[1].recv(1024).decode('ascii')
                    if start_msg == 'start':
                        print('Starting the game..!')
                        time.sleep(2)
                        started = 1
                        break
                    else:
                        time.sleep(0.3)
                        clients[1].send('Try typing "start"\n'.encode())
                        continue


def main():
    Q = random.sample(q, 10)
    global questions, answers
    for x in Q:
        questions.append(x[0])
        answers.append(x[1])

    global clients, num_of_clients, max_players, server_socket
    host = "127.0.0.1"
    port = 1234
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    print("Socket binded to port " + str(port))
    server_socket.listen(5)
    print("Server is ready!")
    print("Waiting for the players to join!")
    clients = [server_socket]
    print('Starting threads..\n')
    t1 = threading.Thread(target=accept_socket, daemon=True)
    t2 = threading.Thread(target=game)
    print('Threads started!\n')

    t1.start()
    t2.start()

    t2.join()
    print('\nServer is closing..')
    server_socket.close()


def game():
    global others_blocked, current_client, current_client_num, scores, clients, question_num, strikes, paused
    global message, i, server_socket, started
    while True:
        if started:
            end = 0
            paused = -1
            answered = 0
            others_blocked = 0
            time.sleep(0.3)
            question = send_Question()
            if question == 1:
                print('Questions deck is empty. Declaring winner(s)..!')
                time.sleep(0.3)
                send_Msg_To_All('over1', clients[0])
                time.sleep(0.3)
                print_Scores(1)
                break
            t0 = time.time() + 5
            while time.time() < t0:
                time.sleep(0.1)
                for strike in strikes:
                    if strike == 3:
                        paused = strikes.index(strike)
                send_Msg_To_All(hit, clients[0])
                if paused != -1:
                    temp = clients.copy()
                    temp.pop(paused + 1)
                    r, w, e = select.select(temp, [], [], 5)

                else:
                    r, w, e = select.select(clients, [], [], 5)
                if r:
                    for sock in r:
                        try:
                            message = sock.recv(1024).decode('ascii')
                            if not message:
                                print('Player ' + str(clients.index(sock)) + ' disconnected\n')
                                send_Msg_To_All(('Player ' + str(clients.index(sock)) + ' disconnected..\n'), clients[0])
                                sock.close()
                                clients.pop(clients.index(sock))
                                time.sleep(0.1)
                                continue
                        except Exception as e:
                            print(e)
                        current_client = sock
                        i = 0
                        while i < len(clients):
                            if clients[i] == current_client:
                                i -= 1
                                break
                            i += 1
                        current_client_num = i + 1

                        if (others_blocked == 0) and (i != paused):
                            others_blocked = 1
                            break
                        else:
                            time.sleep(0.1)
                            continue
                else:
                    break
                if others_blocked:
                    otherisfaster = 'Player' + str(current_client_num) + ' was faster!'
                    time.sleep(0.1)
                    send_Msg_To_All(otherisfaster, current_client)

                if message == 'error':
                    print('Message error.')
                    continue
                else:
                    msg = message.split()
                if message:
                    if msg[0] == str(question_num):
                        answer = check_Answer(question, msg[1], i, current_client)
                        if answer == 1:
                            end = 1
                            print('Player ' + str(i) + ' wins the game by scoring 5 points.')
                            answered = 1
                            break
                        elif answer == 2:
                            others_blocked = 0
                            continue
                        elif answer == 3:
                            answered = 1
                            break
                    else:
                        time.sleep(0.1)
                        # current_client.send('Wrong ID!\n'.encode())
            if answered == 0:
                time.sleep(0.1)
                send_Msg_To_All('\nTime up!', clients[0])
                time.sleep(0.1)
                send_Msg_To_All('Proceeding with next question..\n', clients[0])
                answers.pop(question)
                print('Time up! Proceeding with next question..\n')
                print_Scores(1)
                strikes[paused] = 0
            else:
                if end:
                    break
                else:
                    time.sleep(0.1)
                    send_Msg_To_All('Proceeding with next question..\n', clients[0])
                    answers.pop(question)
                    print('Proceeding with next question..\n')
                    print_Scores(1)
                    strikes[paused] = 0

    time.sleep(1)
    declare_Winners()
    time.sleep(0.5)


def print_Scores(option):
    j = 0
    if option == 1:
        print('Updated scores: ')
        while j < len(scores):
            print('Player' + str(j + 1) + ': ' + str(scores[j])),
            j += 1
        print('\n')
    elif option == 2:
        send_Msg_To_All('Scores: \n', clients[0])
        while j < len(scores):
            send_Msg_To_All(('Player' + str(j + 1) + ': ' + str(scores[j]) + '\n'), clients[0]),
            j += 1
        send_Msg_To_All('\n', clients[0])


def declare_Winners():
    global scores
    winners = []
    maximum = max(scores)
    for s in range(len(scores)):
        if scores[s] == maximum:
            winners.append(s)
    if len(winners) > 0:
        time.sleep(0.2)
        print_Scores(2)
        send_Msg_To_All('Winner(s) are:\n', clients[0])
        for x in winners:
            send_Msg_To_All('Player ' + str(x + 1) + '\n', clients[0])
    time.sleep(0.2)
    send_Msg_To_All('over', clients[0])


def check_Answer(question, answer, k, conn):
    print('Player' + str(k) + ' answered ' + answer + ', and the correct answer is ' + answers[question])
    if answer == answers[question]:
        print('Player' + str(k) + ' answered correctly...+1 point.\n')
        scores[k] += 1
        answered_correctly = 'P ' + str(current_client_num) + ' got +1 point!\n'
        answered_correctly_One = 'Correct!..+1 point.\n'
        time.sleep(0.2)
        send_Msg_To_All(answered_correctly, conn)
        conn.send(answered_correctly_One.encode())
        if scores[k] == 5:
            game_over = 'Game over!\n' + str(current_client_num) + ' Won!'
            game_over_One = 'You Won!\n'
            time.sleep(0.2)
            send_Msg_To_All(game_over, conn)
            conn.send(game_over_One.encode())
            return 1
        return 3
    else:
        print('Player' + str(k) + ' answered wrongly...-2 points.\n')
        answered_wrong = 'P ' + str(current_client_num) + ' got -2 points.\n'
        answered_wrong_One = 'Wrong answer..-2 points.\n'
        scores[k] -= 2
        strikes[k] += 1
        time.sleep(0.2)
        send_Msg_To_All(answered_wrong, conn)
        conn.send(answered_wrong_One.encode())
        if strikes[k] == 3:
            conn.send('3 wrong answers. You are paused for 1 round.\n'.encode())
        return 2


def send_Msg_To_All(m, exception):
    global clients
    for client in clients:
        if exception == client:
            continue
        try:
            client.send(m.encode())
        except IOError:
            pass


def send_Question():
    global questions, question_num, deck
    if len(questions) > 0:
        question_num = deck.pop()
        question = 0
        que = '(ID ' + str(question_num) + ') ' + questions[question]
        print(que)
        time.sleep(0.2)
        send_Msg_To_All(que, clients[0])
        send_Msg_To_All('\nYou have 5 seconds to answer (ID answer).', clients[0])
        print('Sent the question successfully!...Removing it from the list!')
        time.sleep(0.2)
        questions.pop(question)
        return question
    else:
        return 1


main()
