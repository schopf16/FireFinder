# -*- coding: utf-8 -*-

import os
import time
import shutil
import threading
import configparser

from pathlib import Path
from firefinder.util_screen import GuiHandler, get_screen_obj_from_string
from firefinder.util_logger import Logger


def get_screen_config(screen_name: str, config_obj: configparser.ConfigParser, basedir: str):
    screen_name = screen_name.lower()
    screen_config = dict()

    if screen_name == "event":
        equipment_list = []
        for x in range(1, 11):
            option_name = f"equipment_{x}"
            picture = config_obj.get('Response', option_name, fallback=None)
            if picture:
                equipment_list.append(picture)

        image_left = config_obj.get('Event', 'picture_left', fallback="")
        image_right = config_obj.get('Event', 'picture_right', fallback="")
        screen_config["alarm_message"]         = config_obj.get('Event', 'message_full', fallback="")
        screen_config["image_left"]            = os.path.join(basedir, image_left)
        screen_config["image_right"]           = os.path.join(basedir, image_right)
        screen_config["show_progress_bar"]     = config_obj.getboolean('Progress', 'show_progress', fallback=False)
        screen_config["progress_bar_duration"] = config_obj.getint('Progress', 'progress_time', fallback=7*60)
        screen_config["sound_file"]            = config_obj.get('Sound', 'sound', fallback="")
        screen_config["sound_repeat"]          = config_obj.getint('Sound', 'repeat', fallback=1)
        screen_config["equipment_list"]        = equipment_list

    return screen_config


class FileWatch(object):
    def __init__(self, file_path: str, callback: GuiHandler.set_screen_and_config, logger: Logger, backup_file=False,
                 backup_path="."):
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\FileWatch.log")
        self.backup_enable = backup_file
        self.backup_path = Path(backup_path)

        if self.backup_enable and not self.backup_path.exists():
            logger.info(f"'{self.backup_path.resolve()}' is not existing, create folder")
            os.makedirs(self.backup_path.resolve())

        assert callback.__func__ is GuiHandler.set_screen_and_config, "Wrong callback type"
        self.callback = callback
        self.file_path = file_path
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._do_watch,
                                        daemon=True,
                                        name="FileWatch",
                                        args=(self.file_path, self.callback, self.logger, self.backup_enable, self.backup_path))
        self._thread.start()

    def _do_backup(self):
        path_obj = Path(self.file_path)

        file_stem = path_obj.stem
        file_suffix = path_obj.suffix
        timestr = time.strftime("_%Y%m%d_%H%M%S")
        new_file_name = file_stem + timestr + file_suffix

        shutil.copyfile(path_obj.resolve(), os.path.join(self.backup_path.resolve(), new_file_name))

    @staticmethod
    def _do_watch(file_path, callback, logger, do_backup: bool, backup_path: Path):
        # catch exceptions in this thread
        threading.excepthook = logger.thread_except_hook

        path_obj = Path(file_path)

        last_modified_time = os.stat(path_obj.resolve()).st_mtime
        logger.info(f"Start watching file '{path_obj.resolve()}' for modification")

        is_file_available = True

        while True:
            time.sleep(1)
            try:
                file_time = os.stat(path_obj.resolve()).st_mtime

                if not is_file_available:
                    is_file_available = True
                    logger.error(f"File '{path_obj.resolve()}' is available again")

            except FileNotFoundError:
                # If the file does not exist (perhaps it gets deleted before updated)
                file_time = last_modified_time

                if is_file_available:
                    is_file_available = False
                    logger.error(f"File '{path_obj.resolve()}' no longer available")

            if file_time != last_modified_time:
                last_modified_time = file_time

                logger.debug("FileModifiedEvent raised")

                if do_backup:
                    logger.info(f"Backup '{path_obj.resolve()}' to '{backup_path.resolve()}'")
                    file_stem   = path_obj.stem
                    file_suffix = path_obj.suffix
                    time_str    = time.strftime("_%Y%m%d_%H%M%S")
                    new_file_name = file_stem + time_str + file_suffix
                    shutil.copyfile(path_obj.resolve(), os.path.join(backup_path.resolve(), new_file_name))

                config_obj = configparser.ConfigParser()
                try:
                    # Try UTF-8 without BOM first
                    config_obj.read(path_obj.resolve(), encoding='utf-8')
                except configparser.MissingSectionHeaderError:
                    # If failing, try UTF-8 with BOM
                    config_obj.read(path_obj.resolve(), encoding='utf-8-sig')

                screen_name = config_obj.get("General", "show", fallback=None)
                if screen_name is None or screen_name == "":
                    logger.error(f"Failed to read variable \"show\" in section [General], read value is '{screen_name}")
                    logger.info("Set screen_name to default 'off'")
                    screen_name = 'off'

                screen_obj = get_screen_obj_from_string(screen_name=screen_name)
                if screen_obj is None:
                    logger.error(f"Could not assign a valid screen to '{screen_name}'")
                    return

                screen_config = get_screen_config(screen_name = screen_name,
                                                  config_obj  = config_obj,
                                                  basedir     = str(path_obj.parent))
                callback(screen_name=screen_obj, screen_config=screen_config)

