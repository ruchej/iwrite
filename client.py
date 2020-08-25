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
from errors import IncorrectDataRecivedError, ReqFieldMissingError, ServerError
from message import Message
from metaclasses import ClientMaker

LOG = logging.getLogger("client")
MSG = Message()


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


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def create_exit_message(self):
        """Функция создаёт словарь с сообщением о выходе"""
        return {
            s.KEY_ACTION: s.ACTION_EXIT,
            s.KEY_TIME: time.time(),
            s.KEY_ACCOUNT_NAME: self.account_name,
        }

    def create_message(self):
        to = input("Введите получателя сообщения: ")
        message = input("Введите сообщение для отправки: ")
        message_dict = {
            s.KEY_ACTION: s.ACTION_MESSAGE,
            s.KEY_FROM: self.account_name,
            s.KEY_TO: to,
            s.KEY_TIME: time.time(),
            s.KEY_MESSAGE: message,
        }
        LOG.debug(f"Сформирован словарь сообщения: {message_dict}")
        try:
            MSG.send(self.sock, message_dict)
            LOG.info(f"Отправлено сообщение для пользователя {to}")
        except:
            LOG.critical("Потеряно соединение с сервером.")
            exit(1)

    def run(self):
        def _exit():
            try:
                MSG.send(self.sock, self.create_exit_message())
            except:
                pass
            print("Завершение соединения.")
            LOG.info("Завершение работы по команде пользователя.")
            time.sleep(0.5)
            # break

        self.print_help()
        funcs = {
            "/msg": [
                self.create_message,
                " - отправить сообщение. Кому и текст будет запрошены отдельно.",
            ],
            "/help": [self.print_help, " - вывести подсказки по командам"],
            "/exit": [_exit, " - выход из программы"],
        }
        while True:
            command = input("Команда:")
            func = funcs[command][0]
            func(funcs)

    def print_help(self, funcs):
        for i in funcs:
            print(f"{i} {funcs[i][1]}")


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            try:
                message = MSG.get(self.sock)
                if (
                    s.KEY_ACTION in message
                    and message[s.KEY_ACTION] == s.ACTION_MESSAGE
                    and s.KEY_FROM in message
                    and s.KEY_TO in message
                    and s.ACTION_MESSAGE in message
                    and message[s.KEY_TO] == self.account_name
                ):
                    print(
                        f"\nПолучено сообщение от пользователя {message[s.KEY_FROM]}:\n{message[s.ACTION_MESSAGE]}"
                    )
                    LOG.info(
                        f"Получено сообщение от пользователя {message[s.KEY_FROM]}:\n{message[s.ACTION_MESSAGE]}"
                    )
                else:
                    LOG.error(f"Получено некорректное сообщение с сервера: {message}")
            except IncorrectDataRecivedError:
                LOG.error(f"Не удалось декодировать полученное сообщение.")
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


def main():
    print("Консольный месседжер. Клиентский модуль.")

    # Загружаем параметы коммандной строки
    server_address, server_port, client_name = arg_parser()

    # Если имя пользователя не было задано, необходимо запросить пользователя.
    if not client_name:
        client_name = input("Введите имя пользователя: ")
    else:
        print(f"Клиентский модуль запущен с именем: {client_name}")

    LOG.info(
        f"Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}"
    )

    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        MSG.send(transport, create_presence(client_name))
        answer = process_ans(MSG.get(transport))
        LOG.info(f"Установлено соединение с сервером. Ответ сервера: {answer}")
        print(f"Установлено соединение с сервером.")
    except json.JSONDecodeError:
        LOG.error("Не удалось декодировать полученную Json строку.")
        exit(1)
    except ServerError as error:
        LOG.error(f"При установке соединения сервер вернул ошибку: {error.text}")
        exit(1)
    except ReqFieldMissingError as missing_error:
        LOG.error(
            f"В ответе сервера отсутствует необходимое поле {missing_error.missing_field}"
        )
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        LOG.critical(
            f"Не удалось подключиться к серверу {server_address}:{server_port}, конечный компьютер отверг запрос на подключение."
        )
        exit(1)
    else:
        # Если соединение с сервером установлено корректно, запускаем клиенский процесс приёма сообщний
        module_reciver = ClientReader(client_name, transport)
        module_reciver.daemon = True
        module_reciver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        module_sender = ClientSender(client_name, transport)
        module_sender.daemon = True
        module_sender.start()
        LOG.debug("Запущены процессы")

        # Watchdog основной цикл, если один из потоков завершён, то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках, достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if module_reciver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == "__main__":
    main()
