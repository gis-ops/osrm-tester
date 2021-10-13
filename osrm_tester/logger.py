import logging
from logging import CRITICAL, INFO, DEBUG, NOTSET

from .__version__ import __title__

LOGGER = logging.getLogger(__title__)
LOGGER.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
LOGGER.addHandler(handler)


class LOG_COLORS:

    CYAN = "\033[96m\033[1m"
    BLUE = "\033[94m\033[1m"
    BOLD = "\033[1m"
    END = "\033[0m"


def map_verbosity(verbosity):
    level: int = NOTSET
    if verbosity == 0:
        level = CRITICAL
    elif verbosity == 1:
        level = INFO
    elif verbosity >= 2:
        level = DEBUG
    return level
