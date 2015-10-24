#!/usr/bin/env python
# -*- coding: latin-1-*-

'''
    Copyright (C) 2015  Michael Anderegg <m.anderegg@gmail.com>

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
'''


import sys
import os
import codecs
import tkinter as tk
import subprocess
import time


from configparser       import ConfigParser
from watchdog.observers import Observer
from watchdog.events    import FileSystemEventHandler

# local classes
from firefinder.sound           import alarmSound
from firefinder.screenClock     import ScreenClock
from firefinder.screenObject    import ScreenObject
from firefinder.screenOff       import ScreenOff
from firefinder.screenSlideshow import ScreenSlideshow

from django.utils.termcolors import background, foreground

try:   
    from firefinder.cecLibrary     import CecClient
    cec_lib_available = True
except:
    print("Failed load CEC")
    cec_lib_available = False
    


LARGE_FONT= ("Verdana", 12)

########################################################################
'''
Some global settings out of the config.ini file which is
read out at the beginning of the program.
'''
# [General] group
observingPathName   = ''
observingFileName   = ''

# [Visual] group
fullscreenEnable    = False  
switchScreenAfter   = 0
switchToScreen      = ''

# [Power] group
cecEnable           = False
stdbyEnable         = False
cecRebootInMinutes  = 0

""" Path's """
ffLogo      = 'firefinder/pic/Logo.png'     # Firefighter Logo
noImage     = 'firefinder/pic/bg/no_image.png'
HDMI_script = 'script/reactivate_screen.sh' # Script to enable HDMI output
wdr         = '' # Working direcotry is set in main 

########################################################################
class FireFinderGUI(tk.Tk):

    def __init__(self, *args, **kwargs):
        """Constructor"""
        tk.Tk.__init__(self, *args, **kwargs)
        
        # Store actual shown screen
        self.actScreen  = ''
        
        # Set actual window to fullscreen and bind the "Escape"
        # key with the function quit option
        self.title("FireFinder")
                
        ''' Remove mouse cursor '''
        # The configuration works quite well on windows, but
        # very bad on linux systems if the script is loaded out
        # of the shell. To remove the mouse cursor us the "unclutter"
        # package instead
        # sudo apt-get install unclutter
        self.config(cursor="none")
        
        ''' Removes the native window boarder. '''
        if fullscreenEnable is True:
            self.attributes('-fullscreen', True)
            
        # With overrideredirect program loses connection with 
        # window manage so it seems that it can't get information 
        # about pressed keys and even it can't be focused.
        #self.overrideredirect(fullscreen)
        
        ''' Disables resizing of the widget.  '''
        self.resizable(False, False)

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        print(("Screensize is: %d x %d pixels") %(w, h))
        self.geometry("%dx%d+0+0" % (w, h))

        ''' Sets focus to the window to catch <Escape> '''
        self.focus_set()
        
        """ Bind Escape tap to the exit method """
        self.bind("<Escape>", lambda e: self.exit())
        
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)        
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        for F in (ScreenSlideshow, 
                  ScreenObject,
                  ScreenClock,
                  ScreenOff):     # Load offscreen as last screen

            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # do some configurations to the screens
        self.frames[ScreenObject].configure(pathToIniFile = observingPathName)
        self.frames[ScreenSlideshow].configure(pathToIniFile = observingPathName)
        
        # store some timing details
        self.startTime  = int(time.time())
        self.lastChange = 0
        
        # show start screen
        self.show_frame(ScreenOff)

    #----------------------------------------------------------------------
    def show_frame(self, cont):
        
        # send a hide signal to the actual shown screen
        if self.actScreen is not '':
            self.frames[self.actScreen].descentScreen()
        
        # store the name of the new screen    
        self.actScreen = cont
        self.lastChange= int(time.time())
        
        # switch to this screen and raise it up
        frame = self.frames[cont]
        self.frames[self.actScreen].raiseScreen()
        frame.tkraise()

    #----------------------------------------------------------------------
    def getActScreen(self):
        return self.frames[self.actScreen]
    
    #----------------------------------------------------------------------
    def exit(self):
        print("Close programm")
        self.destroy()
        self.quit() # Fallback if the one above doesn't work properly
        sys.exit()  # Fallback if the one above doesn't work properly 
        os._exit(0) # Fallback if the one above doesn't work properly      

               
