#!/usr/bin/env python
# -*- coding: latin-1-*-

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

import codecs
import os
import subprocess
import sys
import time
# import logging.handlers
import pygame
# from pygame.locals import KEYDOWN, K_ESCAPE
import tkinter as tk
import configparser

# local classes
from firefinder.ff_sound import AlarmSound
from firefinder.ff_screenClock import ScreenClock
from firefinder.ff_screenEvent import ScreenEvent
from firefinder.ff_screenOff import ScreenOff
from firefinder.ff_screenSlideshow import ScreenSlideshow
from firefinder.cecLibrary import TvPower
from firefinder.ff_miscellaneous import RepeatingTimer

from firefinder.util_screen import GuiHandler, Screen
from firefinder.util_logger import Logger
from firefinder.util_filehandler import FileWatch


########################################################################

class FireFinderGUI(tk.Tk):
    def __init__(self, configuration_dict, **kwargs):
        super(FireFinderGUI, self).__init__()

        self.logger = kwargs.get("logger", logging.getLogger('FireFinderGUI'))

        self.full_screen_enable  = configuration_dict['FullScreen']
        self.observing_path_name = configuration_dict['ObservePathForEvent']
        self.path_logo           = configuration_dict['PathLogo']
        self.company_name        = configuration_dict['CompanyName']

        # Store actual shown screen
        self.actScreen = ''

        # Set actual window to fullscreen and bind the "Escape"
        # key with the function quit option
        self.title("FireFinder")
        self.logger.debug("Set title to FireFinder")

        # The configuration works quite well on windows, but
        # very bad on linux systems if the script is loaded out
        # of the shell. To remove the mouse cursor us the "unclutter"
        # package instead
        # sudo apt-get install unclutter
        self.config(cursor="none")
        self.logger.debug("Disable cursor")

        # Removes the native window boarder
        if self.full_screen_enable is True:
            self.attributes('-fullscreen', True)
            self.logger.info("Set window to fullscreen")
        else:
            self.logger.info("Do not use window in fullscreen")

        # Disable resizable of the x-axis and the y-axis to keep the
        # scree in the maximal possible resolution
        self.resizable(False, False)
        self.logger.debug("Disable resizable of the windwos")

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.logger.info("Screensize of monitor is: %d x %d" % (w, h))
        self.geometry("%dx%d+0+0" % (w, h))

        # Sets focus to the window to catch <Escape>
        self.focus_set()
        self.logger.debug("Get focus of the window to catch <Escape>")

        # Bind <Escape> tap to the exit method
        self.bind("<Escape>", lambda e: self.exit())

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (ScreenSlideshow,
                  ScreenEvent,
                  ScreenClock,
                  ScreenOff):  # Load 'ScreenOff' as last screen
            self.logger.debug("Create a container for frame {}".format(F))
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # do some configurations to the screens
        self.logger.debug("Configure the created frames")
        self.frames[ScreenEvent].configure(pathToIniFile=self.observing_path_name)
        self.frames[ScreenSlideshow].configure(pathToIniFile   = self.observing_path_name,
                                               logoPathAndFile = self.path_logo,
                                               companyName     = self.company_name)
        self.frames[ScreenOff].configure(logoPathAndFile=self.path_logo)

        # store some timing details
        self.startTime = int(time.time())
        self.lastChange = 0

        # show start screen
        self.logger.info("Load splashscreen as start screen")
        self.show_frame(ScreenOff)

    # ----------------------------------------------------------------------
    def show_frame(self, cont):
        """

        :param cont:
        :return:
        """
        self.logger.info("Load {} frame in front".format(cont))

        # send a hide signal to the actual shown screen
        if self.actScreen != '':
            self.frames[self.actScreen].descent_screen()

        # store the name of the new screen    
        self.actScreen = cont
        self.lastChange = int(time.time())

        # switch to this screen and raise it up
        frame = self.frames[cont]
        self.frames[self.actScreen].raise_screen()
        frame.tkraise()

    # ----------------------------------------------------------------------
    def get_act_frame(self):
        """
        The method will return the instance of the actual selected frame
        :return: Instance of the actual shown frame
        """
        return self.frames[self.actScreen]

    # ----------------------------------------------------------------------
    def get_screen_frame(self, screen_name):
        return self.frames[screen_name]

    # ----------------------------------------------------------------------
    def get_act_screen(self):
        """
        The method will return the name of the actual shown screen
        :return: String with the screen name
        """
        return self.actScreen

    # ----------------------------------------------------------------------
    def exit(self):
        self.logger.info("Close program")
        self.destroy()
        self.quit()  # Fallback if the one above doesn't work properly
        sys.exit()   # Fallback if the one above doesn't work properly


