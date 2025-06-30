import logging


def get_logger(name: str):
    logging.basicConfig(filename="./log.txt", level=logging.DEBUG)
    return logging.getLogger(name)