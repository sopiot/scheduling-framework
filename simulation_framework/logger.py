from simulation_framework.typing import *
from simulation_framework.exceptions import *
from termcolor import cprint, colored
from rich.console import Console

import logging
import os
import time
import re
import traceback


class MXTestLogLevel(Enum):
    PASS = 'PASS'
    WARN = 'WARN'
    INFO = 'INFO'
    FAIL = 'FAIL'
    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class MicrosecondFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = datetime.now().strftime(datefmt)
        else:
            t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
            s = "%s,%03d" % (t, record.msecs)
        return s


class MXLogger:

    class LoggingMode(Enum):
        ALL = auto()
        FILE = auto()
        CONSOLE = auto()
        OFF = auto()

        UNDEFINED = 'UNDEFINED'

        def __str__(self):
            return self.value

        @classmethod
        def get(cls, name: str):
            try:
                return cls[name.upper()]
            except Exception:
                return cls.UNDEFINED

    class PrintMode(Enum):
        DEBUG = auto()
        INFO = auto()
        WARN = auto()
        ERROR = auto()
        CRITICAL = auto()

        UNDEFINED = 'UNDEFINED'

        def __str__(self):
            return self.value

        @classmethod
        def get(cls, name: str):
            try:
                return cls[name.upper()]
            except Exception:
                return cls.UNDEFINED

    def __init__(self, file_name: str = f'mqtt_message_{time.strftime("%Y%m%d%H%M", time.localtime(time.time()))}.log', file_path: str = f'./log', logging_mode: LoggingMode = LoggingMode.ALL) -> None:
        self._file_name = file_name
        self._file_path = file_path
        self._logging_mode = logging_mode

        self._console_logger = None
        self._file_logger = None

    def start(self):
        formatter = MicrosecondFormatter('[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S.%f')
        level_list = [logging.DEBUG, logging.INFO,
                      logging.WARN, logging.ERROR, logging.CRITICAL]

        if self._logging_mode == self.LoggingMode.ALL:
            os.makedirs('/'.join(self._file_path.rstrip('/').split('/')), exist_ok=True)

            file_logger = logging.getLogger('file_logger')
            file_logger.setLevel(logging.DEBUG)
            file_handler_list = [logging.FileHandler(filename='/'.join([self._file_path, self._file_name]), mode='a', encoding='utf-8') for _ in range(5)]

            for level, file_handler in zip(level_list, file_handler_list):
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                file_logger.addHandler(file_handler)

            self._file_logger = file_logger

            console_logger = logging.getLogger('console_logger')
            console_logger.setLevel(logging.DEBUG)

            console_handler_list = [logging.StreamHandler() for _ in range(5)]

            for level, console_handler in zip(level_list, console_handler_list):
                console_handler.setLevel(level)
                console_handler.setFormatter(formatter)
                console_logger.addHandler(console_handler)

            self._console_logger = console_logger
        elif self._logging_mode == self.LoggingMode.FILE:
            os.makedirs('/'.join(self._file_path.rstrip('/').split('/')), exist_ok=True)

            file_logger = logging.getLogger('file_logger')
            file_logger.setLevel(logging.DEBUG)
            file_handler_list = [logging.FileHandler(filename='/'.join([self._file_path, self._file_name]), mode='a') for _ in range(5)]

            for level, file_handler in zip(level_list, file_handler_list):
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                file_logger.addHandler(file_handler)

            self._file_logger = file_logger
        elif self._logging_mode == self.LoggingMode.CONSOLE:
            console_logger = logging.getLogger('console_logger')
            console_logger.setLevel(logging.DEBUG)

            console_handler_list = [logging.StreamHandler() for _ in range(5)]

            for level, console_handler in zip(level_list, console_handler_list):
                console_handler.setLevel(level)
                console_handler.setFormatter(formatter)
                console_logger.addHandler(console_handler)

            self._console_logger = console_logger
        else:
            pass

    def _remove_color(self, msg: str) -> str:
        ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
        msg = ansi_escape.sub('', msg)
        return msg

    def select_by_logger_name(self, logger_name: str, logging_func: Callable, msg: List[str], color: str):
        if logger_name == 'console_logger':
            logging_func(colored(msg, color))
        elif logger_name == 'file_logger':
            logging_func(self._remove_color(msg))

    def select_by_print_mode(self, logger: logging.Logger, msg: List[str], color: str, print_mode: PrintMode = PrintMode.DEBUG):
        if print_mode == self.PrintMode.DEBUG:
            self.select_by_logger_name(logger.name, logger.debug, msg, color)
        elif print_mode == self.PrintMode.INFO:
            self.select_by_logger_name(logger.name, logger.info,  msg, color)
        elif print_mode == self.PrintMode.WARN:
            self.select_by_logger_name(logger.name, logger.warn, msg, color)
        elif print_mode == self.PrintMode.ERROR:
            self.select_by_logger_name(logger.name, logger.error,  msg, color)
        elif print_mode == self.PrintMode.CRITICAL:
            self.select_by_logger_name(logger.name, logger.critical,  msg, color)
        else:
            raise UnsupportedError(f'Not supported print mode: {print_mode}')

    def print(self, msg: List[str], color: str = None, mode: PrintMode = PrintMode.DEBUG):
        try:
            if self._logging_mode == self.LoggingMode.ALL:
                self.select_by_print_mode(self._console_logger, msg, color, mode)
                self.select_by_print_mode(self._file_logger, msg, color, mode)
            elif self._logging_mode == self.LoggingMode.FILE:
                self.select_by_print_mode(self._file_logger, msg, color, mode)
            elif self._logging_mode == self.LoggingMode.CONSOLE:
                self.select_by_print_mode(self._console_logger, msg, color, mode)
            elif self._logging_mode == self.LoggingMode.OFF:
                pass
            else:
                raise UnsupportedError(f'Not supported logging mode: {mode}')
        except Exception as e:
            print(f'Unknown exception error : {str(e)}')