########################################################################       
class MyHandler(FileSystemEventHandler):
    def __init__(self, controller):
        
        """Constructor"""
        self.controller = controller
        self.HDMIout    = SwitchTelevision()

        self.alarmSound   = alarmSound( os.path.join(wdr, 'firefinder', 'sound') )
        self.lastModified = 0
        
           
    #----------------------------------------------------------------------
    def on_modified(self, event):
        # Check if the file has ben modified I'm looking for
        if os.path.split(event.src_path)[-1].lower() == observingFileName.lower():

            """
            Do to some reasons, the watchdog trigger the FileModifiedEvent
            twice. Therefore capture the time and ignore changes within
            the next second.
            """
            
            if self.lastModified == time.ctime(os.path.getmtime(event.src_path)):
                return
             
            self.lastModified = time.ctime(os.path.getmtime(event.src_path)) 

            # The parser-file has to be converted as UTF-8 file. Otherwise
            # special character like umlaut could not successfully read.
            try:
                self.parser = ConfigParser()
                with codecs.open(event.src_path, 'r', encoding='UTF-8-sig') as f:
                    self.parser.readfp(f)
            except:
                print("Failed to open ini-file \"%s\"" %event.src_path)
                print("--> Be sure file is encode as \"UTF-8 BOM\"")
                print("--------------------------------------------------\n\n")
                return
        
            
            if self.parser.has_option('General', 'show') != True:
                print("Failed to read variable \"show\" in section [General]")
                return
            
            
            show = self.parser.get('General', 'show')          
            if show.lower() == 'time':
                self.alarmSound.stop()
                self.controller.show_frame(ScreenClock)
                self.HDMIout.set_Visual('On')
             
            if show.lower() == 'slideshow':
                self.alarmSound.stop()
                self.controller.show_frame(ScreenSlideshow)
                self.HDMIout.set_Visual('On')   
                               
            if show.lower() == 'off':  
                self.alarmSound.stop()                  
                self.controller.show_frame(ScreenOff)
                self.HDMIout.set_Visual('Off')

        
            if show.lower() == 'object':
                # get information from ini-file
                try:    AddMsg       = self.parser.get('ObjectInfo', 'entire_msg')
                except: AddMsg       = ""
                
                try:    picture_1    = self.parser.get('ObjectInfo', 'picture_1')
                except: picture_1    = ""
                
                try:    picture_2    = self.parser.get('ObjectInfo', 'picture_2')
                except: picture_2    = ""
                
                try:    cropPicture  = self.parser.getboolean('ObjectInfo', 'crop_picture')
                except: cropPicture  = True
                
                try:    category     = self.parser.get('ObjectInfo', 'category')
                except: category     = ""
                
                try:    sound        = self.parser.get('ObjectInfo', 'sound')
                except: sound        = "None"
                
                try:    repeat       = self.parser.getint('ObjectInfo', 'repeat')
                except: repeat       = 1
                
                try:    showPB       = self.parser.getboolean('ObjectInfo', 'show_progress')
                except: showPB       = False
                
                try:    timePB       = self.parser.getint('ObjectInfo', 'progresstime')
                except: timePB       = 0
  
                try:    showRO       = self.parser.getboolean('ObjectInfo', 'show_responseOrder')
                except: showRO       = False
                
                equipment = {}
                for x in range(1,10):
                    s = (('equipment_%01i') %(x))
                    try:    equipment[x] = self.parser.get('ObjectInfo',s)
                    except: equipment[x] = ""
                               
                # set ScreenObject as active frame and set addresses
                self.controller.show_frame(ScreenObject)
                frame = self.controller.getActScreen()
                # first configure
                frame.configure(alarmMessage      = AddMsg,
                                picture_1         = picture_1,
                                picture_2         = picture_2,
                                cropPicture       = cropPicture,
                                category          = category,
                                progressBarTime   = timePB,
                                responseOrder     = equipment)
                # then start
                frame.configure(showProgressBar   = showPB,
                                showResponseOrder = showRO)
    
                
                # enable television
                self.HDMIout.set_Visual('On')
                
                # set sound
                if sound.lower() != 'none':
                    self.alarmSound.loadMusic(sound)
                    self.alarmSound.start(loops=repeat, start=0, delay=2, pause=15)
                else:
                    self.alarmSound.stop()
                
            if show.lower() == 'quit':
                self.alarmSound.stop()
                self.HDMIout.set_Visual('On')
                self.controller.exit(self)

    
