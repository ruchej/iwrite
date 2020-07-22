# -*- coding: utf8 -*-

import sys

import client
import server
import settings as s


class Command:
    def runserver(self):
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
                listen_address = ""

        except IndexError:
            print(
                "После параметра 'a'- необходимо указать адрес, который будет слушать сервер."
            )
            sys.exit(1)
        server.create_socket(listen_address, listen_port)

    def client(self):
        """Загружаем параметы коммандной строки"""
        # client.py 192.168.1.2 8079

        try:
            if "-p" in sys.argv:
                server_port = int(sys.argv[sys.argv.index("-p") + 1])
            else:
                server_port = s.DEFAULT_PORT
            if server_port < 1024 or server_port > 65535:
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
                server_address = sys.argv[sys.argv.index("-a") + 1]
            else:
                server_address = s.DEFAULT_IP_ADDRESS

        except IndexError:
            print(
                "После параметра 'a'- необходимо указать адрес, который будет слушать сервер."
            )
            sys.exit(1)
        if "-n" in sys.argv:
            name = sys.argv[sys.argv.index("-n") + 1]
        else:
            name = "Guest"
        client.create_socket(server_address, server_port, name)


def main():

    c = Command()
    if "runserver" in sys.argv:
        c.runserver()

    if "client" in sys.argv:
        c.client()


if __name__ == "__main__":
    main()