class MyHandler(object):
    def __init__(self, gui_handler, configuration_dict, **kwargs):

        self.logger = kwargs.get("logger", logging.getLogger())

        # Grab all necessary information's form the configuration dict
        self.switch_screen_delay_after_start = configuration_dict['switchScreenDelayAfterStart']
        self.switch_to_screen_after_start    = configuration_dict['switchToScreenAfterStart']
        self.switch_screen_delay_after_event = configuration_dict['switchScreenDelayAfterEvent']
        self.switch_to_screen_after_event    = configuration_dict['switchToScreenAfterEvent']
        self.observing_file_name             = configuration_dict['ObserveFileForEvent']
        self.path_sound_folder               = configuration_dict['PathSoundFolder']
        self.force_sound_file                = configuration_dict['ForceSoundFile']
        self.force_repetition                = configuration_dict['ForceSoundRepetition']

        # Create instances
        self.sound_handler = AlarmSound(self.path_sound_folder)
        self.parser = ConfigParser()

        self.gui_instance    = gui_handler
        self.power_instance  = grafic

        # variable to hold the ID of the "after" job to
        self._job_after_startup  = None
        self._job_after_event    = None

        self.lastModified = 0

        if self.switch_screen_delay_after_start != 0:
            self._job_after_startup = self.gui_instance.after(self.switch_screen_delay_after_start * 1000,  # Delay in milliseconds
                                                              self.switch_screen_frame,  # Called function after time expired
                                                              self.switch_to_screen_after_start)  # Screen to display

    # ----------------------------------------------------------------------
    def on_modified(self, event):
        # Check if the file has ben modified I'm looking for
        if os.path.split(event.src_path)[-1].lower() == self.observing_file_name.lower():

            # Due to some reasons, the watchdog trigger the FileModifiedEvent
            # twice. Therefore capture the time and ignore changes within
            # the next second.
            if self.lastModified == time.ctime(os.path.getmtime(event.src_path)):
                return

            self.lastModified = time.ctime(os.path.getmtime(event.src_path))
            self.logger.debug("FileModifiedEvent raised")

            # The parser-file has to be converted as UTF-8 file. Otherwise
            # special character like umlaut could not successfully read.
            try:
                with codecs.open(event.src_path, 'r', encoding='UTF-8-sig') as f:
                    self.parser.read_file(f)
            except:
                self.logger.exception("Failed to open ini-file \"{}\", be sure"
                                      "file is encoded as \"UTF-8 BOM\"".format(event.src_path))
                return

            if not self.parser.has_option('General', 'show'):
                self.logger.error("Failed to read variable \"show\" in section [General]")
                return

            # file was modivied by user, aboard auto_switch_screen_after_start if running
            if self._job_after_startup is not None:
                self.logger.debug("Aboard switchToScreenAfterStart")
                self.gui_instance.after_cancel(self._job_after_startup)
                self._job_after_startup = None

            if self._job_after_event is not None:
                self.logger.debug("Aboard switchToScreenAfterEvent")
                self.gui_instance.after_cancel(self._job_after_event)
                self._job_after_event = None

            # Parse the requested screen
            show = self.parser.get('General', 'show')

            # If time-screen is requested, get some additional settings
            if show.lower() == 'clock':
                # get information from ini-file
                try:    show_second_hand    = self.parser.getboolean('Clock', 'show_second_hand')
                except: show_second_hand    = True
                try:    show_minute_hand    = self.parser.getboolean('Clock', 'show_minute_hand')
                except: show_minute_hand    = True
                try:    show_hour_hand      = self.parser.getboolean('Clock', 'show_hour_hand')
                except: show_hour_hand      = True
                try:    show_digital_time   = self.parser.getboolean('Clock', 'show_digital_time')
                except: show_digital_time   = False
                try:    show_ditial_date    = self.parser.getboolean('Clock', 'show_digital_date')
                except: show_ditial_date    = True
                try:    show_digital_second = self.parser.getboolean('Clock', 'show_digital_second')
                except: show_digital_second = True

                frame = self.gui_instance.get_screen_frame(ScreenClock)
                frame.configure(showSecondHand=show_second_hand,
                                showMinuteHand=show_minute_hand,
                                showHourHand=show_hour_hand,
                                showDigitalTime=show_digital_time,
                                showDigitalDate=show_ditial_date,
                                showDigitalSeconds=show_digital_second)

            # If event-screen is requested, get some additional settings
            elif show.lower() == 'event':
                # get information from ini-file
                try:    full_event_message = self.parser.get('Event', 'message_full')
                except: full_event_message = ""
                try:    picture_1          = self.parser.get('Event', 'picture_left')
                except: picture_1          = ""
                try:    picture_2          = self.parser.get('Event', 'picture_right')
                except: picture_2          = ""
                try:    crop_pciture       = self.parser.getboolean('Event', 'crop_picture')
                except: crop_pciture       = True
                try:    category           = self.parser.get('Event', 'category')
                except: category           = ""
                try:    sound              = self.parser.get('Sound', 'sound')
                except: sound              = "07.mp3"
                try:    repeat             = self.parser.getint('Event', 'repeat')
                except: repeat             = 1
                try:    progressbar_show   = self.parser.getboolean('Progress', 'show_progress')
                except: progressbar_show   = False
                try:    progressbar_time   = self.parser.getint('Progress', 'progress_time')
                except: progressbar_time   = 0
                try:    responseorder_show = self.parser.getboolean('Response', 'show_responseOrder')
                except: responseorder_show = False

                equipment = {}
                for x in range(1, 10):
                    s = ('equipment_%01i' % x)
                    try:    equipment[x] = self.parser.get('Response', s)
                    except: equipment[x] = ""

                frame = self.gui_instance.get_screen_frame(ScreenEvent)
                frame.configure(alarmMessage=full_event_message,
                                picture_1=picture_1,
                                picture_2=picture_2,
                                cropPicture=crop_pciture,
                                category=category,
                                progressBarTime=progressbar_time,
                                responseOrder=equipment,
                                showProgressBar=progressbar_show,
                                showResponseOrder=responseorder_show)

                # Check if a sound file needs to be played
                if sound.lower() != 'none' or self.force_sound_file.lower() != 'none':
                    h_result = False
                    if sound.lower() != 'none':
                        h_result = self.sound_handler.load_music(sound)

                    # If sound-file couldn't be loaded, try to overwrite with force settings
                    if self.force_sound_file.lower() != 'none' and not h_result:
                        h_result = self.sound_handler.load_music(self.force_sound_file)
                        repeat   = self.force_repetition

                    if h_result:
                        self.sound_handler.start(loops=repeat, start=0, delay=2, pause=15)
                else:
                    self.sound_handler.stop()

                # Create a job to switch screen after a certain time
                if self.switch_screen_delay_after_event != 0:
                    self._job_after_event = self.gui_instance.after(self.switch_screen_delay_after_event * 1000,
                                                                    self.switch_screen_frame,
                                                                    self.switch_to_screen_after_event)

            # If slideshow-screen is requested, get some additional settings
            elif show.lower() == 'slideshow':
                # get information from ini-file
                try:    sort_images_alphabetically = self.parser.getboolean('Slideshow', 'sort_images_alphabetically')
                except: sort_images_alphabetically = True
                try:    show_header_bar = self.parser.getboolean('Slideshow', 'show_header_bar')
                except: show_header_bar = True
                try:    seconds_between_images = self.parser.getint('Slideshow', 'seconds_between_images')
                except: seconds_between_images = 10

                frame = self.gui_instance.get_screen_frame(ScreenSlideshow)
                frame.configure(sortAlphabetically=sort_images_alphabetically,
                                secondsBetweenImages=seconds_between_images,
                                showHeaderBar=show_header_bar)

            # If software close is requested, do some additional settings
            elif show.lower() == 'quit':
                self.sound_handler.stop()
                self.power_instance.set_visual('On')
                self.gui_instance.exit(self)

            self.switch_screen_frame(show)

    # ----------------------------------------------------------------------
    def switch_screen_frame(self, switch_to_screen_frame):

        if switch_to_screen_frame.lower() == 'clock':
            self.sound_handler.stop()
            self.gui_instance.show_frame(ScreenClock)
            self.power_instance.set_visual('On')

        elif switch_to_screen_frame.lower() == 'slideshow':
            self.sound_handler.stop()
            self.gui_instance.show_frame(ScreenSlideshow)
            self.power_instance.set_visual('On')

        elif switch_to_screen_frame.lower() == 'event':
            self.gui_instance.show_frame(ScreenEvent)
            self.power_instance.set_visual('On')

        elif switch_to_screen_frame.lower() == 'splashscreen':
            self.sound_handler.stop()
            self.gui_instance.show_frame(ScreenOff)
            self.power_instance.set_visual('On')

        elif switch_to_screen_frame.lower() == 'off':
            self.sound_handler.stop()
            self.gui_instance.show_frame(ScreenOff)
            self.power_instance.set_visual('Off')

        else:
            self.logger.warning("No visual frame with name \"{}\" avialable".format(switch_to_screen_frame))


