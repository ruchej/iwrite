import argparse
import logging
import select
import socket
import sys
import time

import settings as s
from decorators import Log
from logger import server_logger
from message import Message
from descrptrs import Port
from metaclasses import ServerMaker

LOG = logging.getLogger("server")
MSG = Message()


@Log()
def arg_parse():
    """Парсер аргументов командной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", default=s.DEFAULT_PORT, type=int, nargs="?")
    parser.add_argument("-a", default="", type=str, nargs="?")
    namespace = parser.parse_args(sys.argv[1:])
    listen_addr = namespace.a
    listen_port = namespace.p
    if not 1023 < listen_port < 65536:
        LOG.critical(
            f"Попытка запуска сервера с указанием неподходящего порта "
            f"{listen_port}. Допустимы адреса с 1024 до 65535."
        )
        sys.exit(1)

    return listen_addr, listen_port


class Server(metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_addr, listen_port):
        self.addr = listen_addr
        self.port = listen_port
        self.clients = []
        self.messages = []
        self.names = dict()

    def init_socket(self):
        LOG.info(
            f"Запущен сервер, порт для подключений: {self.port} , "
            f"адрес с которого принимаются подключения: {self.addr}."
            f"Если адрес не указан, принимаются соединения с любых адресов."
        )

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)
        self.sock = transport
        self.sock.listen()

    def main_loop(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                LOG.info(f"Установлено соедение с ПК {client_address}")
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(
                        self.clients, self.clients, [], 0
                    )
            except OSError:
                pass

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.client_message_handler(
                            MSG.get(client_with_message), client_with_message
                        )
                    except:
                        LOG.info(
                            f"Клиент {client_with_message.getpeername()} отключился от сервера."
                        )
                        self.clients.remove(client_with_message)
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except:
                    LOG.info(
                        f"Связь с клиентом с именем {message[s.KEY_TO]} была потеряна"
                    )
                    self.clients.remove(self.names[message[s.KEY_TO]])
                    del self.names[message[s.KEY_TO]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        if (
            message[s.KEY_TO] in self.names
            and self.names[message[s.KEY_TO]] in listen_socks
        ):
            MSG.send(self.names[message[s.KEY_TO]], message)
            LOG.info(
                f"Отправлено сообщение пользователю {message[s.KEY_TO]} от пользователя {message[s.KEY_FROM]}."
            )
        elif (
            message[s.KEY_TO] in self.names
            and self.names[message[s.KEY_TO]] not in listen_socks
        ):
            raise ConnectionError
        else:
            LOG.error(
                f"Пользователь {message[s.KEY_TO]} не зарегистрирован на сервере, отправка сообщения невозможна."
            )

    def client_message_handler(self, message, client):
        """
        Message handler from clients, accepts dictionary -
        message from the client, checks correctness,
        returns the response dictionary for the client

        """
        LOG.debug(f"Разбираем сообщение: {message}")
        if (
            s.KEY_ACTION in message
            and message[s.KEY_ACTION] == s.ACTION_PRESENCE
            and s.KEY_TIME in message
            and s.KEY_USER in message
        ):
            if message[s.KEY_USER][s.KEY_ACCOUNT_NAME] not in self.names.keys():
                self.names[message[s.KEY_USER][s.KEY_ACCOUNT_NAME]] = client
                MSG.send(client, {s.RESPONSE_200})
            else:
                response = s.RESPONSE_400
                response[s.KEY_ERROR] = "Имя пользователя уже занято."
                MSG.send(client, response)
                self.clients.remove(client)
                client.close()
            return
        # Если это сообщение, то добавляем его в очередь сообщений.
        # Ответ не требуется.
        elif (
            s.KEY_ACTION in message
            and message[s.KEY_ACTION] == s.ACTION_MESSAGE
            and s.KEY_TIME in message
            and s.KEY_TO in message
            and s.KEY_FROM in message
            and s.KEY_MESSAGE in message
        ):
            self.messages.append(message)
            return
        # Если клиент выходит
        elif (
            s.KEY_ACTION in message
            and message[s.KEY_ACTION] == s.ACTION_EXIT
            and s.KEY_ACCOUNT_NAME in message
        ):
            self.clients.remove(self.names[message[s.KEY_ACCOUNT_NAME]])
            self.names[message[s.KEY_ACCOUNT_NAME]].close()
            del self.names[message[s.KEY_ACCOUNT_NAME]]
            return
        # Иначе отдаём Bad request
        else:
            response = s.RESPONSE_400
            response[s.KEY_ERROR] = "Запрос не корректен"
            MSG.send(client, response)
            return


@Log()
def main():
    """Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию"""
    listen_addr, listen_port = arg_parse()
    server = Server(listen_addr, listen_port)
    server.main_loop()


if __name__ == "__main__":
    main()
