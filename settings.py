import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Порт по умолчанию для сетевого ваимодействия
DEFAULT_PORT = 7777
# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = "127.0.0.1"
# Максимальная очередь подключений
MAX_CONNECTIONS = 5
# Максимальная длинна сообщения в байтах
MAX_PACKAGE_LENGTH = 1024
# Кодировка проекта
ENCODING = "utf-8"

# Прококол JIM основные ключи:
KEY_ACTION = "action"
KEY_TIME = "time"
KEY_USER = "user"
KEY_ACCOUNT_NAME = "account_name"
KEY_TO = "to"
KEY_FROM = "from"
KEY_MESSAGE = "message"
KEY_RESPONSE = "response"
KEY_ERROR = "error"

ACTION_EXIT = "exit"
ACTION_MESSAGE = "msg"
ACTION_PRESENCE = "presence"

LOG_DIR = os.path.join(BASE_DIR, "log")

# Словари - ответы:
# 200
RESPONSE_200 = {KEY_RESPONSE: 200}
# 400
RESPONSE_400 = {
    KEY_RESPONSE: 400,
    KEY_ERROR: None
}
