#!/usr/bin/env python
# -*- coding: UTF-8-*-

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
import random
import codecs
import tkinter as tk
import subprocess
import time
import functools
#import firefinder.miscellaneous as fms


from configparser       import ConfigParser
from watchdog.observers import Observer
from watchdog.events    import FileSystemEventHandler
from PIL                import ImageTk, Image
#from tkinter            import ttk
from itertools          import cycle

# local classes
from firefinder.sound         import alarmSound
from firefinder.clock         import ScreenClock
from firefinder.footer        import ProgressBar, ResponseOrder
from firefinder.miscellaneous import createImage

try:   
    from firefinder.cecLibrary     import CecClient
    cec_lib_available = True
except:
    print("Failed load CEC")
    cec_lib_available = False
    


LARGE_FONT= ("Verdana", 12)

########################################################################
""" Some global settings. They include namely settings from the """
""" config.ini file which is read in at the beginning """

CEC_on_script     = 0
CEC_off_script    = 0

""" Visual settings """
fullscreen        = False  
switchScreenAfter = 0
switchToScreen    = ''


""" Power settings """
cec_enable        = False
stdby_enable      = False

""" Path's """
ffLogo      = 'firefinder/pic/Logo.png'     # Firefighter Logo
noImage     = 'firefinder/pic/bg/no_image.png'
HDMI_script = 'script/reactivate_screen.sh' # Script to enable HDMI output

