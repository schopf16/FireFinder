# -*- coding: utf-8 -*-

"""
    This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
    To view a copy of this license, visit https://creativecommons.org/licenses/by-sa/4.0/.

    You are free to share and adapt this work for any purpose, even commercially, as long as you give appropriate
    credit to the original author and distribute any derivatives under the same license. By sharing and adapting
    this work, you agree to make any resulting derivative works available under the same license. This means that
    others may use, share, and adapt your work, as long as they also give you credit and release their derivative
    works under the same license.

    By licensing this work under a copyleft license, the author hopes to promote collaboration, sharing, and
    innovation in the creative community, and to ensure that the benefits of this work are shared with as many
    people as possible.
"""

import os
import time
import configparser

from firefinder.util_screen import GuiHandler, Screen
from firefinder.util_logger import Logger
from firefinder.util_filehandler import FileWatch


class ConfigFile(object):

    def __init__(self, logger, **kwargs):

        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        self._config_file = kwargs.get('ini_file', config_path)
        self._logger = logger
        self.successful = False

        # check if the passed file exist. Do not try to parse the file if it cannot be located
        if isinstance(self._config_file, str) and os.path.isfile(self._config_file):
            self._config = configparser.ConfigParser()
            self._config.read(self._config_file)

            # [FileObserver]
            self.file_observer = {
                "observing_path": self._get_value('FileObserver', 'observing_path', default=""),
                "observing_file": self._get_value('FileObserver', 'observing_file', default="")
            }

            # [Visual] and [Power]
            self.gui_settings = {
                "full_screen_enable"              : self._get_boolean('Visual', 'fullscreen', default=False),
                "switch_screen_delay_after_start" : self._get_int('Visual', 'switchScreenAfterStart', default=0),
                "switch_to_screen_after_start"    : self._get_value('Visual', 'switchToScreenAfterStart', default='Off'),
                "switch_screen_delay_after_event" : self._get_int('Visual', 'switchScreenAfterEvent', default=0),
                "switch_to_screen_after_event"    : self._get_value('Visual', 'switchToScreenAfterEvent', default='Off'),
                "cec_enable"                      : self._get_boolean('Power', 'cec_enable', default=False),
                "standby_enable"                  : self._get_boolean('Power', 'stdby_enable', default=False)
            }

            # [SplashScreen]
            self.splash_screen = {
                "company_path_logo"      : self._get_value('Visual', 'company_path_logo', default="")
            }

            # [Slideshow]
            self.slideshow_screen = {
                "slideshow_path"         : self._get_value('Slideshow', 'slideshow_path', default=""),
                "fade_over_background"   : self._get_boolean('Slideshow', 'fade_over_background', default=True),
                "seconds_between_images" : self._get_int('Slideshow', 'seconds_between_images', default=60),
                "sort_alphabetically"    : self._get_boolean('Slideshow', 'sort_alphabetically', default=True),
                "show_header_bar"        : self._get_boolean('Slideshow', 'show_header_bar', default=True),
                "company_path_logo"      : self._get_value('Visual', 'company_path_logo', default=""),
                "company_name"           : self._get_value('Visual', 'company_name', default="")
            }

            # [Clock]
            self.clock_screen = {
                "show_second_hand"     : self._get_boolean("Clock", "show_second_hand", default=True),
                "show_minute_hand"     : self._get_boolean("Clock", "show_minute_hand", default=True),
                "show_hour_hand"       : self._get_boolean("Clock", "show_hour_hand", default=True),
                "show_digital_time"    : self._get_boolean("Clock", "show_digital_time", default=True),
                "show_digital_date"    : self._get_boolean("Clock", "show_digital_date", default=True),
                "show_digital_seconds" : self._get_boolean("Clock", "show_digital_seconds", default=True)
            }

            # [Event]
            self.event_screen = {
                "show_alarm_message"    : self._get_boolean("Event", "show_alarm_message", default=True),
                "show_progress_bar"     : self._get_boolean("Event", "show_progress_bar", default=False),
                "show_response_order"   : self._get_boolean("Event", "show_response_order", default=False),
                "path_sound_folder"     : self._get_value('Event', 'path_sounds', default=""),
                "sound_file_force"      : self._get_value('Event', 'force_sound_file', default=""),
                "sound_repeat_force"    : self._get_int('Event', 'force_repetition', default=1)
            }

            self.successful = True

        else:
            self._logger.critical("Failed loading ini-file at expected path: '{}'".format(self._config_file))

    def _has_section(self, section):
        """ Check if the given section is listed in the ini-file

        :param section: Name of the section that should be checked
        :return: True if available in the ini-file, False in any other case
        """
        ret = self._config.has_section(section=section)
        if not ret:
            self._logger.info("Section {} not found".format(section))
        return ret

    def _has_option(self, section, option):
        """ Check if the option is listed in the given section of the ini-file

        :param section: Name of the section in the ini-file
        :param option:  Name of the option in the section
        :return: True if available in the ini-file, False in any other case
        """
        ret = self._config.has_option(section=section, option=option)

        if not ret:
            self._logger.info("Option {} in Section {} not found".format(option, section))
        return ret

    @staticmethod
    def _str_to_bool(txt):
        """
        Check if the value 'txt' is part of the TRUE_TABLE. If so, return True, else False
        """
        true_table = ['true', 'wahr', 'ja', '1', 't', 'y', 'yes', 'yeah', 'yup', 'sure', 'certainly', 'uh-huh', 'dude',
                      'haan']
        if str(txt).lower() in true_table:
            return True
        else:
            return False

    def _get_sections(self):
        """Return a list of section names, excluding [DEFAULT]"""
        return self._config.sections()

    def _get_options(self, section):
        """Return a list of option names for the given section name."""
        return self._config.options(section=section)

    def _get_value(self, section, option, default=None, expect_boolean=False, expect_int=False):
        """ Get the value from the option

        :param section:        Name of the section in the ini-file
        :param option:         Name of the option in the section
        :param expect_boolean: If True, check value with TRUE_TABLE and set either to True or False
        :return:               value of the option, None empty
        """
        value = default

        # Check if section is available
        if self._config.has_section(section=section):

            # Check if option is available
            if self._config.has_option(section=section, option=option):
                if expect_boolean:
                    value = self._config.getboolean(section=section, option=option)
                elif expect_int:
                    value = self._config.getint(section=section, option=option)
                else:
                    value = self._config.get(section=section, option=option)
            else:
                self._logger.debug("Option {} in section {} is not available".format(option, section))
        else:
            self._logger.debug("Section {} is not available".format(section))

        return value

    def _get_boolean(self, section, option, default=None):
        return self._get_value(section=section, option=option, default=default, expect_boolean=True)

    def _get_int(self, section, option, default=None):
        return self._get_value(section=section, option=option, default=default, expect_int=True)

    def to_dict(self):
        """
        Convert all attributes from this class into a dictionary. Remove all attributes who start with _
        :return:
        """
        attribute_dict = dict()
        if self.successful:
            attribute_dict = self.__dict__
            attribute_dict = {k: v for k, v in attribute_dict.items() if not k.startswith('_')}

        return attribute_dict


