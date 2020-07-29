import json
import socket
import sys

import settings as s
from message import Message


def client_message_handler(message):
    """
    Message handler from clients, accepts dictionary -
    message from the client, checks correctness,
    returns the response dictionary for the client

    """
    if (
        s.ACTION in message
        and message[s.ACTION] == s.PRESENCE
        and s.TIME in message
        and s.USER in message
        and message[s.USER][s.ACCOUNT_NAME] != ""
    ):
        return {s.RESPONSE: 200}
    return {s.RESPONSE: 400, s.ERROR: "Bad Request"}


def create_socket(addr, port):

    message = Message()
    # Готовим сокет

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((addr, port))
    # Слушаем порт
    transport.listen(s.MAX_CONNECTIONS)

    while True:
        print(f"The server listens {addr}: {port}\nPress CTRL + C to stop the server\n")
        try:
            client, client_address = transport.accept()
        except KeyboardInterrupt:
            print('\nThe server is stopped')
            client.close()
            sys.exit(1)
        try:
            print(client, client_address)
            message_from_client = message.get(client)
            print(message_from_client)
            # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
            response = client_message_handler(message_from_client)
            message.send(client, response)
            client.close()
        except KeyboardInterrupt:
            sys.exit(1)
        except (ValueError, json.JSONDecodeError):
            print("Принято некорретное сообщение от клиента.")
        client.close()


def main():
    """
        Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию.
        Сначала обрабатываем порт:
        server.py -p 8079 -a 192.168.1.2
    """
    try:
        if "-p" in sys.argv:
            listen_port = int(sys.argv[sys.argv.index("-p") + 1])
        else:
            listen_port = s.DEFAULT_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print("После параметра -'p' необходимо указать номер порта.")
        sys.exit(1)
    except ValueError:
        print(
            "В качастве порта может быть указано только число в диапазоне от 1024 до 65535."
        )
        sys.exit(1)
    # Затем загружаем какой адрес слушать
    try:
        if "-a" in sys.argv:
            listen_address = sys.argv[sys.argv.index("-a") + 1]
        else:
            listen_address = "127.0.0.1"

    except IndexError:
        print(
            "После параметра 'a'- необходимо указать адрес, который будет слушать сервер."
        )
        sys.exit(1)
    create_socket(listen_address, listen_port)


if __name__ == "__main__":
    main()
