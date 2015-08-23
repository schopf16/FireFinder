#!/usr/bin/env python
# -*- coding: UTF-8-*-

'''
    Copyright (C) 2015  Michael Anderegg

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

from configparser       import ConfigParser
from watchdog.observers import Observer
from watchdog.events    import FileSystemEventHandler
from PIL                import ImageTk, Image
#from tkinter            import ttk
from itertools          import cycle

# local classes
from firefinder.sound              import alarmSound
from firefinder.clock              import ScreenClock
from firefinder.progressbar        import progressBar

#from cgitb import text


LARGE_FONT= ("Verdana", 12)

########################################################################
""" Some global settings. They include namely settings from the """
""" config.ini file which is read in at the beginning """

CEC_on_script   = 0
CEC_off_script  = 0

""" Visual settings """
fullscreen      = False  

""" Power settings """
cec_enable      = False
stdby_enable    = False

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
        
        # Set actual window to fullscreen and bind the "Escape"
        # key with the function quit option
        self.title("FireFinder")
        
        ''' Sets focus to the window. '''
        self.focus_set()
        
        ''' Remove mouse cursor '''
        self.config(cursor="")
        
        ''' Removes the native window boarder. '''
        self.overrideredirect(fullscreen)
        
        ''' Disables resizing of the widget.  '''
        self.resizable(False, False)

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        print(("Screensize is: %d x %d pixels") %(w, h))
        self.geometry("%dx%d+0+0" % (w, h))
#        self.wm_state('zoomed')

        """ Bind Escape tap to the widget quit method """
        self.bind("<Escape>", lambda e: e.widget.quit())
        
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        self.container = tk.Frame(self)        
        self.container.pack(side="top", fill="both", expand = True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frame = ""
 
#        self.frames = {}
 
#         for F in (ScreenOff, 
#                   ScreenObject, 
#                   ScreenTruck,
#                   ScreenClock,
#                   ScreenSlidshow):
#  
#             frame = F(self.container, self)
#  
#             self.frames[F] = frame
#  
#             frame.grid(row=0, column=0, sticky="nsew")
 
        self.show_frame(ScreenOff)
        
    #----------------------------------------------------------------------
    def show_frame(self, cont):
 
        self.actScreen = cont
        self.frame = cont(self.container, self)
        self.frame.grid(row=0, column=0, sticky="nsew")
#        frame = self.frames[cont]
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
        self.eventBar = tk.Canvas(self                            , 
                                  width=self.winfo_screenwidth()  , 
                                  height = barHeight              , 
                                  highlightthickness = 0          ) 
        self.eventBarImg = self.eventBar.create_image(0, 0, anchor = 'nw') 
        self.eventBarTxt = self.eventBar.create_text(self.winfo_screenwidth()/2, 8 ) 
        self.eventBar.itemconfig(self.eventBarTxt                , 
                                 fill = "black"                  , 
                                 anchor = 'n'                    , 
                                 font=('Arial', 70)              ,
                                 width = self.winfo_screenwidth(),
                                 justify = 'center'              ,
                                 text    = 'Lade Einsatz...') 
        self.eventBar.place(x=0, y=0) 


        """ Create a label for the left picture """
        self.route = tk.Label(self, bd=0, background='black')
        self.route.place(x=0, y=barHeight, anchor='nw')
        
        """ Create a label for the right picture """
        self.detail = tk.Label(self, bd=0, background='black')
        self.detail.place(x=self.winfo_screenwidth(), y=barHeight, anchor='ne') 
        
        self.myPB = progressBar(self,
                                wsize = self.winfo_screenwidth(), 
                                hsize = 100, 
                                bg = 'slate gray', 
                                fg = 'red', 
                                value= 0, 
                                maximum=100, 
                                wdr = wdr)
                
        
        self.bartime = 0
        self.showbar = 0
        self.pb_Time = 0
        self.pb_Act  = 0
        self.pb_Step = 0
       
        self.poll()

    
    #----------------------------------------------------------------------     
    def setAddress(self                 , 
                   AlarmMsg     = 'None',
                   picture_1    = ""    ,
                   picture_2    = ""    ,
                   overlay      = False ,
                   category     = ""    ,
                   bartime      = 0     ,
                   showbar      = False):
        
        '''
        AlarmMsg    Set the actual Alarm Message received from the
                    control room
        picture_1   Name and type of the picture. If picture_2 is
                    empty, this picture is shown as fullscreen over
                    the fill width of the screen
        picutre_2   Name and type of the picutre. If available, the
                    screen is splited into two parts where picture_1
                    is shown on the left side while picutre_2 is shown
                    on the right side of the screen.
        overlay     If overlay is set to True, the picture_1 is shown as
                    fullscreen over the full width of the screen while 
                    picture_2 is shown on the left bottom corner, raised
                    over picture_1

        '''
        
        self.showbar = showbar
        
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
        barHeight = self.eventBar.winfo_height()
        picHeight = self.winfo_screenheight() - barHeight - (int(showbar) * 100)
        picWidth  = self.winfo_screenwidth() 
        
        # if picture 2 is empty, show picture 1 as fullscreen
        if (picture_2 != "") and (overlay == False):
            picWidth = picWidth / 2     
            
              
        """ change first picture """      
        path = os.path.join(inifile_path, picture_1)
        if os.path.isfile(path) == True:   
            self.routeImg = createImage(self, path=path, width=picWidth, height=picHeight, crop=True)
        else:     
            self.routeImg = createImage(self, path=noImage, width=picWidth, height=picHeight, keepRatio=False)             
        self.route["image"] = self.routeImg
        
        
        """ change second picture """ 
        if picture_2 != "":     
            path = os.path.join(inifile_path, picture_2)
            if os.path.isfile(path) == True:  
                self.detailImg = createImage(self, path=path, width=picWidth, height=picHeight, crop=True)
            else:     
                self.detailImg = createImage(self, path=noImage, width=picWidth, height=picHeight, keepRatio=False)         
            self.detail["image"] = self.detailImg
    
       
        # The time has to be greater than 0 Seconds
        if bartime == 0:
            self.showbar = False
                   
        if self.showbar == False: 
            self.myPB.forget()   
        else:
            self.pb_Time     = bartime*10           # Amount of 100mS Ticks
            self.pb_Act      = 0                    # Start position
            self.pb_Step     = self.winfo_screenwidth() / self.pb_Time   # whide at each Tick
            self.myPB.setValue(value=self.pb_Act, maximum=self.winfo_screenwidth())
            self.myPB.place(x=0, y=self.winfo_screenheight()-100)            

            
    #----------------------------------------------------------------------
    def poll(self):
        if self.showbar == True:
            if self.pb_Act < self.pb_Time :
                self.pb_Act += 1                 
                if self.pb_Act < (self.pb_Time * 0.9):                
                    self.myPB.step(self.pb_Step, 'red')
                    self.myPB.text("Warten bis TLF voll")
                elif self.pb_Act < (self.pb_Time * 0.97):    
                    self.myPB.step(self.pb_Step, 'orange')
                    self.myPB.text("Bereitmachen, auch wenn nicht voll")
                else:
                    self.myPB.step(self.pb_Step, 'green')
                    self.myPB.text("und gezupft...")
        self.after(100,self.poll)   


########################################################################
class ScreenTruck(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        tk.Frame.config(self, bg='black')
        
        self.truckcollection = tk.Frame(self, background='gray')
        self.truckcollection.pack(side='bottom', fill='both')
        
        # Create a set of 6 labels to hold the truck and trailer-images
        self.equipment    = {}
        self.equipmentImg = {}
        for x in range(1,12):
            self.equipment[x] = tk.Label(self.truckcollection, background='gray')
            self.equipment[x].pack(side='left', fill='both')          

    #----------------------------------------------------------------------   
    def setTruck(self, equipment):
        
        # generate the truck pictures concerning the ini-file
        for x in equipment:
            path = os.path.join(wdr, 'firefinder', 'pic', equipment[x])
            self.equipmentImg[x] = createImage(self, path, height=100)
            self.equipment[x]["image"] = self.equipmentImg[x]
                   
         
########################################################################       
class MyHandler(FileSystemEventHandler):
    def __init__(self, controller):
        
        """Constructor"""
        self.controller = controller
        self.HDMIout    = SwitchTelevision()
        

        self.alarmSound   = alarmSound( os.path.join(wdr, 'sound') )
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
                print("show slideshow")
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
                
                try:    OverviewPic  = self.parser.get('ObjectInfo', 'picture_route')
                except: OverviewPic  = ""
                
                try:    DetailPic    = self.parser.get('ObjectInfo', 'pciture_detail')
                except: DetailPic    = ""
                
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
                               
                # set ScreenObject as active frame and set addresses
                self.controller.show_frame(ScreenObject)
                self.controller.frame.setAddress(  AlarmMsg    = AddMsg,
                                                   picture_1   = OverviewPic,
                                                   picture_2   = DetailPic,
                                                   category    = category,
                                                   bartime     = timePB,
                                                   showbar     = showPB)
                
                # enable television
                self.HDMIout.set_Visual('On')
                
                # set sound
                if sound.lower() != 'none':
                    self.alarmSound.loadMusic(sound)
                    self.alarmSound.start(loops=repeat, start=0, delay=2, pause=15)
                else:
                    self.alarmSound.stop()
                
            if show.lower() == 'truck':
                self.alarmSound.stop()
                
                equipment = {}
                for x in range(1,12):
                    s = (('equipment_%01i') %(x))
                    try:    equipment[x] = self.parser.get('TruckInfo',s)
                    except: equipment[x] = ""
                
                self.controller.show_frame(ScreenTruck)
                self.controller.frame.setTruck (equipment = equipment) 
                
                
                self.HDMIout.set_Visual('On')
                print("show truck")
                
            if show.lower() == 'quit':
                self.alarmSound.stop()
                self.HDMIout.set_Visual('On')
                print("Try to close program")
                os._exit(0)
  

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
        
        if cec_enable == True:
            self.__switchTelevisionState(newState = state)
            
    #----------------------------------------------------------------------        
    def __switchGraficOutput(self, newState):
        
        if newState == 'On':
            if os.name == 'posix':
                if self.__actGraficOutput != newState:
                    try:    subprocess.call(["/opt/vc/bin/tvservice", "-p"])
                    except: pass
                    try:    subprocess.call(["sudo", "/bin/chvt", "6"])
                    except: pass
                    try:    subprocess.call(["sudo", "/bin/chvt", "7"])
                    except: pass
                self.__actGraficOutput = newState
            
        if newState == 'Off':
            if os.name == 'posix':
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
#         print("Da kommt noch was")
            
def createImage(self, path, width=0, height=0, crop=False, keepRatio=True):
    """
    The function creates a ImageTk.PhotoImage from a given picture with
    path. If width and height of the picture is known, the picture can be
    crop. The function will automatically crop the image around the middle
    to fit onto the given width and height.
    If one side of the picture is unknown, the function will fit the image
    to the given side while the other side will grove or reduce to fit to
    the resolution of the picture.
    
    crop        If set to True, the function will resize the image to fit
                as god as possible to the given width and height. If the 
                image is on one side bigger than expected, the side will be
                croped on both sides.
                
    keepRatio   If set to True, the function will resize the image while
                keeping the same resolution. If set to False, the fuction
                will resize the image to the given width and height even if
                the ratio is not the same.

                
    """
    
    # check if a file is found at given path
    if os.path.isfile(path) != True:  
        return ""
    
    try:             
        image = Image.open(path)  
    except:
        print("Failed to open picture")
        return ""
    
    # force dimension to integer
    width  = int( width  )
    height = int( height )
    
    # if one axes is equal, set this to maximum
    if width  == 0: width = self.winfo_screenwidth()
    if height == 0: height = self.winfo_screenheight()

    # define which axes is the base
    if ((width / image.size[0]) * image.size[1]) > height: 
        base = 'height'
    else:
        base = 'width'
    
    # If the picture can crop afterwards, switch the base
    if crop == True:
        if base == 'height':    base = 'width'
        else:                   base = 'height'
    
    # Calculate the new dimenson according the given values
    if keepRatio == True:     
        if base == 'width':        
            wpercent = (width / float(image.size[0]))
            hsize    = int( (float(image.size[1]) * float(wpercent)) )
            wsize    = int( width )
        else:          
            hpercent = (height / float(image.size[1]))
            wsize = int( (float(image.size[0]) * float(hpercent)) )
            hsize = int( height )
    else:
        wsize = int( width )
        hsize = int( height )
                                       
    # Resize the image
    image = image.resize((wsize, hsize), Image.ANTIALIAS)        
            
    if crop == True:
        # Crop image if its bigger than expected
        wOffset = int( (image.size[0] - width ) / 2 )
        hOffset = int( (image.size[1] - height) / 2 )  
        image = image.crop((wOffset, hOffset, wOffset + width, hOffset + height)) 
               
    return ImageTk.PhotoImage(image)   

                
########################################################################          
if __name__ == "__main__":
    
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
    try:    deltahours = sysconfig.getint('Visual', 'time_shift_UTC')
    except: pass
    
    try:    fullscreen = sysconfig.getboolean('Visual', 'fullscreen')
    except: pass
        
    try:    cec_enable   = sysconfig.getboolean('Power', 'cec_enable')
    except: pass
    
    try:    stdby_enable = sysconfig.getboolean('Power', 'stdby_enable')
    except: pass
    
    # Create some objects
    app             = FireFinderGUI()
    eventHandler    = MyHandler(app)
    observer        = Observer()  
    
    # configure the observer thread and start it afterward
    observer.schedule(eventHandler, inifile_path, recursive=False)
    observer.start()   
    
    app.mainloop()