def main():
    log_obj = Logger(verbose=True, file_path=".\\firefinder.log")
    log_obj.info("Start FireFinder")

    config_obj = ConfigFile(logger=log_obj)
    config_dict = config_obj.to_dict()
    config_successful = config_dict.get("successful", False)
    if not config_successful:
        log_obj.critical("Could not successfully load the configuration -> abording")
        assert config_successful, "Failed loading configuration file"

    gui = GuiHandler(logger             = log_obj,
                     gui_settings       = config_dict.get("gui_settings", dict()),
                     splash_settings    = config_dict.get("splash_screen", dict()),
                     clock_settings     = config_dict.get("clock_screen", dict()),
                     event_settings     = config_dict.get("event_screen", dict()),
                     slideshow_settings = config_dict.get("slideshow_screen", dict())
                     )
    gui.start()

    # Check if a path observation is configured, if so register it an apply gui-callback
    observe_path = config_dict["file_observer"].get("observing_path", "")
    observe_file = config_dict["file_observer"].get("observing_file", "")
    if observe_path != "" and os.path.isdir(observe_path):
        if observe_file != "":
            watch = FileWatch(file_path = os.path.join(observe_path, observe_file),
                              callback  = gui.set_screen_and_config,
                              logger    = log_obj)
            watch.start()
        else:
            log_obj.error("observing_path is defined in config but not observing_file, please specify it")
    else:
        log_obj.error(f"Cannot observe path '{observe_path}' as this path does not exist")

    # time.sleep(5)
    # gui.set_screen(screen_name=Screen.event)
    # time.sleep(5)
    # gui.set_screen(screen_name=Screen.clock)
    # time.sleep(5)
    gui.set_screen_and_config(screen_name=Screen.slideshow, screen_config={"slideshow_path": "D:\\Firefinder\\Slideshow"})
    while gui.is_running():
        time.sleep(1)

    gui.stop()


if __name__ == "__main__":
    main()
