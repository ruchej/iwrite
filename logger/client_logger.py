import logging
import os

import settings as s


FILENAME = os.path.join(s.LOG_DIR, "client.log")

LOG = logging.getLogger("client")
FILE_HANDLER = logging.FileHandler(FILENAME, encoding="utf-8")
FILE_HANDLER.setLevel(logging.DEBUG)
FORMATTER = logging.Formatter("%(levelname)-10s %(asctime)s %(message)s")
FILE_HANDLER.setFormatter(FORMATTER)
LOG.addHandler(FILE_HANDLER)
LOG.setLevel(logging.DEBUG)