######################################################################## 
class SwitchTelevision:
    def __init__(self):
        self.__actGraficOutput      = 'On'
        self.__actTelevisionState   = 'Off'
        
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
        
    #----------------------------------------------------------------------
    def get_Visual(self):
        """
        Return the status of the graphical output. If CEC is enabled, both
        (HDMI output and television on) has to be enabled, otherwise 'Off'
        will returned if at least on is disabled.
        """
        if cec_enable == True:
            return self.__actGraficOutput & self.__actTelevisionState
        else:
            return self.__actGraficOutput
                                        
    #----------------------------------------------------------------------
    def set_Visual(self, state):
        """
        Activate or deactivate the graphical output to force monitor to
        standby. If CEC is enabled, the television is triggered too,
        otherwise only the graphic output is driven.
        """
        self.__switchGraficOutput(newState = state)
            
    #----------------------------------------------------------------------        
    def __switchGraficOutput(self, newState):
        
        if newState == 'On':
            '''
            ORDER:
            First enable the HDMI port and the switch the TV on if
            availalbe. If done otherwise, the cec command can't be
            transmittet over a deactivatet HDMI port.
            ''' 
            if (stdbyEnable == True) and (os.name == 'posix'):
                if self.__actGraficOutput != newState:
                    try:    subprocess.call(["/opt/vc/bin/tvservice", "-p"])
                    except: pass
                    try:    subprocess.call(["sudo", "/bin/chvt", "6"])
                    except: pass
                    try:    subprocess.call(["sudo", "/bin/chvt", "7"])
                    except: pass
                    self.__actGraficOutput = newState
            
            if cecEnable == True:
                print("Switch TV on")
                cecObj.ProcessCommandActiveSource()
            
        if newState == 'Off':  
            '''
            ORDER:
            First switch of the TV with the CEC commandos if availalbe
            and then disable the HDMI port. If done otherwise, the
            cec command can't be transmittet over a deactivatet HDMI
            port.
            '''          
            if cecEnable == True: 
                print("Switch TV off") 
                cecObj.ProcessCommandTx("10:36")  

            if (stdbyEnable == True) and (os.name == 'posix'):
                if self.__actGraficOutput != newState:
                    try:    subprocess.call(["/opt/vc/bin/tvservice", "-o"])
                    except: pass
                    self.__actGraficOutput = newState
               
    #----------------------------------------------------------------------                
    def __switchTelevisionState(self, newState):
        
        if newState == 'On':
            subprocess.call(["echo", "on 0", "|", "cec-client", "-s"])
        else:
            subprocess.call(["echo", "standby 0", "|", "cec-client", "-s"])


########################################################################
def log_callback(level, time, message):
    return cecObj.LogCallback(level, time, message)

########################################################################    
def switchScreenAfterWhile():
    
    # Only adapt the screen if no other change
    # was requested by the user
    if (app.startTime+2) <= app.lastChange:
        print(app.startTime)
        print(app.lastChange)
        return
    
    if switchToScreen.lower() == 'time':
        eventHandler.alarmSound.stop()
        app.show_frame(ScreenClock)
        eventHandler.HDMIout.set_Visual('On')
     
    if switchToScreen.lower() == 'slideshow':
        eventHandler.alarmSound.stop()
        app.show_frame(ScreenSlideshow)
        eventHandler.HDMIout.set_Visual('On')   
                       
    if switchToScreen.lower() == 'off':  
        eventHandler.alarmSound.stop()                  
        app.show_frame(ScreenOff)
        eventHandler.HDMIout.set_Visual('Off') 
        