class GraficOutputDriver:
    def __init__(self, **kwargs):
        self.logger               = kwargs.get("logger", logging.getLogger('GraficOutputDriver'))
        self.cec_enable           = kwargs.get("cec_enable", False)
        self.standby_enable       = kwargs.get("standby_enable", False)
        self.bypass_tv_power_save = kwargs.get("bypass_tv_power_save", 0)

        self.__actGraficOutput = 'On'
        self.__actTelevisionState = 'Off'

        # Create television object to drive TV
        self.television = TvPower()

        # create a empty 'object' for a timer, if requested
        self.rebootTvTimer = None

        # Try to disable power saving
        if os.name == 'posix':
            self.logger.debug("Try to disable power save on unix system")
            try:    subprocess.call(["xset", "s", "noblank"])
            except: pass
            try:    subprocess.call(["xset", "s", "noblank"])
            except: pass
            try:    subprocess.call(["xset", "-dpms"])
            except: pass

        elif os.name == 'nt':
            self.logger.debug("Try to disable power save on windows system")
            try:    subprocess.call(["powercfg.exe", "-change", "-monitor-timeout-ac", "0"])
            except: pass
            try:    subprocess.call(["powercfg.exe", "-change", "-disk-timeout-ac", "0"])
            except: pass
            try:    subprocess.call(["powercfg.exe", "-change", "-standby-timeout-ac", "0"])
            except: pass
            try:    subprocess.call(["powercfg.exe", "-change", "-hibernate-timeout-ac", "0"])
            except: pass

        # If user enable automatic TV reboot to prevent it from power save
        # launch a separate thread to handle this asynchron from any ini-commands
        if self.bypass_tv_power_save != 0:
            self.logger.debug("Load timer for reboot TV")
            self.rebootTvTimer = RepeatingTimer(self.bypass_tv_power_save * 60,
                                                self.__reboot_television_over_cec)

    # ----------------------------------------------------------------------
    def get_visual(self):
        return_value = 'off'

        """
        Return the status of the graphical output. If CEC is enabled, both
        (HDMI output and television on) has to be enabled, otherwise 'Off'
        will returned if at least on is disabled.
        """
        if self.cec_enable:
            if self.__actGraficOutput.lower() == 'on':
                if self.__actTelevisionState.lower() == 'on':
                    return_value = 'on'
        else:
            return_value = self.__actGraficOutput

        return return_value

    # ----------------------------------------------------------------------
    def set_visual(self, state):
        """
        Activate or deactivate the graphical output to force monitor to
        standby. If CEC is enabled, the television is triggered too,
        otherwise only the graphic output is driven.
        :param state: Can be on or off
        """
        if self.rebootTvTimer:
            if state.lower() == 'on':
                # Start timer only if its not alive, otherwise a
                # new screen whould restart the timer, but the TV
                # doesn't trigger the screen, only power-changes
                if self.rebootTvTimer.is_alive() is not True:
                    self.rebootTvTimer.start()

            if state.lower() == 'off':
                if self.rebootTvTimer.is_alive() is True:
                    self.rebootTvTimer.cancel()
                    self.rebootTvTimer.join(20)  # wait to kill thread

        self.__switch_grafic_output(new_state=state)

    # ----------------------------------------------------------------------
    def set_power_off(self):
        self.set_visual('Off')

    # ----------------------------------------------------------------------
    def __switch_grafic_output(self, new_state):

        if new_state.lower() == 'on':
            '''
            ORDER:
            First enable the HDMI port and the switch the TV on if
            available. If done otherwise, the cec command can't be
            transmitted over a deactivated HDMI port.
            '''
            if self.standby_enable and (os.name == 'posix'):
                if self.__actGraficOutput != new_state:
                    try:    subprocess.call(["/opt/vc/bin/tvservice", "-p"])
                    except: pass
                    try:    subprocess.call(["sudo", "/bin/chvt", "6"])
                    except: pass
                    try:    subprocess.call(["sudo", "/bin/chvt", "7"])
                    except: pass
                    self.__actGraficOutput = new_state

            if self.cec_enable:
                # Always enable TV. The user could switch of TV manualy
                self.logger.info("Switch TV on")
                self.television.run(True)

        if new_state.lower() == 'off':
            '''
            ORDER:
            First switch off the TV with the CEC commandos if available
            and then disable the HDMI port. If done otherwise, the
            cec command can't be transmitted over a deactivate HDMI
            port.
            '''
            if self.cec_enable:
                self.logger.info("Switch TV off")
                self.television.run(False)

            if self.standby_enable and (os.name == 'posix'):
                if self.__actGraficOutput != new_state:
                    try:    subprocess.call(["/opt/vc/bin/tvservice", "-o"])
                    except: pass
                    self.__actGraficOutput = new_state

        if (self.cec_enable is False) and (self.standby_enable is False):
            self.logger.warning("CEC and Standby is disabled. Monitor can't switch on or off")

    # ----------------------------------------------------------------------
    def __reboot_television_over_cec(self):
        self.logger.debug("keep alive TV requested")

        self.__switch_grafic_output('Off')
        time.sleep(10)
        self.__switch_grafic_output('On')


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
                "sort_alphabetically"   : self._get_boolean('Slideshow', 'sort_alphabetically', default=True),
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


