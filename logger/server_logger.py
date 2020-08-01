import logging
import os
import sys
import settings as s


FILENAME = os.path.join(s.LOG_DIR, "server.log")

LOG = logging.getLogger("server")
FILE_HANDLER = logging.FileHandler(FILENAME, encoding="utf-8")
FILE_HANDLER.setLevel(logging.DEBUG)

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setLevel(logging.INFO)

FORMATTER = logging.Formatter("%(levelname)-10s %(asctime)s %(message)s")
STREAM_HANDLER.setFormatter(FORMATTER)
FILE_HANDLER.setFormatter(FORMATTER)

LOG.addHandler(STREAM_HANDLER)
LOG.addHandler(FILE_HANDLER)
LOG.setLevel(logging.DEBUG)
