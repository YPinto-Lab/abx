import logging
from .config import DEBUG

_LOGGER = None

def get_logger(name="trend", debug: bool = None):
    """Return a configured logger that writes to trend_debug.log and stdout.

    This is a convenience wrapper so existing code can call get_logger().debug(...)
    or use it as a drop-in for the previous `debug` function.
    """
    global _LOGGER
    if debug is None:
        debug = DEBUG

    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Avoid adding duplicate handlers in interactive runs
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

        # file handler
        fh = logging.FileHandler("trend_debug.log", mode="w")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        # console handler (only for debug)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG if debug else logging.INFO)
        ch.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(ch)

    _LOGGER = logger
    return _LOGGER
