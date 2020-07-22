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
        and message[s.USER][s.ACCOUNT_NAME] == "Guest"
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
        print("Слушаю")
        client, client_address = transport.accept()
        try:
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
