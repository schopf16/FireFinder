#!/usr/bin/env python
# -*- coding: latin-1-*-

"""
    Copyright (C) 2016  Michael Anderegg <m.anderegg@gmail.com>

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
import tkinter as tk
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

########################################################################

""" Path's """
ffLogo = 'firefinder/pic/Logo.png'  # Firefighter Logo
noImage = 'firefinder/pic/bg/no_image.png'


########################################################################
class FireFinderGUI(tk.Tk):
    def __init__(self, observing_path_name, **kwargs):
        super(FireFinderGUI, self).__init__()

        fullscreen_enable = kwargs.get('fullscreen', False)

        # Store actual shown screen
        self.actScreen = ''

        # Set actual window to fullscreen and bind the "Escape"
        # key with the function quit option
        self.title("FireFinder")

        # The configuration works quite well on windows, but
        # very bad on linux systems if the script is loaded out
        # of the shell. To remove the mouse cursor us the "unclutter"
        # package instead
        # sudo apt-get install unclutter
        self.config(cursor="none")

        # Removes the native window boarder
        if fullscreen_enable is True:
            self.attributes('-fullscreen', True)

        # Disable resizable of the x-axis and the y-axis to keep the
        # scree in the maximal possible resolution
        self.resizable(False, False)

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        print("Screensize is: %d x %d pixels" % (w, h))
        self.geometry("%dx%d+0+0" % (w, h))

        # Sets focus to the window to catch <Escape>
        self.focus_set()

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

            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # do some configurations to the screens
        self.frames[ScreenEvent].configure(pathToIniFile=observing_path_name)
        self.frames[ScreenSlideshow].configure(pathToIniFile=observing_path_name)

        # store some timing details
        self.startTime = int(time.time())
        self.lastChange = 0

        # show start screen
        self.show_frame(ScreenOff)

    # ----------------------------------------------------------------------
    def show_frame(self, cont):
        """

        :param cont:
        :return:
        """

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
        :return: Instance of the actaul shown frame
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
        print("Close programm")
        self.destroy()
        self.quit()  # Fallback if the one above doesn't work properly
        sys.exit()   # Fallback if the one above doesn't work properly


