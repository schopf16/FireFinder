#!/usr/bin/env python
# -*- coding: UTF-8-*-

'''
Created on 10.06.2015

@author: andmi
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
from PIL                import ImageTk, Image
from tkinter            import ttk

# local classes
from sound              import alarmSound
from clock              import ScreenClock
from progressbar        import progressBar


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
ffLogo      = 'pic/Logo.png'                # Firefighter Logo
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
#        self.focus_force()
        
        ''' Removes the native window boarder. '''
        self.overrideredirect(fullscreen)
        
        ''' Disables resizing of the widget.  '''
        self.resizable(False, False)

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        print(w, h)
        self.geometry("%dx%d+0+0" % (w, h))
#        self.wm_state('zoomed')

        """ Bind Escape tap to the widget quit method """
        self.bind("<Escape>", lambda e: e.widget.quit())
        
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        
        container.pack(side="top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
 
        self.frames = {}
 
        for F in (ScreenOff, 
                  ScreenObject, 
                  ScreenTruck,
                  ScreenClock):
 
            frame = F(container, self)
 
            self.frames[F] = frame
 
            frame.grid(row=0, column=0, sticky="nsew")
 
        self.show_frame(ScreenOff)
        
    #----------------------------------------------------------------------
    def show_frame(self, cont):
 
        self.actScreen = cont
        frame = self.frames[cont]
        frame.tkraise()
    
    

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
            path = os.path.join(wdr, 'pic', 'bg', ('%s.png') %(x)) 
            if os.path.isfile(path) == True:               
                logo = Image.open(path)
                logo = logo.resize((self.winfo_screenwidth(), barHeight), Image.ANTIALIAS)
                self.eventBgColor[x] = ImageTk.PhotoImage(logo) 
        
        # Create a canvas to hold the top event bar
        self.eventBar = tk.Canvas(self                            , 
                                  width=self.winfo_screenwidth()  , 
                                  height = barHeight                    , 
                                  highlightthickness = 0          ) 
        self.eventBarImg = self.eventBar.create_image(0, 0, anchor = 'nw') 
        self.eventBarTxt = self.eventBar.create_text(15, 30 ) 
        self.eventBar.itemconfig(self.eventBarTxt                , 
                                 fill = "black"                  , 
                                 anchor = 'nw'                   , 
                                 font=('Arial', 60)              ,
                                 width = self.winfo_screenwidth(),
                                 justify = 'center'              ) 
        self.eventBar.place(x=0, y=0) 


        """ Create a label for the left picture """
        self.route = tk.Label(self, bd=0,  background='green')
        self.route.place(x=0, y=barHeight, anchor='nw')
        
        """ Create a label for the right picture """
        self.detail = tk.Label(self, bd=0,  background='green')
        self.detail.place(x=self.winfo_screenwidth(), y=barHeight, anchor='ne')
              
        
        """ Create styles for the Progressbar """
        redBar = ttk.Style()
        redBar.theme_use('default')
        redBar.configure("red.Horizontal.TProgressbar", foreground='red', background='red', thickness=100)
        
        oreBar = ttk.Style()
        oreBar.theme_use('default')
        oreBar.configure("orange.Horizontal.TProgressbar", foreground='orange', background='orange', thickness=100)
        
        greBar = ttk.Style()
        greBar.theme_use('default')
        greBar.configure("green.Horizontal.TProgressbar", foreground='green', background='green', thickness=100)
        
        
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
                   OverviewPic  = 0     ,
                   DetailPic    = 0     ,
                   category     = ""    ,
                   bartime      = 0     ,
                   showbar      = False):
        
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
        self.eventBar.itemconfig(self.eventBarTxt, justify = 'center', text="%s" %AlarmMsg)
        
        barHeight = self.eventBar.winfo_height()
        
        """ change detail picture """      
        path = os.path.join(inifile_path, DetailPic)
        picWidth  = self.winfo_screenwidth() / 2
        picHeight = self.winfo_screenheight() - barHeight - (int(showbar) * 100)
        print(picHeight)
        self.detailImg = createImage(self, path=path, width=picWidth, height=picHeight, crop=True)             
        self.detail["image"] = self.detailImg
        
        """ change route picture """      
        path = os.path.join(inifile_path, OverviewPic)
        picWidth  = self.winfo_screenwidth() / 2
        picHeight = self.winfo_screenheight() - barHeight - (int(showbar) * 100)
        print(picHeight)
        self.routeImg = createImage(self, path=path, width=picWidth, height=picHeight, crop=True)             
        self.route["image"] = self.routeImg
 
        
       
        # The time has to be greater than 0 Seconds
        if bartime == 0:
            self.showbar = False
                   
        if self.showbar == False: 
            print("Delete progress")
            self.myPB.forget()   
        else:
            print("Show progress")
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
        self.truck    = {}
        self.trail    = {} 
        self.truckImg = {}
        self.trailImg = {}    
        for x in range(1,7):
            self.truck[x] = tk.Label(self.truckcollection, background='gray')
            self.truck[x].pack(side='left', fill='both')
            self.trail[x] = tk.Label(self.truckcollection, background='gray')
            self.trail[x].pack(side='left')
            

    #----------------------------------------------------------------------   
    def setTruck(self, truck, trailer):
        
        # generate the truck pictures concerning the ini-file
        for x in truck:
            path = os.path.join(wdr, 'pic', truck[x])
            self.truckImg[x] = createImage(self, path, height=100)
            self.truck[x]["image"] = self.truckImg[x]
      
        # generate the trailer pictures concerning the ini-file
        for x in trailer:
            path = os.path.join(wdr, 'pic', trailer[x])
            self.trailImg[x] = createImage(self, path, height=100)
            self.trail[x]["image"] = self.trailImg[x]
       
         
########################################################################       
class MyHandler(FileSystemEventHandler):
    def __init__(self, controller):
        
        """Constructor"""
        self.controller = controller
        self.setAddress = self.controller.frames[ScreenObject].setAddress
        self.setTruck   = self.controller.frames[ScreenTruck].setTruck
        self.HDMIout    = SwitchTelevision()
        

        self.alarmSound   = alarmSound( os.path.join(wdr, 'sound') )
        self.lastModified = 0
        
        self.parser = ConfigParser()
           
    #----------------------------------------------------------------------
    def on_modified(self, event):
        # Check if the file has ben modified I'm looking for
        if os.path.split(event.src_path)[-1].lower() == inifile_name.lower():

            """
            Do to some reasons, the watchdog trigger the FileModifiedEvent
            twice. Therefore capture the time and ignore changes within
            the next second.
            """
            if self.lastModified >= int(time.time()): 
                return
             
            self.lastModified = int(time.time()) + 2

            # The parser-file has to be converted as UTF-8 file. Otherwise
            # special character like umlaut could not successfully read.
            
        
            try: 
                with open(event.src_path,'r', encoding='UTF-8-sig') as configfile:
                    self.parser.clear()       
                    self.parser.readfp(configfile)              
#                 self.parser.clear()
#                 self.parser.read(event.src_path, encoding='UTF-8-sig')
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
                
                print(showPB)
                # Change object data and put frame to front afterwards
                self.setAddress(AlarmMsg    = AddMsg,
                                OverviewPic = OverviewPic,
                                DetailPic   = DetailPic,
                                category    = category,
                                bartime     = timePB,
                                showbar     = showPB)       
                
                # set ScreenObject as active frame
                self.controller.show_frame(ScreenObject)
                
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
                
                truck = {}
                trail = {}
                for x in range(1,7): 
                    s = (('truck_%01i') %(x))
                    try:    truck[x] = self.parser.get('TruckInfo', s)
                    except: truck[x] = ""
                    s = (('truck_%01i_trailer') %(x))
                    try:    trail[x] = self.parser.get('TruckInfo', s)
                    except: trail[x] = ""
                    
                self.setTruck(truck = truck, trailer = trail)
                
                self.controller.show_frame(ScreenTruck)
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
        self.__pathToReactivateMonitor = os.path.join(wdr, HDMI_script)
        
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
            self.__switchMonitorState(newState = state)
            
    #----------------------------------------------------------------------        
    def __switchGraficOutput(self, newState):
        
        if newState == 'On':
            if self.__actGraficOutput != newState:
                try:    subprocess.check_output([self.__pathToReactivateMonitor], shell=True)
                except: print("error while script")
                self.__actGraficOutput = newState
            
        if newState == 'Off':
            if self.__actGraficOutput != newState:
                # Before disabling the graphic output, be sure there is a
                # shell-script for reactivation available
                if os.path.isfile(self.__pathToReactivateMonitor) == True:
                    try:    subprocess.call(["/opt/vc/bin/tvservice", "-o"])
                    except: pass
                    self.__actGraficOutput = newState
                else:
                    print("No file to reactivate graphical output")
                
    #----------------------------------------------------------------------                
    def __switchTelevisionState(self, newState):
        print("Da kommt noch was")
            
def createImage(self, path, width=0, height=0, crop=False):
    """
    The function creates a ImageTk.PhotoImage from a given picture with
    path. If width and height of the picture is known, the picture can be
    crop. The function will automatically crop the image around the middle
    to fit onto the given width and height.
    If one side of the picture is unknown, the function will fit the image
    to the given side while the other side will grove or reduce to fit to
    the resolution of the picture.
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
         
    if base == 'width':        
        wpercent = (width / float(image.size[0]))
        hsize    = int( (float(image.size[1]) * float(wpercent)) )
        wsize    = int( width )
    else:          
        hpercent = (height / float(image.size[1]))
        wsize = int( (float(image.size[0]) * float(hpercent)) )
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
