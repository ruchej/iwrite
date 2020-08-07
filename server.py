import argparse
import json
import logging
import select
import socket
import sys
import time

import settings as s
from decorators import Log
from logger import server_logger
from message import Message

LOG = logging.getLogger("server")


@Log()
def arg_parse():
    """Парсер аргументов командной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", default=s.DEFAULT_IP_ADDRESS, type=str, nargs="?")
    parser.add_argument("-p", default=s.DEFAULT_PORT, type=int, nargs="?")
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


@Log()
def client_message_handler(message, messages_list, client):
    """
    Message handler from clients, accepts dictionary -
    message from the client, checks correctness,
    returns the response dictionary for the client

    """
    LOG.debug(f"Разбираем сообщение: {message}")
    msg = Message()
    if (
        s.KEY_ACTION in message
        and message[s.KEY_ACTION] == s.ACTION_PRESENCE
        and s.KEY_TIME in message
        and s.KEY_USER in message
        and message[s.KEY_USER][s.KEY_ACCOUNT_NAME] != ""
    ):
        msg.send(client, {s.KEY_RESPONSE: 200})
        return
    elif (
        s.KEY_ACTION in message
        and message[s.KEY_ACTION] == s.ACTION_MESSAGE
        and s.KEY_TIME in message
        and s.KEY_MESSAGE in message
    ):
        messages_list.append((message[s.KEY_ACCOUNT_NAME], message[s.KEY_MESSAGE]))
    else:
        return msg.send(client, {s.KEY_RESPONSE: 400, s.KEY_ERROR: "Bad Request"})


@Log()
def create_socket(listen_addr, listen_port):
    msg = Message()
    clients = []
    messages = []
    # Готовим сокет

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    LOG.info(f"Подключаемся к адресу: {listen_addr}: {listen_port}")
    transport.bind((listen_addr, listen_port))
    # Слушаем порт
    transport.listen(s.MAX_CONNECTIONS)

    LOG.info(
        f"The server listens {listen_addr}: {listen_port}\nPress CTRL + C to stop the server\n"
    )
    while True:
        try:
            client, client_address = transport.accept()
        except KeyboardInterrupt:
            print("\nThe server is stopped")
            client.close()
            sys.exit(1)
        else:
            LOG.info(f"Установлено соедение с ПК {client_address}")
            clients.append(client)

        recv_data_lst = []
        send_data_lst = []
        err_lst = []

        # Проверяем на наличие ждущих клиентов
        try:
            if clients:
                recv_data_lst, send_data_lst, err_lst = select.select(
                    clients, clients, [], 0
                )
        except OSError:
            pass

        # принимаем сообщения и если там есть сообщения,
        # кладём в словарь, если ошибка, исключаем клиента.
        if recv_data_lst:
            for client_with_message in recv_data_lst:
                try:
                    client_message_handler(
                        msg.get(client_with_message), messages, client_with_message
                    )
                except:
                    LOG.info(
                        f"Клиент {client_with_message.getpeername()} "
                        f"отключился от сервера."
                    )
                    clients.remove(client_with_message)

        # Если есть сообщения для отправки и ожидающие клиенты, отправляем им сообщение.
        if messages and send_data_lst:
            message = {
                s.KEY_ACTION: s.ACTION_MESSAGE,
                s.KEY_FROM: messages[0][0],
                s.KEY_TIME: time.time(),
                s.KEY_MESSAGE: messages[0][1],
            }
            del messages[0]
            for waiting_client in send_data_lst:
                try:
                    msg.send(waiting_client, message)
                except:
                    LOG.info(
                        f"Клиент {waiting_client.getpeername()} отключился от сервера."
                    )
                    clients.remove(waiting_client)


@Log()
def main():
    """Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию"""
    listen_addr, listen_port = arg_parse()

    LOG.info(
        f"Запущен сервер, порт для подключений: {listen_port}, "
        f"адрес с которого принимаются подключения: {listen_addr}. "
        f"Если адрес не указан, принимаются соединения с любых адресов."
    )
    create_socket(listen_addr, listen_port)


if __name__ == "__main__":
    main()