########################################################################       
class MyHandler(FileSystemEventHandler):
    def __init__(self, gui_handler, configuration_dict, ):

        # Grab all neccessery informations form the configuration dict
        full_screen_enable              = configuration_dict['FullScreen']
        self.switch_screen_delay_after_start = configuration_dict['switchScreenDelayAfterStart']
        self.switch_to_screen_after_start    = configuration_dict['switchToScreenAfterStart']
        self.switch_screen_delay_after_event = configuration_dict['switchScreenDelayAfterEvent']
        self.switch_to_screen_after_event    = configuration_dict['switchToScreenAfterEvent']
        cec_enable                      = configuration_dict['cec_enable']
        standby_enable                  = configuration_dict['standby_hdmi_enable']
        reboot_hdmi_device_after        = configuration_dict['rebootHDMIdeviceAfter']
        self.observing_file_name             = configuration_dict['ObserveFileForEvent']
        observing_path_name             = configuration_dict['ObservePathForEvent']
        self.path_sound_folder               = configuration_dict['PathSoundFolder']
        path_logo                       = configuration_dict['PathLogo']

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

            # The parser-file has to be converted as UTF-8 file. Otherwise
            # special character like umlaut could not successfully read.
            try:
                with codecs.open(event.src_path, 'r', encoding='UTF-8-sig') as f:
                    self.parser.read_file(f)
            except:
                print("Failed to open ini-file \"%s\"" % event.src_path)
                print("--> Be sure file is encode as \"UTF-8 BOM\"")
                print("--------------------------------------------------\n\n")
                return

            if not self.parser.has_option('General', 'show'):
                print("Failed to read variable \"show\" in section [General]")
                return

            # file was modivied by user, aboard auto_switch_screen_after_start if running
            if self._job_after_startup is not None:
                self.gui_instance.after_cancel(self._job_after_startup)
                self._job_after_startup = None

            if self._job_after_event is not None:
                self.gui_instance.after_cancel(self._job_after_event)
                self._job_after_event = None

            # Parse the requestet screen
            show = self.parser.get('General', 'show')

            # If time-screen is requested, get some additional settings
            if show.lower() == 'time':
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

            # If event-screen is requestet, get some additional settings
            if show.lower() == 'event':
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

                # set sound
                if sound.lower() != 'None':
                    self.sound_handler.load_music(sound)
                    self.sound_handler.start(loops=repeat, start=0, delay=2, pause=15)
                else:
                    self.sound_handler.stop()

                # Create a job to switch screen after a certain time
                if self.switch_screen_delay_after_event is not 0:
                    self._job_after_event = self.gui_instance.after(self.switch_screen_delay_after_event * 1000,
                                                                    self.switch_screen_frame,
                                                                    self.switch_to_screen_after_event)

            if show.lower() == 'quit':
                self.sound_handler.stop()
                self.power_instance.set_visual('On')
                self.gui_instance.exit(self)

            self.switch_screen_frame(show)

    # ----------------------------------------------------------------------
    def switch_screen_frame(self, switch_to_screen_frame):

        if switch_to_screen_frame.lower() == 'time':
            self.sound_handler.stop()
            self.gui_instance.show_frame(ScreenClock)
            self.power_instance.set_visual('On')

        if switch_to_screen_frame.lower() == 'slideshow':
            self.sound_handler.stop()
            self.gui_instance.show_frame(ScreenSlideshow)
            self.power_instance.set_visual('On')

        if switch_to_screen_frame.lower() == 'event':
            self.gui_instance.show_frame(ScreenEvent)
            self.power_instance.set_visual('On')

        if switch_to_screen_frame.lower() == 'off':
            self.sound_handler.stop()
            self.gui_instance.show_frame(ScreenOff)
            self.power_instance.set_visual('Off')


