"""Программа-клиент"""

import sys
import json
import socket
import time
import settings as s

from message import Message


def create_presence(account_name="Guest"):
    """
    Функция генерирует запрос о присутствии клиента
    :param account_name:
    :return:
    """
    # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
    out = {
        s.ACTION: s.PRESENCE,
        s.TIME: time.time(),
        s.USER: {s.ACCOUNT_NAME: account_name},
    }
    return out


def create_message(account_name="Guest", msg=""):

    out = {
        s.ACTION: "msg",
        s.TIME: time.time(),
        s.TO: "#room_name",
        s.FROM: account_name,
        s.MESSAGE: msg,
    }
    return out


def process_ans(message):
    """
    Функция разбирает ответ сервера
    :param message:
    :return:
    """
    if s.RESPONSE in message:
        if message[s.RESPONSE] == 200:
            return "200 : OK"
        return f"400 : {message[s.ERROR]}"
    raise ValueError


def create_socket(addr, port, name):
    # Инициализация сокета и обмен
    m = Message()
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((addr, port))
    message_to_server = create_presence(name)
    m.send(transport, message_to_server)
    try:
        answer = process_ans(m.get(transport))
        print(answer)
    except (ValueError, json.JSONDecodeError):
        print("Не удалось декодировать сообщение сервера.")
