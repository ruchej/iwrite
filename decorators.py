import inspect
import logging
import sys
import traceback

import logger.client_logger
import logger.server_logger

if sys.argv[0].find("client") == -1:
    LOGGER = logging.getLogger("server")
else:
    LOGGER = logging.getLogger("client")


class Log:
    def __call__(self, func):
        def wrap(*args, **kwargs):
            func_res = func(*args, **kwargs)
            LOGGER.debug(
                f"Была вызавана функция {func.__name__} с параметрами {args}, {kwargs}."
                f"Вызов из модуля {func.__module__}. Вызов из функции "
                f"{traceback.format_stack()[0].strip().split()[-1]}."
                f"Вызов из функции {inspect.stack()[1][3]}"
            )
            return func_res

        return wrap