base_logger: MXLogger = None


def START_LOGGER(whole_log_path: str = None, logging_mode: MXLogger.LoggingMode = MXLogger.LoggingMode.ALL):
    global base_logger

    if not whole_log_path:
        whole_log_path = f'./log/mqtt_message_{time.strftime("%Y%m%d%H%M", time.localtime(time.time()))}.log'
    else:
        whole_log_path = f'{whole_log_path.rsplit(".", 1)[0]}_{time.strftime("%Y%m%d%H%M", time.localtime(time.time()))}.log'
    os.makedirs(os.path.dirname(whole_log_path), exist_ok=True)
    log_name = os.path.basename(whole_log_path)
    log_path = os.path.dirname(whole_log_path)

    if base_logger is None:
        base_logger = MXLogger(log_name, log_path, logging_mode)
        base_logger.start()
        # cprint('logger is started!', 'green')


def MXLOG_DEBUG(msg: List[str], color: str = None, mode: MXLogger.PrintMode = MXLogger.PrintMode.DEBUG):
    global base_logger
    if base_logger is not None:
        base_logger.print(msg, color, mode)
    else:
        cprint('MXLogger is not initialized... start logger init', 'red')
        START_LOGGER()


# FIXME: Remove Exception parameter(e)
def MXTEST_LOG_DEBUG(msg: str, error: MXTestLogLevel = MXTestLogLevel.PASS, color: str = None, progress: float = None):
    # error = 0  : PASS ✅
    # error = 1  : WARN ⚠ -> use b'\xe2\x9a\xa0\xef\xb8\x8f'.decode()
    # error = -1 : FAIL ❌
    log_msg = ''
    WARN_emoji = b'\xe2\x9a\xa0\xef\xb8\x8f'.decode()
    progress_status = ''
    if progress:
        progress_status = f'[{progress*100:8.3f}%]'

    if error == MXTestLogLevel.PASS:
        log_msg = f'{progress_status} [PASS✅] {msg}'
        MXLOG_DEBUG(log_msg, 'green' if not color else color)
    elif error == MXTestLogLevel.WARN:
        log_msg = f'{progress_status} [WARN{WARN_emoji} ] {msg}'
        MXLOG_DEBUG(log_msg, 'yellow' if not color else color)
    elif error == MXTestLogLevel.INFO:
        log_msg = f'{progress_status} [INFOℹ️ ] {msg}'
        MXLOG_DEBUG(log_msg, 'cyan' if not color else color)
    elif error == MXTestLogLevel.FAIL:
        log_msg = f'{progress_status} [FAIL❌] {msg}'
        MXLOG_DEBUG(log_msg, 'red' if not color else color)


def print_error(show_locals: bool = True):
    Console().print_exception(show_locals=show_locals)
    # traceback_msg = traceback.format_exc()
    # MXLOG_DEBUG(f'Traceback message : {traceback_msg}\nError: {e}', 'red')