######################################################################## 
def readConfigIniFile():
    # force python to use the global variables instead of creating
    # them localy
    global observingPathName
    global observingFileName
    global fullscreenEnable
    global switchScreenAfter
    global switchToScreen
    global cecEnable
    global stdbyEnable
    global cecRebootInMinutes
          
    # Check if config.ini file exist
    configPath = os.path.join(wdr, 'config.ini')
    if os.path.isfile(configPath) != True:
        # quit skript due to an error
        errorMsg = ("The file \"config.ini\" is missing. Be sure this"
                    "file is in the same directory like this python-script")
        print ("ERROR: %s" %errorMsg)
        return 'IniFileNotFound'     
    
    # config.ini file exist, going to read the data
    sysconfig = ConfigParser()
    with codecs.open(configPath, 'r', encoding='UTF-8-sig') as f:
        sysconfig.readfp(f)
    
    # read informations which are required
    try:
        observingPathName = sysconfig.get('General', 'observing_path')
        observingFileName = sysconfig.get('General', 'observing_file')
    except:
        errorMsg = ('An unexpected error occurred while reading config.ini')
        print ("ERROR: %s" %errorMsg)
        return 'CouldNotReadIniFile'
    
    # Check if the observation-directory exist. Otherwise the observer
    # will raise a FileNotFoundError
    if os.path.isdir(observingPathName) != True:
        # quit script due to an error
        errorMsg = ("The directory \"%s\" for observation is missing." %observingPathName)  
        print ("ERROR: %s" %errorMsg) 
        return 'PathDoesNotExist'   
                
    '''
    Read variables with lower priority. 
    If not available, work with standard values
    '''
    
    # [Visual] group 
    try:    fullscreenEnable    = sysconfig.getboolean('Visual', 'fullscreen')
    except: fullscreenEnable    = False    
    try:    switchScreenAfter   = sysconfig.getint('Visual', 'switchScreenAfter')
    except: switchScreenAfter   = 0   
    try:    switchToScreen      = sysconfig.get('Visual', 'switchToScreen')
    except: switchToScreen      = ScreenOff
    
    # [Power] group   
    try:    cecEnable           = sysconfig.getboolean('Power', 'cec_enable')
    except: cecEnable           = False   
    try:    stdbyEnable         = sysconfig.getboolean('Power', 'stdby_enable')
    except: stdbyEnable         = False   
    try:    cecRebootInMinutes  = sysconfig.getint('Power', 'cec_reboot_after_minutes')
    except: cecRebootInMinutes  = 0

    return True

########################################################################          
if __name__ == "__main__":

    # Hint to GNU copy left license
    print("\n")
    print("+-------------------------------------------------+")
    print("| FireFinder Copyright (C) 2015  Michael Anderegg |")
    print("| This program comes with ABSOLUTELY NO WARRANTY. |")
    print("| This is free software, and you are welcome to   |")
    print("| redistribute it under certain conditions.       |")
    print("+-------------------------------------------------+")
    print("\n\n")
    
    # store working directory
    try:    wdr = os.path.dirname( __file__ )
    except: wdr = os.getcwd()
    
    # Read config.ini File & check for failure
    returnValue = readConfigIniFile()
    if returnValue is not True:
        app = tk.Tk()   # Create a tkinter to put failure message on screen
        if returnValue == 'IniFileNotFound':
            errorMessage = ('Die Datei config.ini wurde nicht gefunden. '
                            'Stelle sicher dass sich die Datei im selben '
                            'Ordner befindet wie die Datei \"run.py\"')
        elif returnValue == 'CouldNotReadIniFile':
            errorMessage = ('Die Datei config.ini konnte nicht gelesen '
                            'werden. Stelle sicher, dass in der Gruppe '
                            'General die Variablen richtig aufgeführt '
                            'sind\n\n[General]\nobserving_path = <Kompletter '
                            'Pfad>\nobserving_file   = <Dateiname mit Endung>')
        elif returnValue == 'PathDoesNotExist':
            errorMessage = ('Der in der config.ini Datei angegebene Pfad'
                            '\n\n\"%s\"\n\nwurde nicht gefunden. Stelle '
                            'der Pfad korrekt ist. Die Gross- / Klein'
                            'sicher das schreibung muss beachtet werden.' 
                            %observingPathName)       
        errorCanvas = tk.Canvas(app                                     , 
                                width  = int(app.winfo_screenwidth()/2) , 
                                height = int(app.winfo_screenheight()/2),
                                background ='red') 
        errorText = errorCanvas.create_text(
                                int(app.winfo_screenwidth()/4)      , 
                                int(app.winfo_screenwidth()/8)      ,
                                text   = "!! Schwerer Systemfehler !!\n\n%s" %errorMessage,                              
                                font=('arial', 30)                  ,                 
                                width=int(app.winfo_screenwidth()/2))
        errorCanvas.pack(side='top') 

    else:            
        # Create some objects
        app             = FireFinderGUI()
        eventHandler    = MyHandler(app)
        observer        = Observer()
        
        # create a object to libcec
        if (cec_lib_available==True) and (cecEnable==True):
            print("Enable CEC")
            cecObj = CecClient()
            cecObj.SetLogCallback(log_callback)
            cecObj.InitLibCec()
        else:
            cecEnable = False # Force to False if there was an error with the cec-lib
        
        if switchScreenAfter is not 0:
            switchTimeInSeconds = switchScreenAfter * 1000
            app.after(switchTimeInSeconds,switchScreenAfterWhile)
    
        # configure the observer thread and start it afterward
        observer.schedule(eventHandler, observingPathName, recursive=False)
        observer.start()   
    
    app.mainloop()
