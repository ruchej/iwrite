"""Программа-клиент"""

import argparse
import json
import logging
import socket
import sys
import threading
import time

import settings as s
from decorators import Log
from logger import client_logger
from message import Message

LOG = logging.getLogger("client")


@Log()
def exit_message(account_name):
    """Функция создаёт словарь с сообщением о выходе"""
    return {
        s.KEY_ACTION: s.ACTION_EXIT,
        s.KEY_TIME: time.time(),
        s.KEY_ACCOUNT_NAME: account_name,
    }


@Log()
def arg_parser():
    """Создаём парсер аргументов коммандной строки
    и читаем параметры, возвращаем 3 параметра
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", default=s.DEFAULT_IP_ADDRESS, nargs="?")
    parser.add_argument("-p", default=s.DEFAULT_PORT, type=int, nargs="?")
    parser.add_argument("-n", "--name", default=None, nargs="?")
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.a
    server_port = namespace.p
    name = namespace.name

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        LOG.critical(
            f"Попытка запуска клиента с неподходящим номером порта: {server_port}. "
            f"Допустимы адреса с 1024 до 65535. Клиент завершается."
        )
        sys.exit(1)

    return server_address, server_port, name


@Log()
def message_from_server(sock, user_name):
    """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
    msg = Message()
    while True:
        try:
            message = msg.get(sock)
            if (
                s.KEY_ACTION in message
                and message[s.KEY_ACTION] == s.ACTION_MESSAGE
                and s.KEY_FROM in message
                and s.KEY_TO in message
                and s.KEY_MESSAGE in message
                and message[s.KEY_TO] == user_name
            ):
                print(
                    f"\nПолучено сообщение от пользователя "
                    f"{message[s.KEY_FROM]}:\n{message[s.KEY_MESSAGE]}"
                )
                LOG.info(
                    f"Получено сообщение от пользователя "
                    f"{message[s.KEY_FROM]}:\n{message[s.KEY_MESSAGE]}"
                )
            else:
                LOG.error(f"Получено некорректное сообщение с сервера: {message}")

        except (
            OSError,
            ConnectionError,
            ConnectionAbortedError,
            ConnectionResetError,
            json.JSONDecodeError,
        ):
            LOG.critical(f"Потеряно соединение с сервером.")
            break


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
    msg = Message()
    to_user = input("Введите получателя сообщения: ")
    message = input("Введите сообщение для отправки: ")
    message_dict = {
        s.KEY_ACTION: s.ACTION_MESSAGE,
        s.KEY_FROM: account_name,
        s.KEY_TO: to_user,
        s.KEY_TIME: time.time(),
        s.KEY_MESSAGE: message,
    }
    LOG.debug(f"Сформирован словарь сообщения: {message_dict}")
    try:
        msg.send(sock, message_dict)
        LOG.info(f"Отправлено сообщение для пользователя {to_user}")
    except:
        LOG.critical("Потеряно соединение с сервером")
        sys.exit(1)


@Log()
def user_interactive(sock, username):
    """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
    msg = Message()
    print_help()
    while True:
        command = input("Введите команду: ")
        if command == "message":
            create_message(sock, username)
        elif command == "help":
            print_help()
        elif command == "exit":
            msg.send(sock, exit_message(username))
            print("Завершение соединения.")
            LOG.info("Завершение работы по команде пользователя.")
            # Задержка неоходима, чтобы успело уйти сообщение о выходе
            time.sleep(0.5)
            break
        else:
            print(
                "Команда не распознана, попробойте снова. help - вывести поддерживаемые команды."
            )


@Log()
def process_ans(message):
    """
    Функция разбирает ответ сервера
    """
    LOG.debug(f"Разбор приветственного сообщения от сервера: {message}")
    if s.KEY_RESPONSE in message:
        if message[s.KEY_RESPONSE] == 200:
            return "200 : OK"
        return f"400 : {message[s.KEY_ERROR]}"
    raise ValueError


@Log()
def create_socket(server_address, server_port, client_name):
    # Инициализация сокета и обмен
    msg = Message()
    # Если имя пользователя не было задано, необходимо запросить пользователя.
    if not client_name:
        client_name = input("Введите имя пользователя: ")

    LOG.info(
        f"Запущен клиент с парамертами: адрес сервера: {server_address}, "
        f"порт: {server_port}, имя пользователя: {client_name}"
    )
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        message_to_server = create_presence(client_name)
        msg.send(transport, message_to_server)
        answer = process_ans(msg.get(transport))
        LOG.info(f"Установлено соединение с сервером. Ответ сервера: {answer}")
        print(f"Установлено соединение с сервером.")
    except (ValueError, json.JSONDecodeError):
        print("Не удалось декодировать сообщение сервера.")

    else:
        # Если соединение с сервером установлено корректно,
        # запускаем клиенский процесс приёма сообщний
        receiver = threading.Thread(
            target=message_from_server, args=(transport, client_name)
        )
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = threading.Thread(
            target=user_interactive, args=(transport, client_name)
        )
        user_interface.daemon = True
        user_interface.start()
        LOG.debug("Запущены процессы")

        # Watchdog основной цикл, если один из потоков завершён,
        # то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках,
        # достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


def print_help():
    """Функция выводящяя справку по использованию"""
    print("Поддерживаемые команды:")
    print("message - отправить сообщение. Кому и текст будет запрошены отдельно.")
    print("help - вывести подсказки по командам")
    print("exit - выход из программы")


@Log()
def main():
    """Сообщаем о запуске"""
    print("Консольный месседжер. Клиентский модуль.")

    server_address, server_port, name = arg_parser()
    create_socket(server_address, server_port, name)


if __name__ == "__main__":
    main()
