"""Программа-клиент"""

import argparse
import json
import logging
import socket
import sys
import time

import settings as s
from decorators import Log
from logger import client_logger
from message import Message

LOG = logging.getLogger("client")


@Log()
def arg_parser():
    """Создаём парсер аргументов коммандной строки
    и читаем параметры, возвращаем 3 параметра
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", default=s.DEFAULT_IP_ADDRESS, nargs="?")
    parser.add_argument("-p", default=s.DEFAULT_PORT, type=int, nargs="?")
    parser.add_argument("-m", "--mode", default="listen", nargs="?")
    parser.add_argument("-n", "--name", default="Guest", nargs="?")
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.a
    server_port = namespace.p
    client_mode = namespace.mode
    name = namespace.name

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        LOG.critical(
            f"Попытка запуска клиента с неподходящим номером порта: {server_port}. "
            f"Допустимы адреса с 1024 до 65535. Клиент завершается."
        )
        sys.exit(1)

    # Проверим допустим ли выбранный режим работы клиента
    if client_mode not in ("listen", "send"):
        LOG.critical(
            f"Указан недопустимый режим работы {client_mode}, "
            f"допустимые режимы: listen , send"
        )
        sys.exit(1)

    return server_address, server_port, client_mode, name


@Log()
def message_from_server(message):
    """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
    if (
        s.KEY_ACTION in message
        and message[s.KEY_ACTION] == s.ACTION_MESSAGE
        and s.KEY_FROM in message
        and s.KEY_MESSAGE in message
    ):
        print(
            f"Получено сообщение от пользователя "
            f"{message[s.KEY_FROM]}:\n{message[s.KEY_MESSAGE]}"
        )
        LOG.info(
            f"Получено сообщение от пользователя "
            f"{message[s.KEY_FROM]}:\n{message[s.KEY_MESSAGE]}"
        )
    else:
        LOG.error(f"Получено некорректное сообщение с сервера: {message}")


@Log()
def create_presence(account_name="Guest"):
    """Функция генерирует запрос о присутствии клиента"""
    out = {
        s.KEY_ACTION: s.ACTION_PRESENCE,
        s.KEY_TIME: time.time(),
        s.KEY_USER: {s.KEY_ACCOUNT_NAME: account_name},
    }
    LOG.debug(
        f"Сформировано {s.ACTION_PRESENCE} сообщение для пользователя {account_name}"
    )
    return out


@Log()
def create_message(sock, account_name="Guest"):
    """Функция запрашивает текст сообщения и возвращает его.
    Так же завершает работу при вводе подобной комманды
    """
    message = input("Введите сообщение для отправки или '!!!' для завершения работы: ")
    if message == "!!!":
        sock.close()
        LOG.info("Завершение работы по команде пользователя.")
        print("Спасибо за использование нашего сервиса!")
        sys.exit(0)
    message_dict = {
        s.KEY_ACTION: s.ACTION_MESSAGE,
        s.KEY_TIME: time.time(),
        s.KEY_ACCOUNT_NAME: account_name,
        s.KEY_MESSAGE: message,
    }
    LOG.debug(f"Сформирован словарь сообщения: {message_dict}")
    return message_dict


@Log()
def process_ans(message):
    """
    Функция разбирает ответ сервера
    :param message:
    :return:
    """
    if s.KEY_RESPONSE in message:
        if message[s.KEY_RESPONSE] == 200:
            return "200 : OK"
        return f"400 : {message[s.KEY_ERROR]}"
    raise ValueError


@Log()
def create_socket(server_address, server_port, client_mode, name):
    # Инициализация сокета и обмен
    msg = Message()
    LOG.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, режим работы: {client_mode}')
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        message_to_server = create_presence(name)
        msg.send(transport, message_to_server)
        answer = process_ans(msg.get(transport))
        print(answer)
    except (ValueError, json.JSONDecodeError):
        print("Не удалось декодировать сообщение сервера.")

    else:
        # Если соединение с сервером установлено корректно,
        # начинаем обмен с ним, согласно требуемому режиму.
        # основной цикл прогрммы:
        if client_mode == "send":
            print("Режим работы - отправка сообщений.")
        else:
            print("Режим работы - приём сообщений.")
        while True:
            # режим работы - отправка сообщений
            if client_mode == "send":
                try:
                    msg.send(transport, create_message(transport))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    LOG.error(f"Соединение с сервером {server_address} было потеряно.")
                    sys.exit(1)

            # Режим работы приём:
            if client_mode == "listen":
                try:
                    mfs = message_from_server(msg.get(transport))
                    print(mfs)
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    LOG.error(f"Соединение с сервером {server_address} было потеряно.")
                    sys.exit(1)


@Log()
def main():
    """Загружаем параметы коммандной строки"""
    server_address, server_port, client_mode, name = arg_parser()
    create_socket(server_address, server_port, client_mode, name)


if __name__ == "__main__":
    main()
