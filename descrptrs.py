import logging

LOG = logging.getLogger("server")


class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            LOG.critical(
                f"Попытка запуска сервера с указанием неподходящего порта {value}. Допустимы адреса с 1024 до 65535."
            )
            exit(1)
        # Если порт прошел проверку, добавляем его в список атрибутов экземпляра
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
