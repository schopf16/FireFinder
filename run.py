#!/usr/bin/env python
# -*- coding: latin-1-*-

"""
    Copyright (C) 2016  Michael Anderegg <michael@anderegg.be>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import codecs
import os
import subprocess
import sys
import time
import logging.handlers
# import tkinter as tk
import pygame
from configparser import ConfigParser

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# local classes
from firefinder.ff_sound import AlarmSound
from firefinder.ff_screenClock import ScreenClock
from firefinder.ff_screenEvent import ScreenEvent
from firefinder.ff_screenOff import ScreenOff
from firefinder.ff_screenSlideshow import ScreenSlideshow
from firefinder.cecLibrary import TvPower
from firefinder.ff_miscellaneous import RepeatingTimer

# Überprüfen, ob die optionalen Text- und Sound-Module geladen werden konnten.
if not pygame.font: print('Fehler pygame.font Modul konnte nicht geladen werden!')
if not pygame.mixer: print('Fehler pygame.mixer Modul konnte nicht geladen werden!')

########################################################################
# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)-15s - %(levelname)-8s : %(message)s')

# create console handler and set level to debug
console_handler = logging.StreamHandler(sys.stdout)
# console_handler.setLevel(logging.DEBUG)

# add formatter to ch
console_handler.setFormatter(formatter)

# add handler to logger
logger.addHandler(console_handler)


########################################################################
class FireFinderGUI(pygame):
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
        pygame.display.set_caption("FireFinder")
        self.logger.debug("Set title to FireFinder")

        # The configuration works quite well on windows, but
        # very bad on linux systems if the script is loaded out
        # of the shell. To remove the mouse cursor us the "unclutter"
        # package instead
        # sudo apt-get install unclutter
        self.config(cursor="none")
        self.logger.debug("Disable cursor")


        infoObject = pygame.display.Info()
        width = infoObject.current_w
        height = infoObject.current_h
        resolution = (width, height)
        if self.full_screen_enable:
            resolution = pygame.display.list_modes()[0]
            main_surface = pygame.display.set_mode(resolution, pygame.FULLSCREEN)
        else:
            main_surface = pygame.display.set_mode(resolution)

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
        if self.actScreen is not '':
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


########################################################################       
class MyHandler(FileSystemEventHandler):
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

        if self.switch_screen_delay_after_start is not 0:
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
                if self.switch_screen_delay_after_event is not 0:
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


######################################################################## 
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
        if self.bypass_tv_power_save is not 0:
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
            if self.__actGraficOutput.lower() is 'on':
                if self.__actTelevisionState.lower() is 'on':
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
            if state.lower() is 'on':
                # Start timer only if its not alive, otherwise a
                # new screen whould restart the timer, but the TV
                # doesn't trigger the screen, only power-changes
                if self.rebootTvTimer.is_alive() is not True:
                    self.rebootTvTimer.start()

            if state.lower() is 'off':
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


########################################################################
def read_config_ini_file():
    """
    This function will open the file 'config.ini' which is located in
    the same folder as this run.py file. This configuration file holds
    all necessary information's about the firefinder app. The information's
    from the configuration file is stored in a dict for better handling
    afterwards

    :return: result True if no error occur, otherwise string with error
    :return: dict_ini Holds the stored information's in a Dict
    """
    try:
        wdr = os.path.dirname(__file__)
    except:
        wdr = os.getcwd()

    # Set default values
    error                           = None
    full_screen_enable              = False
    switch_screen_delay_after_start = 0
    switch_to_screen_after_start    = ScreenOff
    switch_screen_delay_after_event = 0
    switch_to_screen_after_event    = ScreenOff
    cec_enable                      = False
    standby_enable                  = False
    reboot_hdmi_device_after        = 0
    observing_file_name             = ''
    observing_path_name             = ''
    path_sound_folder               = 'None'
    force_sound_file                = 'None'
    force_sound_repetition          = 1
    company_path_logo               = ''
    company_name                    = ''
    enable_logging                  = False
    logging_file                    = ''
    logging_file_max_byte           = 1000
    logging_backup_count            = 2
    logging_level                   = 'Warning'

    # Create instance for reading the ini file
    sysconfig = ConfigParser()

    # Check if config.ini file exist
    config_path = os.path.join(wdr, 'config.ini')
    if not os.path.isfile(config_path):
        # Configuration file could not be found
        error_message = ("The file \"config.ini\" is missing. Be sure this"
                         "file is in the same directory like this python-script")
        error = 'IniFileNotFound'
        logger.critical(error_message)

    # config.ini file exist, going to read the data
    if error is None:
        with codecs.open(config_path, 'r', encoding='UTF-8-sig') as f:
            sysconfig.read_file(f)

        # read information which are required
        try:
            observing_path_name = sysconfig.get('General', 'observing_path')
            observing_file_name = sysconfig.get('General', 'observing_file')
        except:
            error_message = 'An unexpected error occurred while reading config.ini'
            error = 'CouldNotReadIniFile'
            logger.critical(error_message)

    if error is None:
        # Check if the observation-directory exist. Otherwise the observer
        # will raise a FileNotFoundError
        if not os.path.isdir(observing_path_name):
            # quit script due to an error
            error_message = ("The directory \"%s\" for observation is missing." % observing_path_name)
            error = 'PathDoesNotExist'
            logger.critical(error_message)

    # Read values with lower priority
    # [Visual]
    try:    full_screen_enable = sysconfig.getboolean('Visual', 'fullscreen')
    except: logger.debug("System configuration missing [Visual] --> fullscreen")
    try:    switch_screen_delay_after_start = sysconfig.getint('Visual', 'switchScreenAfterStart')
    except: logger.debug("System configuration missing [Visual] --> switchScreenAfterStart")
    try:    switch_to_screen_after_start = sysconfig.get('Visual', 'switchToScreenAfterStart')
    except: logger.debug("System configuration missing [Visual] --> switchToScreenAfterStart")
    try:    switch_screen_delay_after_event = sysconfig.getint('Visual', 'switchScreenAfterEvent')
    except: logger.debug("System configuration missing [Visual] --> switchScreenAfterEvent")
    try:    switch_to_screen_after_event = sysconfig.get('Visual', 'switchToScreenAfterEvent')
    except: logger.debug("System configuration missing [Visual] --> switchToScreenAfterEvent")
    try:    company_path_logo = sysconfig.get('Visual', 'company_path_logo')
    except: logger.debug("System configuration missing [Visual] --> company_path_logo")
    try:    company_name = sysconfig.get('Visual', 'company_name')
    except: logger.debug("System configuration missing [Visual] --> company_name")

    # [Power]
    try:    cec_enable = sysconfig.getboolean('Power', 'cec_enable')
    except: logger.debug("System configuration missing [Power] --> cec_enable")
    try:    standby_enable = sysconfig.getboolean('Power', 'stdby_enable')
    except: logger.debug("System configuration missing [Power] --> stdby_enable")
    try:    reboot_hdmi_device_after = sysconfig.getint('Power', 'cec_reboot_after_minutes')
    except: logger.debug("System configuration missing [Power] --> cec_reboot_after_minutes")

    # [Sound]
    try:    path_sound_folder = sysconfig.get('Sound', 'path_sounds')
    except: logger.debug("System configuration missing [Sound] --> path_sounds")
    try:    force_sound_file = sysconfig.get('Sound', 'force_sound_file')
    except: logger.debug("System configuration missing [Sound] --> force_sound_file")
    try:    force_sound_repetition = sysconfig.getint('Sound', 'force_repetition')
    except: logger.debug("System configuration missing [Sound] --> force_repetition")

    # [Logger]
    try:    enable_logging = sysconfig.getboolean('Logging', 'enable_logging')
    except: logger.debug("System configuration missing [Logging] --> enable_logging")
    try:    logging_file = sysconfig.get('Logging', 'logging_file')
    except: logger.debug("System configuration missing [Logging] --> logging_file")
    try:    logging_file_max_byte = sysconfig.getint('Logging', 'logging_file_max_byte')
    except: logger.debug("System configuration missing [Logging] --> logging_file_max_byte")
    try:    logging_backup_count = sysconfig.getint('Logging', 'logging_backup_count')
    except: logger.debug("System configuration missing [Logging] --> logging_backup_count")
    try:    logging_level = sysconfig.get('Logging', 'logging_level')
    except: logger.debug("System configuration missing [Logging] --> logging_level")

    # Check if sound-path exist. Otherwhise work with standard path
    if not os.path.isdir(path_sound_folder):
        path_sound_folder = os.path.join(wdr, 'firefinder', 'sound')

    # Create a directory for return value
    dict_ini = {"FullScreen"                  : full_screen_enable,
                "switchScreenDelayAfterStart" : switch_screen_delay_after_start,
                "switchToScreenAfterStart"    : switch_to_screen_after_start,
                "switchScreenDelayAfterEvent" : switch_screen_delay_after_event,
                "switchToScreenAfterEvent"    : switch_to_screen_after_event,
                "cec_enable"                  : cec_enable,
                "standby_hdmi_enable"         : standby_enable,
                "rebootHDMIdeviceAfter"       : reboot_hdmi_device_after,
                "ObserveFileForEvent"         : observing_file_name,
                "ObservePathForEvent"         : observing_path_name,
                "PathSoundFolder"             : path_sound_folder,
                "ForceSoundFile"              : force_sound_file,
                "ForceSoundRepetition"        : force_sound_repetition,
                "PathLogo"                    : company_path_logo,
                "CompanyName"                 : company_name,
                "LoggingEnable"               : enable_logging,
                "LoggingFilePathName"         : logging_file,
                "LoggingFileMaxByte"          : logging_file_max_byte,
                "LoggingBackupCount"          : logging_backup_count,
                "LoggingLevel"                : logging_level}

    if error is None:
        error = True
        logger.info('Load configuration file done')
    return error, dict_ini


########################################################################
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

    # Create a empty canvas to hold the error text string with a red background
    master = tk.Tk()
    error_canvas = tk.Canvas(master,
                             width=int(master.winfo_screenwidth() / 2),
                             height=int(master.winfo_screenheight() / 2),
                             background='red')

    # Create a text string placed in the canvas createt above
    error_canvas.create_text(int(master.winfo_screenwidth() / 4),
                             int(master.winfo_screenwidth() / 8),
                             text=u'!! Schwerer Systemfehler !!\n\n{0:s}'.format(error_message),
                             font=('arial', 30),
                             width=int(master.winfo_screenwidth() / 2))
    error_canvas.pack(side='top')
    return master


########################################################################
if __name__ == "__main__":

    # Hint to GNU copy left license
    logger.info("")
    logger.info("+-------------------------------------------------+")
    logger.info("| FireFinder Copyright (C) 2016  Michael Anderegg |")
    logger.info("| This program comes with ABSOLUTELY NO WARRANTY. |")
    logger.info("| This is free software, and you are welcome to   |")
    logger.info("| redistribute it under certain conditions.       |")
    logger.info("+-------------------------------------------------+")
    logger.info("")

    # Read config.ini File & check for failure
    result, configuration = read_config_ini_file()

    # set up logger to file
    if configuration["LoggingEnable"] is True:
        # create a rotating file handler
        file_logger = logging.handlers.RotatingFileHandler(filename=configuration["LoggingFilePathName"],
                                                           maxBytes=configuration["LoggingFileMaxByte"],
                                                           backupCount=configuration["LoggingBackupCount"])

        # set the logging level
        if configuration["LoggingLevel"].lower() == 'debug':
            file_logger.setLevel(level=logging.DEBUG)
        elif configuration["LoggingLevel"].lower() == 'info':
            file_logger.setLevel(level=logging.INFO)
        elif configuration["LoggingLevel"].lower() == 'warning':
            file_logger.setLevel(level=logging.WARNING)
        elif configuration["LoggingLevel"].lower() == 'error':
            file_logger.setLevel(level=logging.ERROR)
        elif configuration["LoggingLevel"].lower() == 'critical':
            file_logger.setLevel(level=logging.CRITICAL)

        file_logger.setFormatter(formatter)   # Adopt same formate as the console logger is using
        file_logger.doRollover()              # Force using new logging file
        logger.addHandler(file_logger)        # Add file to logging handler
        logger.info('File logger is loaded')  # Write first entry to log

        # Add a logging entry to file if the config file return an error
        if result is not True:
            logger.critical("Function read_config_ini_file returned: {}".format(result))

    if result is True:
        # Create some objects
        grafic = GraficOutputDriver(logger               = logger,
                                    cec_enable           = configuration["cec_enable"],
                                    standby_enable       = configuration["standby_hdmi_enable"],
                                    bypass_tv_power_save = configuration["rebootHDMIdeviceAfter"])
        app = FireFinderGUI(configuration, logger = logger)
        eventHandler = MyHandler(app, configuration, logger = logger)
        observer = Observer()

        # configure the observer thread and start it afterward
        file_for_oberve = configuration["ObservePathForEvent"]
        observer.schedule(eventHandler, file_for_oberve, recursive=False)
        observer.start()

    else:
        app = show_error_screen(result, configuration)

    app.mainloop()
