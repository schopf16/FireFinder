# -*- coding: utf-8 -*-

import os
import sys
import inspect
import logging
import colorama

from enum import Enum
from termcolor import colored
from logging.handlers import RotatingFileHandler

colorama.init(autoreset=True)


class DebugLevel(str, Enum):
    Debug    = "Debug"
    Info     = "Info"
    Warning  = "Warning"
    Error    = "Error"
    Critical = "Critical"


class Logger(object):
    def __init__(self, verbose, file_path, no_color=False, exit_zero=False):
        self.verbose = verbose
        self._file_path = file_path
        self._no_color = no_color
        self._logger = None
        self._old_except_hook = None
        self._exit_zero = exit_zero

        # Start logger
        self._init()

    def _init(self):
        try:
            path, file = os.path.split(self._file_path)
            if not os.path.exists(path):
                os.makedirs(path)

            # If log file already exist, it shall exchange, not append
            if os.path.isfile(self._file_path):
                os.remove(self._file_path)

            # Create a rotating file handler to overwrite old log files
            my_handler = RotatingFileHandler(self._file_path, mode='a', maxBytes=5 * 1024 * 1024, backupCount=5)
            app_log = logging.getLogger('root')

            log_formatter = logging.Formatter('%(asctime)s - %(message)s')
            my_handler.setFormatter(log_formatter)

            # Setting up the logging level
            if self.verbose:
                my_handler.setLevel(logging.DEBUG)
                app_log.setLevel(logging.DEBUG)
            else:
                my_handler.setLevel(logging.INFO)
                app_log.setLevel(logging.INFO)

            app_log.addHandler(my_handler)

            # Redirect python exception handler to my method
            self._old_except_hook = sys.excepthook
            sys.excepthook = self._except_hook

        except Exception as e:
            self._print_console("LOGGING DISABLED: {}".format(e), dbg_lvl=DebugLevel.Warning)
            app_log = None  # Disable logging

        # return instance for logging
        self._logger = app_log

    def _except_hook(self, exctype, value, traceback):
        msg = "Unhandled exception occurred"

        if self._logger:
            self._logger.exception(msg)

        if self._no_color:
            print(msg)
        else:
            print(colored(msg, color="red"))

        # Don't need another copy of traceback on stderr
        if self._old_except_hook != sys.__excepthook__:
            self._old_except_hook(exctype, value, traceback)

        # Exit depend on the users wish
        if self._exit_zero:
            exit(0)
        else:
            exit(1)

    def _print_console(self, msg, dbg_lvl):
        if self.verbose:
            if self._no_color:
                print(msg)
            else:
                if dbg_lvl == DebugLevel.Debug:
                    color = "grey"
                elif dbg_lvl == DebugLevel.Info:
                    color = "green"
                elif dbg_lvl == DebugLevel.Warning:
                    color = "cyan"
                elif dbg_lvl == DebugLevel.Error:
                    color = "yellow"
                else:
                    color = "red"
                print(colored(msg, color=color))

    @staticmethod
    def _sanitize_msg(msg, dbg_lvl, *args, **kwargs):

        # Get the pre-previous frame in the stack, otherwise it would be this function!!!
        func = inspect.currentframe().f_back.f_back.f_code
        filename = func.co_filename.split('\\')[-1]
        lineno = func.co_firstlineno
        funcname = func.co_name
        log = "[{}:{} - {:>40}() ] {:>9}: {}".format(filename, lineno, funcname, dbg_lvl.upper(), msg)

        if len(args[0]) or len(args[1]):
            log = "{} {}".format(log, args)
        if kwargs:
            log = "{} {}".format(log, kwargs)
        return log

    def debug(self, msg, *args, **kwargs):
        dbg_lvl = DebugLevel.Debug
        if self._logger:
            log = self._sanitize_msg(msg, dbg_lvl, args, kwargs)
            self._logger.debug(log)
        self._print_console(msg=msg, dbg_lvl=dbg_lvl)

    def info(self, msg, *args, **kwargs):
        dbg_lvl = DebugLevel.Info
        if self._logger:
            log = self._sanitize_msg(msg, dbg_lvl, args, kwargs)
            self._logger.info(log)
        self._print_console(msg=msg, dbg_lvl=dbg_lvl)

    def warning(self, msg, *args, **kwargs):
        dbg_lvl = DebugLevel.Warning
        if self._logger:
            log = self._sanitize_msg(msg, dbg_lvl, args, kwargs)
            self._logger.warning(log)
        self._print_console(msg=msg, dbg_lvl=dbg_lvl)

    def error(self, msg, *args, **kwargs):
        dbg_lvl = DebugLevel.Error
        if self._logger:
            log = self._sanitize_msg(msg, dbg_lvl, args, kwargs)
            self._logger.error(log)
        self._print_console(msg=msg, dbg_lvl=dbg_lvl)

    def critical(self, msg, *args, **kwargs):
        dbg_lvl = DebugLevel.Critical
        if self._logger:
            log = self._sanitize_msg(msg, dbg_lvl, args, kwargs)
            self._logger.critical(log)
        self._print_console(msg=msg, dbg_lvl=dbg_lvl)