def show_error_screen(error_code, ini_file_path):
    """
    This function will create a canvas and show up the given error code
    in a way that the user can handel it easily

    :param error_code: String off error code given by the function read_config_ini_file
    :param ini_file_path: Dict of the ini file, given by the function read_config_ini_file
    :return: instance of a tinker for display
    """
    error_code    = error_code
    error_message = ''
    ini_file_path = ini_file_path

    if error_code == 'IniFileNotFound':
        error_message = ('Die Datei config.ini wurde nicht gefunden. '
                         'Stelle sicher dass sich die Datei im selben '
                         'Ordner befindet wie die Datei \"run.py\"')
    elif error_code == 'CouldNotReadIniFile':
        error_message = ('Die Datei config.ini konnte nicht gelesen '
                         'werden. Stelle sicher, dass in der Gruppe '
                         '[General] die Variablen richtig aufgefuehrt '
                         'sind\n\n[General]\nobserving_path = <Kompletter '
                         'Pfad ohne Datei>\nobserving_file   = <Dateiname mit Endung>')
    elif error_code == 'PathDoesNotExist':
        received_path_and_file = os.path.join(ini_file_path["ObservePathForEvent"],
                                              ini_file_path["ObserveFileForEvent"])
        error_message = ('Der in der config.ini Datei angegebene Pfad'
                         '\n\n{}\n\nwurde nicht gefunden. Stelle sicher '
                         'dass der Pfad korrekt ist. Die Gross- / Klein'
                         'schreibung muss beachtet werden.'
                         .format(received_path_and_file))

    # Create an empty canvas to hold the error text string with a red background
    pygame.init()

    info_obj = pygame.display.Info()
    screen = pygame.display.set_mode((info_obj.current_w / 2, info_obj.current_h / 2))

    # Fill the background with red

    screen.fill((255, 0, 0))

    font = pygame.font.SysFont('arial', 30)
    text = u'!! Schwerer Systemfehler !!\n\n{0:s}'.format(error_message)
    blit_text(screen, text, (20, 20), font)
    #  img = font.render(u'!! Schwerer Systemfehler !!\n\n{0:s}'.format(error_message), True, (255, 255, 255))
    # screen.blit(img, (20, 20))

    # master = tk.Tk()
    # error_canvas = tk.Canvas(master,
    #                          width=int(master.winfo_screenwidth() / 2),
    #                          height=int(master.winfo_screenheight() / 2),
    #                          background='red')
    #
    # # Create a text string placed in the canvas created above
    # error_canvas.create_text(int(master.winfo_screenwidth() / 4),
    #                          int(master.winfo_screenwidth() / 8),
    #                          text=u'!! Schwerer Systemfehler !!\n\n{0:s}'.format(error_message),
    #                          font=('arial', 30),
    #                          width=int(master.winfo_screenwidth() / 2))
    # error_canvas.pack(side='top')
    # return master
    return screen


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
