#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import logging
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

FORMATTER = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(funcName)s:%(lineno)d — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
MAX_LOG_FILE_SIZE = 2 * math.pow(10, 6)  # 2 MB


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(logfile):
    file_handler = RotatingFileHandler(
        filename=logfile, maxBytes=MAX_LOG_FILE_SIZE, backupCount=10
    )
    file_handler.setFormatter(FORMATTER)
    return file_handler


def make_logger(logger_name, logfile):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(logfile))
    logger.propagate = False
    return logger


def get_logger(logger_name, log_prefix):
    curr_date_time = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    log_dir = "logs"
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logfile_name = log_prefix + "-" + curr_date_time + ".log"
    logfile_path = os.path.join(log_dir, logfile_name)
    return make_logger(logger_name=logger_name, logfile=logfile_path)