######################################################################## 
class GraficOutputDriver:
    def __init__(self, bypass_tv_power_save, **kwargs):
        self.cec_enable = kwargs.get("cec_enable", False)
        self.standby_enable = kwargs.get("standby_enable", False)

        self.__actGraficOutput = 'On'
        self.__actTelevisionState = 'Off'

        # Create television object to drive TV
        self.television = TvPower()

        # create a empty 'object' for a timer, if requested
        self.rebootTvTimer = None

        # Try to disable power saving
        if os.name == 'posix':
            try:    subprocess.call(["xset", "s", "noblank"])
            except: pass
            try:    subprocess.call(["xset", "s", "noblank"])
            except: pass
            try:    subprocess.call(["xset", "-dpms"])
            except: pass

        elif os.name == 'nt':
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
        if bypass_tv_power_save is not 0:
            self.rebootTvTimer = RepeatingTimer(bypass_tv_power_save * 60,
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
            availalbe. If done otherwise, the cec command can't be
            transmittet over a deactivatet HDMI port.
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
                print("Switch TV on")
                self.television.run(True)

        if new_state.lower() == 'off':
            '''
            ORDER:
            First switch of the TV with the CEC commandos if availalbe
            and then disable the HDMI port. If done otherwise, the
            cec command can't be transmittet over a deactivatet HDMI
            port.
            '''
            if self.cec_enable:
                print("Switch TV off")
                self.television.run(False)

            if self.standby_enable and (os.name == 'posix'):
                if self.__actGraficOutput != new_state:
                    try:    subprocess.call(["/opt/vc/bin/tvservice", "-o"])
                    except: pass
                    self.__actGraficOutput = new_state

    # ----------------------------------------------------------------------
    def __reboot_television_over_cec(self):
        print("keep alive TV requested")

        self.__switch_grafic_output('Off')
        time.sleep(10)
        self.__switch_grafic_output('On')


########################################################################
def read_config_ini_file():
    """
    This function will open the file 'config.ini' which is located in
    the same folder as this run.py file. This configuration file holds
    all necessary informations about the firefinder app. The informations
    from the configuration file is stored in a dict for better handling
    afterwards

    :return: result True if no error occur, otherwise string with error
    :return: dict_ini Holds the stored informations in a Dict
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
    path_sound_folder               = os.path.join(wdr, 'firefinder', 'sound')
    path_logo                       = ''

    # Create instance for reading the ini file
    sysconfig = ConfigParser()

    # Check if config.ini file exist
    config_path = os.path.join(wdr, 'config.ini')
    if not os.path.isfile(config_path):
        # Configuration file could not be found
        error_message = ("The file \"config.ini\" is missing. Be sure this"
                         "file is in the same directory like this python-script")
        print("ERROR: %s" % error_message)
        error = 'IniFileNotFound'

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
            print("ERROR: %s" % error_message)
            error = 'CouldNotReadIniFile'

    if error is None:
        # Check if the observation-directory exist. Otherwise the observer
        # will raise a FileNotFoundError
        if not os.path.isdir(observing_path_name):
            # quit script due to an error
            error_message = ("The directory \"%s\" for observation is missing." % observing_path_name)
            print("ERROR: %s" % error_message)
            error = 'PathDoesNotExist'

    # Read values with lower priority
    if error is None:
        # Path]
        try:    path_sound_folder = sysconfig.getboolean('Path', 'path_sounds')
        except: pass
        try:    path_logo = sysconfig.getint('Path', 'path_logo')
        except: pass

        # [Visual]
        try:    full_screen_enable = sysconfig.getboolean('Visual', 'fullscreen')
        except: pass
        try:    switch_screen_delay_after_start = sysconfig.getint('Visual', 'switchScreenAfterStart')
        except: pass
        try:    switch_to_screen_after_start = sysconfig.get('Visual', 'switchToScreenAfterStart')
        except: pass
        try:    switch_screen_delay_after_event = sysconfig.getint('Visual', 'switchScreenAfterEvent')
        except: pass
        try:    switch_to_screen_after_event = sysconfig.get('Visual', 'switchToScreenAfterEvent')
        except: pass

        # [Power]
        try:    cec_enable = sysconfig.getboolean('Power', 'cec_enable')
        except: pass
        try:    standby_enable = sysconfig.getboolean('Power', 'stdby_enable')
        except: pass
        try:    reboot_hdmi_device_after = sysconfig.getint('Power', 'cec_reboot_after_minutes')
        except: pass

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
                "PathLogo"                    : path_logo}

    if error is None:
        error = True
    return error, dict_ini


########################################################################
def show_error_screen(error_code, ini_file_path):
    """
    This function will create a canvas and show up the given error code
    in a way that the user can handelt it easily

    :param error_code: String off error code given by the function read_config_ini_file
    :param ini_file_path: Dict of the ini file, given by the function read_config_ini_file
    :return: instanc of a tinker for display
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
    print("\n")
    print("+-------------------------------------------------+")
    print("| FireFinder Copyright (C) 2016  Michael Anderegg |")
    print("| This program comes with ABSOLUTELY NO WARRANTY. |")
    print("| This is free software, and you are welcome to   |")
    print("| redistribute it under certain conditions.       |")
    print("+-------------------------------------------------+")
    print("\n\n")

    # Read config.ini File & check for failure
    result, configuration = read_config_ini_file()
    if result is True:
        # Create some objects
        grafic = GraficOutputDriver(configuration["rebootHDMIdeviceAfter"])
        app = FireFinderGUI(observing_path_name=configuration["ObservePathForEvent"])
        eventHandler = MyHandler(app, configuration)
        observer = Observer()

        # configure the observer thread and start it afterward
        file_for_oberve = configuration["ObservePathForEvent"]
        observer.schedule(eventHandler, file_for_oberve, recursive=False)
        observer.start()

    else:
        app = show_error_screen(result, configuration)

    app.mainloop()