########################################################################
class FireFinderGUI(tk.Tk):

    def __init__(self, *args, **kwargs):
        """Constructor"""
        tk.Tk.__init__(self, *args, **kwargs)
        
        # Store actual shown screen
        self.actScreen  = 0
        self.startTime  = int(time.time())
        self.lastChange = 0
        
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
        self.overrideredirect(fullscreen)
        
        ''' Disables resizing of the widget.  '''
        self.resizable(False, False)

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        print(("Screensize is: %d x %d pixels") %(w, h))
        self.geometry("%dx%d+0+0" % (w, h))

        ''' Sets focus to the window to catch <Escape> '''
        self.focus_set()
        
        """ Bind Escape tap to the widget quit method """
        self.bind("<Escape>", lambda e: self.quit())
        
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        self.container = tk.Frame(self)        
        self.container.pack(side="top", fill="both", expand = True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frame = ""
 
        self.show_frame(ScreenOff)

    #----------------------------------------------------------------------
    def show_frame(self, cont):
 
        self.actScreen = cont
        self.lastChange= int(time.time())
        self.frame = cont(self.container, self)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.tkraise()
        
########################################################################        
class ScreenOff(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        self.config(background='black')
        
        screenWidth = self.master.winfo_screenwidth()
        screenHigh  = self.master.winfo_screenheight()
        
        # Create a logo with the firefighter Emblem
        path = os.path.join(wdr, ffLogo)
        if os.path.isfile(path) == True:     
            # create screen for object
            self.image = createImage(self, path=path, width=screenWidth-20, height=screenHigh-20) 
            
            ffEmblem = tk.Label(self)
            ffEmblem["bg"]     = "black"
            ffEmblem["width"]  = screenWidth
            ffEmblem["height"] = screenHigh                        
            ffEmblem["image"] = self.image
            ffEmblem.pack()
        else:
            canvas = tk.Canvas(self, 
                               width               = screenWidth,
                               height              = screenHigh,
                               background          = 'black',
                               highlightthickness  = 0)
            canvas.create_line(0, 0, screenWidth, screenHigh, fill='red', width=5)
            canvas.create_line(screenWidth, 0, 0, screenHigh, fill='red', width=5)
            canvas.pack()             

########################################################################        
class ScreenSlidshow(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        self.config(background='black')

        # create a lable to show the image
        self.picture_display = tk.Label(self)
        self.picture_display["bg"]     = "black"
        self.picture_display["fg"]     = "white"
        self.picture_display["width"]  = self.master.winfo_screenwidth()
        self.picture_display["height"] = self.master.winfo_screenheight() 
        self.picture_display["font"]   = ("Arial", 60) 
        self.picture_display.pack()
        
        # set milliseconds time between slides
        self.delay = 3600 #delay
        
        # store path where the pictures for the 
        # the slideshow are stored
        self.pathToImage = os.path.join(inifile_path, 'Slideshow') 
        
        # rebuild list of pictures
        self.pictures     = 0
        self.file_names   = []
        self.fileInFolder = 0
              
        # run slideshow
        self.show_slides()
            
    #----------------------------------------------------------------------        
    def show_slides(self):

        # check if slideshow directory exists and create it if necessary 
        if not os.path.exists(self.pathToImage):
            os.makedirs(self.pathToImage)

        # check if there are new images or some are deleted
        countFile = len([name for name in os.listdir(self.pathToImage) if os.path.isfile(os.path.join(self.pathToImage, name))])
        if countFile != self.fileInFolder:
            
            # delete the list
            self.file_names = []
            
            # load all images which could be shown
            included_extenstions = ['.jpg','.jpeg','.bmp','.png','.gif','.eps','.tif','.tiff'] ;
            for file in os.listdir(self.pathToImage):

                # get extension
                ext = os.path.splitext(file)[1]
                
                # check if extension is available
                if ext.lower() in included_extenstions:
                    self.file_names.append(os.path.join(self.pathToImage, file))

            # Check if list is not empty, otherwhise do not proceed
            if self.file_names:
                # shuffle the list randomly
                random.shuffle( self.file_names )
                # put list in a cycle
                self.cycledList = cycle(self.file_names)
                
            # store the amount of files
            self.fileInFolder = countFile
         
        # check if there is at least an image available
        if len(self.file_names):
            self.pictures = createImage(self, path=next(self.cycledList))          
            self.picture_display.config(image=self.pictures)
            self.picture_display.config(text = "")
        else:            
            self.picture_display.config(image= "")
            self.picture_display.config(text = "Keine Bilder zum Anzeigen :-(")      
        
        # wait to show the next picture
        self.after(self.delay, self.show_slides)
      
        
########################################################################
class ScreenObject(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        self.AudioIsOn = 0
        
        """
        Event bar
        On the top of the screen, there is the event bar. It hold's the 
        main information about the mission. Depend of the happening, the
        color of the background may change. Due to this, it is more simple
        to distinguish between the missions. Example
        urgend       -- red.png
        semi urgend  -- blue.png
        neighborhood -- green.png
        unknown      -- white.png       
        """
        barHeight = 220
        
        self.eventBgColor={}
        for x in ['red', 'blue', 'green', 'white']:
            path = os.path.join(wdr, 'firefinder', 'pic', 'bg', ('%s.png') %(x)) 
            if os.path.isfile(path) == True:               
                logo = Image.open(path)
                logo = logo.resize((self.winfo_screenwidth(), barHeight), Image.ANTIALIAS)
                self.eventBgColor[x] = ImageTk.PhotoImage(logo) 
        
        # Create a canvas to hold the top event bar
        self.eventBar = tk.Canvas(self                               , 
                                  width  = self.winfo_screenwidth()  , 
                                  height = barHeight                 , 
                                  highlightthickness = 0             ) 
        self.eventBarImg = self.eventBar.create_image(0, 0, anchor = 'nw') 
        self.eventBarTxt = self.eventBar.create_text(self.winfo_screenwidth()/2, 8 ) 
        self.eventBar.itemconfig(self.eventBarTxt                 , 
                                 fill   = "black"                 , 
                                 anchor = 'n'                     , 
                                 font   = ('Arial', 70)           ,
                                 width  = self.winfo_screenwidth(),
                                 justify = 'center'               ,
                                 text    = 'Lade Einsatz...'      ) 
        self.eventBar.place(x=0, y=0) 

        self.mapCan = tk.Canvas(self, 
                                width               = self.winfo_screenwidth()             , #WIDTH,
                                height              = self.winfo_screenheight() - barHeight, #HEIGHT,
                                background          = 'black'                              ,
                                highlightthickness  = 0                                    )
        self.mapCan.place(x=0, y=barHeight)
        
        """ Create a label for the left picture """
        self.pic1 = tk.Label(self.mapCan, bd=0, background='black', foreground='black')
        self.pic1.place(x=0, y=barHeight, anchor='nw')
        
        """ Create a label for the right picture """
        self.pic2 = tk.Label(self.mapCan, bd=0, background='black', foreground='black')
        self.pic2.place(x=self.winfo_screenwidth(), y=barHeight, anchor='ne') 
    
    #----------------------------------------------------------------------     
    def setAddress(self                 , 
                   AlarmMsg     = 'None',
                   picture_1    = ""    ,
                   picture_2    = ""    ,
                   overlay      = False ,
                   cropPicture  = True  ,
                   category     = ""    ,
                   bartime      = 0     ,
                   showbar      = False ,
                   showRO       = False , 
                   heightPB     = 100   ,  
                   equipmentRO  = 0     ):
        
        '''
        AlarmMsg    Set the actual Alarm Message received from the
                    control room
        picture_1   Name and type of the left picture. If picture_2 is
                    empty, this picture is shown as fullscreen over
                    the full width of the screen
        picutre_2   Name and type of the picutre. If available, the
                    screen is splited into two parts where picture_1
                    is shown on the left side while picutre_2 is shown
                    on the right side of the screen.
        category    Set the background color of the AlarmMsg. This
                    allowes the incoming staff to distinguish easly
                    between the several alarm types. The following
                    backgrounds ar available:
                    red / blue / green / white
                    If non is selected, the background is set to white
        overlay     Can be True or False. If overlay is set to True, 
                    the picture_1 is shown as fullscreen over the full 
                    width of the screen while picture_2 is shown on the 
                    left bottom corner, raised over picture_1
        cropPicture Can be True or False. If set to True, the picutres 1 
                    and 2 where re-sized to fit to the given space and 
                    then crop on the side to prevent boarder around the 
                    pictures
        bartime     Set the time in seconds where the bar should be fully
                    fill. The bar starts red, turn into orange after 90%
                    of bartime and turn into green after 97%
        showbar     Can be True or False. If set to True, the the bar
                    diagram is shown on the bottom of the object frame.

        '''
        
        self.showbar    = showbar
        self.showRO     = showRO
        self.heightPB   = heightPB
        
        """ Set new message to the top red frame """ 
        # Set background of event bar depend of the category
        if category.lower() == 'red':
            self.eventBar.itemconfig(self.eventBarImg, image=self.eventBgColor['red'])
        elif category.lower() == 'blue':
            self.eventBar.itemconfig(self.eventBarImg, image=self.eventBgColor['blue'])
        elif category.lower() == 'green':
            self.eventBar.itemconfig(self.eventBarImg, image=self.eventBgColor['green'])
        else:
            self.eventBar.itemconfig(self.eventBarImg, image=self.eventBgColor['white'])
 
        # Set alarm message
        self.eventBar.itemconfig(self.eventBarTxt, text="%s" %AlarmMsg)
        
        # Calculate size of Images
        picHeight = self.mapCan.winfo_height() - (int(showbar)*100) - (int(showRO)*heightPB) - (int(showRO)*int(showRO)*5)
        picWidth  = self.mapCan.winfo_width() 
        
        # if picture 2 is empty, show picture 1 as fullscreen
        if (picture_2 != "") and (overlay == False):
            picWidth = picWidth / 2     
            
              
        """ change first picture """      
        path = os.path.join(inifile_path, picture_1)
        if os.path.isfile(path) == True:   
            self.pic1Img = createImage(self, path=path, width=picWidth, height=picHeight, crop=cropPicture)
        else:     
            self.pic1Img = createImage(self, path=noImage, width=picWidth, height=picHeight, keepRatio=False)             
        
        # reposition picture and put it on the screen
        self.pic1.place(    x = (picWidth/2)  - (self.pic1Img.width()/2), 
                            y = (picHeight/2) - (self.pic1Img.height()/2), 
                            anchor = 'nw')
        self.pic1["image"] = self.pic1Img
        
        
        """ change second picture """ 
        if picture_2 != "":     
            path = os.path.join(inifile_path, picture_2)
            if os.path.isfile(path) == True:  
                self.pic2Img = createImage(self, path=path, width=picWidth, height=picHeight, crop=cropPicture)
            else:     
                self.pic2Img = createImage(self, path=noImage, width=picWidth, height=picHeight, keepRatio=False) 
           
            # reposition picture and put it on the screen
            self.pic2.place(    x = (picWidth/2)  - (self.pic1Img.width()/2)  + picWidth, 
                                y = (picHeight/2) - (self.pic1Img.height()/2), 
                                anchor = 'nw')       
            self.pic2["image"] = self.pic2Img
    
        
        if self.showbar == True:
  
            self.progress = ProgressBar(master=self.mapCan              , 
                                        width=self.winfo_screenwidth()  , 
                                        height=100                      , 
                                        pixelPerSlice=1                 )
            self.progress.show(x=0, y=self.mapCan.winfo_height()-100-(int(showRO)*heightPB)-(int(showRO)*5), anchor='nw')
            self.progress.start(timeInSeconds=bartime, startValue=0)

        if self.showRO == True:
            self.responseOrder = ResponseOrder(master=self.mapCan       , 
                                        width=self.winfo_screenwidth()  , 
                                        height=heightPB                 )
            self.responseOrder.show(x=0                                 , 
                                    y=self.mapCan.winfo_height()-heightPB, 
                                    anchor='nw'                         )
            self.responseOrder.setTruck(equipment=equipmentRO)
            

########################################################################
# class ScreenTruck(tk.Frame):
# 
#     def __init__(self, parent, controller):
#         tk.Frame.__init__(self, parent)
#         tk.Frame.config(self, bg='black')
#         
#         self.truckcollection = tk.Frame(self, background='gray')
#         self.truckcollection.pack(side='bottom', fill='both')
#         
#         # Create a set of 6 labels to hold the truck and trailer-images
#         self.equipment    = {}
#         self.equipmentImg = {}
#         for x in range(1,12):
#             self.equipment[x] = tk.Label(self.truckcollection, background='gray')
#             self.equipment[x].pack(side='left', fill='both')          
# 
#     #----------------------------------------------------------------------   
#     def setTruck(self, equipment):
#         
#         # generate the truck pictures concerning the ini-file
#         for x in equipment:
#             path = os.path.join(wdr, 'firefinder', 'pic', equipment[x])
#             self.equipmentImg[x] = createImage(self, path, height=100)
#             self.equipment[x]["image"] = self.equipmentImg[x]
                   
         
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
        if os.path.split(event.src_path)[-1].lower() == inifile_name.lower():

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
                self.controller.show_frame(ScreenSlidshow)
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
                
                try:    overlayPic   = self.parser.getboolean('ObjectInfo', 'overlay_picture')
                except: overlayPic   = True
                
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
                
                try:    heightPB     = self.parser.getint('ObjectInfo', 'responseOrderHeight')
                except: heightPB     = 0
                
                equipment = {}
                for x in range(1,12):
                    s = (('equipment_%01i') %(x))
                    try:    equipment[x] = self.parser.get('ObjectInfo',s)
                    except: equipment[x] = ""
                               
                # set ScreenObject as active frame and set addresses
                self.controller.show_frame(ScreenObject)
                self.controller.frame.setAddress(  AlarmMsg     = AddMsg,
                                                   picture_1    = picture_1,
                                                   picture_2    = picture_2,
                                                   overlay      = overlayPic,
                                                   cropPicture  = cropPicture,
                                                   category     = category,
                                                   bartime      = timePB,
                                                   showbar      = showPB,
                                                   showRO       = showRO,
                                                   heightPB     = heightPB,
                                                   equipmentRO  = equipment)
                
                # enable television
                self.HDMIout.set_Visual('On')
                
                # set sound
                if sound.lower() != 'none':
                    self.alarmSound.loadMusic(sound)
                    self.alarmSound.start(loops=repeat, start=0, delay=2, pause=15)
                else:
                    self.alarmSound.stop()
                
#             if show.lower() == 'truck':
#                 self.alarmSound.stop()
#                 
#                 equipment = {}
#                 for x in range(1,12):
#                     s = (('equipment_%01i') %(x))
#                     try:    equipment[x] = self.parser.get('TruckInfo',s)
#                     except: equipment[x] = ""
#                 
#                 self.controller.show_frame(ScreenTruck)
#                 self.controller.frame.setTruck (equipment = equipment) 
#                 
#                 
#                 self.HDMIout.set_Visual('On')
#                 print("show truck")
                
            if show.lower() == 'quit':
                self.alarmSound.stop()
                self.HDMIout.set_Visual('On')
                print("Try to close program")
                os._exit(0)
  
######################################################################## 

    
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
        
#        if cec_enable == True:
#            self.__switchTelevisionState(newState = state)
            
    #----------------------------------------------------------------------        
    def __switchGraficOutput(self, newState):
        
        if newState == 'On':
            '''
            ORDER:
            First enable the HDMI port and the switch the TV on if
            availalbe. If done otherwise, the cec command can't be
            transmittet over a deactivatet HDMI port.
            ''' 
            if (stdby_enable == True) and (os.name == 'posix'):
                if self.__actGraficOutput != newState:
                    try:    subprocess.call(["/opt/vc/bin/tvservice", "-p"])
                    except: pass
                    try:    subprocess.call(["sudo", "/bin/chvt", "6"])
                    except: pass
                    try:    subprocess.call(["sudo", "/bin/chvt", "7"])
                    except: pass
                    self.__actGraficOutput = newState
            
            if cec_enable == True:
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
            if cec_enable == True: 
                print("Switch TV off") 
                cecObj.ProcessCommandTx("10:36")  

            if (stdby_enable == True) and (os.name == 'posix'):
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


# logging callback
def log_callback(level, time, message):
    return cecObj.LogCallback(level, time, message)

# key press callback
def key_press_callback(key, duration):
    return cecObj.KeyPressCallback(key, duration) 
    
def switchScreenAfterWhile():
    
    # Only adapt the screen if no other change
    # was requested by the user
    if (app.startTime+1) <= app.lastChange:
        print(app.startTime)
        print(app.lastChange)
        return
    
    if switchToScreen.lower() == 'time':
        eventHandler.alarmSound.stop()
        app.show_frame(ScreenClock)
        eventHandler.HDMIout.set_Visual('On')
     
    if switchToScreen.lower() == 'slideshow':
        eventHandler.alarmSound.stop()
        app.show_frame(ScreenSlidshow)
        eventHandler.HDMIout.set_Visual('On')   
                       
    if switchToScreen.lower() == 'off':  
        eventHandler.alarmSound.stop()                  
        app.show_frame(ScreenOff)
        eventHandler.HDMIout.set_Visual('Off')            

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

    #necessary to change working directory? Guess not!
    os.chdir(wdr)

      
    # Check if config.ini file exist
    configPath = os.path.join(wdr, 'config.ini')
    if os.path.isfile(configPath) != True:
        # quit skript due to an error
        print("The file \"config.ini\" is missing. Be sure this"
              "file is in the same directory like this python-script")     
        sys.exit("no config file found") 
    
    # config.ini file exist, going to read the data
    sysconfig = ConfigParser()
    sysconfig.read(configPath)
    
    # read informations which are required
    try:
        inifile_path = sysconfig.get('General', 'observing_path')
        inifile_name = sysconfig.get('General', 'observing_file')
    except:
        print ('An unexpected error occurred while reading config.ini')
    
    # Check if the observation-directory exist. Otherwise the observer
    # will raise a FileNotFoundError
    if os.path.isdir(inifile_path) != True:
        # quit script due to an error
        print("The directory \"%s\" for observation is missing." %inifile_path)     
        sys.exit("The directory for observation is missing") 
                
    # Read variables with lower priority. If not available, work with standard values
    
    try:    fullscreen = sysconfig.getboolean('Visual', 'fullscreen')
    except: pass
    
    try:    switchScreenAfter = sysconfig.getint('Visual', 'switchScreenAfter')
    except: switchScreenAfter = 0
    
    try:    switchToScreen    = sysconfig.get('Visual', 'switchToScreen')
    except: switchToScreen    = ''
        
    try:    cec_enable   = sysconfig.getboolean('Power', 'cec_enable')
    except: pass
    
    try:    stdby_enable = sysconfig.getboolean('Power', 'stdby_enable')
    except: pass
    
    # Create some objects
    app             = FireFinderGUI()
    eventHandler    = MyHandler(app)
    observer        = Observer()
    
    # create a object to libcec
    if (cec_lib_available==True) and (cec_enable==True):
        print("Enable CEC")
        cecObj = CecClient()
        cecObj.SetLogCallback(log_callback)
        cecObj.SetKeyPressCallback(key_press_callback)
        cecObj.InitLibCec()
    else:
        cec_enable = False # Force to False if there was an error with the cec-lib
    
    if switchScreenAfter is not 0:
        switchTimeInSeconds = switchScreenAfter * 1000
        app.after(switchTimeInSeconds,switchScreenAfterWhile)

    # configure the observer thread and start it afterward
    observer.schedule(eventHandler, inifile_path, recursive=False)
    observer.start()   
    
    app.mainloop()
