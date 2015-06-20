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
import sound
import time

from configparser       import ConfigParser
from watchdog.observers import Observer
from watchdog.events    import FileSystemEventHandler
from PIL                import ImageTk, Image
from datetime           import timedelta,datetime
from math               import sin, cos, pi
from tkinter            import ttk




LARGE_FONT= ("Verdana", 12)

########################################################################
""" Some global settings. They include namely settings from the """
""" config.ini file which is read in at the beginning """

CEC_on_script   = 0
CEC_off_script  = 0

""" Visual settings """
deltahours      = -2    # Value for Switzerland
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
            ffEmblem = tk.Label(self)
            ffEmblem["bg"]     = "black"
            ffEmblem["width"]  = screenWidth
            ffEmblem["height"] = screenHigh
            
            logo = Image.open(path)        

            # resize image to fit to the screen           
            if(screenHigh < screenWidth):   basewidth = screenWidth - 20
            else:                           basewidth = screenHigh - 20
                
            wpercent = (basewidth / float(logo.size[0]))
            hsize = int((float(logo.size[1]) * float(wpercent)))
            logo = logo.resize((basewidth, hsize), Image.ANTIALIAS)
            self.image = ImageTk.PhotoImage(logo)
                
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
        self.eventBgColor={}
        for x in ['red', 'blue', 'green', 'white']:
            path = os.path.join(wdr, 'pic', 'bg', ('%s.png') %(x)) 
            if os.path.isfile(path) == True:               
                logo = Image.open(path)
                logo = logo.resize((self.winfo_screenwidth(), 320), Image.ANTIALIAS)
                self.eventBgColor[x] = ImageTk.PhotoImage(logo) 
        
        # Create a canvas to hold the top event bar
        self.eventBar = tk.Canvas(self                            , 
                                  width=self.winfo_screenwidth()  , 
                                  height = 320                    , 
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
        self.route = tk.Label(self, relief='raised', bd=5)
        self.route.place(x=10, y=325, anchor='nw')
        
        """ Create a label for the right picture """
        self.detail = tk.Label(self, relief='raised', bd=5)
        self.detail.place(x=self.winfo_screenwidth()-10, y=325, anchor='ne')
              
        
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
        
        self.pb_hd = ttk.Progressbar(self                               , 
                                     style="red.Horizontal.TProgressbar", 
                                     orient='horizontal'                , 
                                     mode='determinate'                 , 
                                     length = self.winfo_screenwidth()  ,
                                     maximum = 100                      ,
                                     value   = 0                        )
        self.pb_hd.pack(expand=False, fill='both', side='bottom')
                
        
        self.bartime = 0
        self.showbar = 0
       
        self.poll()

    
    #----------------------------------------------------------------------     
    def setAddress(self                 , 
                   AlarmMsg     = 'None',
                   OverviewPic  = 0     ,
                   DetailPic    = 0     ,
                   category     = ""    ,
#                    sound        = 'None',
                   bartime      = 0     ,
                   showbar      = False):
        
        """ Set new message to the top red frame """ 
        # Set background of event bar depend of the category
        if category.lower() == 'fire':
            self.eventBar.itemconfig(self.eventBarImg, image=self.eventBgColor['red'])
        elif category.lower() == 'water':
            self.eventBar.itemconfig(self.eventBarImg, image=self.eventBgColor['blue'])
        elif category.lower() == 'neighborhood':
            self.eventBar.itemconfig(self.eventBarImg, image=self.eventBgColor['green'])
        else:
            self.eventBar.itemconfig(self.eventBarImg, image=self.eventBgColor['white'])
 
        self.eventBar.itemconfig(self.eventBarTxt, text="%s" %AlarmMsg)
        

        """ resize image to the given value """ 
        if showbar == False:        
            basewidth = self.winfo_screenheight() - 340
        else:
            basewidth = self.winfo_screenheight() - 445
        
        
        path = os.path.join(inifile_path, OverviewPic)   
        if os.path.isfile(path) == True:               
            logo = Image.open(path)
            wpercent = (basewidth / float(logo.size[0]))
            hsize = int((float(logo.size[1]) * float(wpercent)))
            logo = logo.resize((basewidth, hsize), Image.ANTIALIAS)
#            logo = logo.crop((0,0,600,600))
            self.routeImg = ImageTk.PhotoImage(logo)               
            self.route["image"] = self.routeImg

        
        path = os.path.join(inifile_path, DetailPic)
        if os.path.isfile(path) == True:               
            logo = Image.open(path)                
            wpercent = (basewidth / float(logo.size[0]))
            hsize = int((float(logo.size[1]) * float(wpercent)))
            logo = logo.resize((basewidth, hsize), Image.ANTIALIAS)
            self.detailImg = ImageTk.PhotoImage(logo)                
            self.detail["image"] = self.detailImg
        
        
            
        # The time has to be greater than 0 Seconds
        if bartime == 0:
            showbar = False
        
        if showbar == False:    
            self.pb_hd.pack_forget()
        else:
            self.pb_Time     = bartime*10
            self.pb_Act      = 0
            self.pb_Step     = 10.0 / bartime
            self.showbar     = showbar            
            self.pb_hd.config(value=0)
            self.pb_hd.pack(expand=False, fill='both', side='bottom')
            
    #----------------------------------------------------------------------
    def poll(self):
        if self.showbar == True:
            if self.pb_Act < self.pb_Time :
                self.pb_Act += 1
                self.pb_hd.step(self.pb_Step)
                
                if self.pb_Act < (self.pb_Time * 0.7):                
                    self.pb_hd.config(style="red.Horizontal.TProgressbar")
                else:    
                    if self.pb_Act < (self.pb_Time * 0.95):
                        self.pb_hd.config(style="orange.Horizontal.TProgressbar")
                    else:
                        self.pb_hd.config(style="green.Horizontal.TProgressbar")


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
        for x in range(1,7):
            self.truck[x] = tk.Label(self.truckcollection, background='gray')
            self.truck[x].pack(side='left', fill='both')
            self.trail[x] = tk.Label(self.truckcollection, background='gray')
            self.trail[x].pack(side='left')
            

    #----------------------------------------------------------------------   
    def setTruck(self,
                 truck,
                 trailer):
        
        self.truckImg = {}
        self.trailImg = {}
        baseheight    = 100               
 
        # generate the truck pictures concerning the ini-file
        for x in truck:
            path = os.path.join(wdr, 'pic', truck[x])
            if os.path.isfile(path) == True:               
                logo     = Image.open(path)
                hpercent = (baseheight/ float(logo.size[1]))
                wsize    = int((float(logo.size[0]) * float(hpercent)))
                logo     = logo.resize((wsize, baseheight), Image.ANTIALIAS)
                self.truckImg[x] = ImageTk.PhotoImage(logo) 
            else:
                self.truckImg[x] = "" 
        
        # generate the trailer pictures concerning the ini-file
        for x in trailer:
            path = os.path.join(wdr, 'pic', trailer[x])
            if os.path.isfile(path) == True:               
                logo = Image.open(path)
                hpercent = (baseheight/ float(logo.size[1]))
                wsize    = int((float(logo.size[0]) * float(hpercent)))
                logo     = logo.resize((wsize, baseheight), Image.ANTIALIAS)
                self.trailImg[x] = ImageTk.PhotoImage(logo)               
            else:
                self.trailImg[x] = ""    

        # copy the picutres into the particular labels
        for x in range(1,7):
            self.truck[x]["image"] = self.truckImg[x]
            self.trail[x]["image"] = self.trailImg[x]
            


########################################################################
class transformer:

    def __init__(self, world, viewport):
        """Constructor""" 
        self.world = world 
        self.viewport = viewport

    #----------------------------------------------------------------------
    def point(self, x, y):
        x_min, y_min, x_max, y_max = self.world
        X_min, Y_min, X_max, Y_max = self.viewport
        f_x = float(X_max-X_min) /float(x_max-x_min) 
        f_y = float(Y_max-Y_min) / float(y_max-y_min) 
        f = min(f_x,f_y)
        x_c = 0.5 * (x_min + x_max)
        y_c = 0.5 * (y_min + y_max)
        X_c = 0.5 * (X_min + X_max)
        Y_c = 0.5 * (Y_min + Y_max)
        c_1 = X_c - f * x_c
        c_2 = Y_c - f * y_c
        X = f * x + c_1
        Y = f * y + c_2
        return X , Y

    #----------------------------------------------------------------------
    def twopoints(self,x1,y1,x2,y2):
        return self.point(x1,y1),self.point(x2,y2)
    
    
########################################################################  
class ScreenClock(tk.Frame):
    
    def __init__(self, parent, controller):
        """Constructor"""     
        tk.Frame.__init__(self, parent)
        tk.Frame.config(self, bg='black')        
        
        self.world       = [-1,-1,1,1]
        self.bgcolor     = '#000000'
        self.circlecolor = 'red'#'#A0A0A0' #'#808080'
        self.timecolor   = '#ffffff'
        self.circlesize  = 0.09
        self._ALL        = 'all'
        self.pad         = 25
        self.delta       = timedelta(hours = deltahours)
        
        # Calculate high depend of the resolution
        if self.winfo_screenheight() > self.winfo_screenwidth():
            # Anzeige im Hochformat
            WIDTH = self.winfo_screenheight() / 2
            print("Hochforamt")
            
        else:
            # Anzeige im Querformat
            WIDTH = self.winfo_screenwidth() / 2
            print("Querformat")
            
        # Uhr soll Quadratisch sein
        HEIGHT = WIDTH        

         
        
        # create a lable for digital time. If wide-screen is available, 
        self.aspect_ratio = self.winfo_screenwidth() / self.winfo_screenheight()
        if self.aspect_ratio >= 1.5:
            # Wide-screen avialalbe
            fontsize = int( (self.winfo_screenheight() - HEIGHT) / 1.5 )
            self.timeLabel = tk.Label(self, font=("Arial", fontsize), bg='black', fg='white')
            self.dateLabel = tk.Label(self, font=("Arial", fontsize-40), bg='black', fg='white')
            
        else:
            # No wide-screen availalble
            fontsize = int( (self.winfo_screenheight() - HEIGHT) / 3 )
            self.timeLabel = tk.Label(self, font=("Arial", fontsize+20), bg='black', fg='white')
            self.dateLabel = tk.Label(self, font=("Arial", fontsize-20), bg='black', fg='white')
        
        # create a canvas for the clock 
        self.canvas = tk.Canvas(self, 
                                width               = WIDTH,
                                height              = HEIGHT,
                                background          = self.bgcolor,
                                highlightthickness  = 0)
        viewport = (self.pad,self.pad,WIDTH-self.pad,HEIGHT-self.pad)
        self.T = transformer(self.world,viewport)
        self.canvas.bind("<Configure>",self.configure())
        
        # show 
        self.canvas.pack(fill=tk.BOTH, expand=tk.NO)
        # if wide-screen available, but them beside, if not, stack
        if self.aspect_ratio >= 1.5:
            self.timeLabel.pack(fill=tk.BOTH, side='left')
            self.dateLabel.pack(fill=tk.BOTH, side='right')
        else:            
            self.dateLabel.pack(fill=tk.BOTH, side='bottom')
            self.timeLabel.pack(fill=tk.BOTH, side='bottom')
       
        self.poll()
 
    #----------------------------------------------------------------------
    def configure(self):
        self.redraw()
    
    #----------------------------------------------------------------------
    def redraw(self):
        sc = self.canvas
        sc.delete(self._ALL)
        width = sc.winfo_width()
        height =sc.winfo_height()
        sc.create_rectangle([[0,0],[width,height]], fill = self.bgcolor, tag = self._ALL)
        viewport = (self.pad,self.pad,width-self.pad,height-self.pad)
        self.T = transformer(self.world,viewport)
        self.paintgrafics()

    #----------------------------------------------------------------------
    def paintgrafics(self):
        start = -pi/2
        step = pi/6
        for i in range(12):
            angle =  start+i*step
            x, y = cos(angle),sin(angle)
            self.paintcircle(x,y)
        self.painthms()
        self.paintcircle(0,0)
    
    #----------------------------------------------------------------------
    def painthms(self):
        T = datetime.timetuple(datetime.utcnow()-self.delta)
        year,month,day,h,m,s,x,x,x = T  # @UnusedVariable
        
        if self.aspect_ratio >= 1.5: # If wide-screen available, show seconds too
            self.timeLabel["text"] = ('%02i:%02i:%02i'  %(h,m,s))
        else:
            self.timeLabel["text"] = ('%02i:%02i'       %(h,m))
        self.dateLabel["text"] = ('%02i.%02i.%04i'      %(day, month, year))

        angle = -pi/2 + (pi/6)*h + (pi/6)*(m/60.0)
        x, y = cos(angle)*.60,sin(angle)*.60   
        scl = self.canvas.create_line
        scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, width = 6)
        angle = -pi/2 + (pi/30)*m + (pi/30)*(s/60.0)
        x, y = cos(angle)*.80,sin(angle)*.80   
        scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, width = 3)
        angle = -pi/2 + (pi/30)*s
        x, y = cos(angle)*.95,sin(angle)*.95   
        scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, arrow = 'last')
           
    #----------------------------------------------------------------------
    def paintcircle(self,x,y):
        ss = self.circlesize / 2.0
        mybbox = [-ss+x,-ss+y,ss+x,ss+y]
        sco = self.canvas.create_oval
        sco(self.T.twopoints(*mybbox), fill = self.circlecolor, tag =self._ALL)
   
    #----------------------------------------------------------------------
    def poll(self):
        self.configure()
        self.after(200,self.poll)
        
         
########################################################################       
class MyHandler(FileSystemEventHandler):
    def __init__(self, controller):
        
        """Constructor"""
        self.controller = controller
        self.setAddress = self.controller.frames[ScreenObject].setAddress
        self.setTruck   = self.controller.frames[ScreenTruck].setTruck
        self.HDMIout    = SwitchTelevision()
        

        self.alarmSound   = sound.alarmSound( os.path.join(wdr, 'sound') )
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
            if self.lastModified >= int(time.time()): 
                return
             
            self.lastModified = int(time.time()) + 3

            # The parser-file has to be converted as UTF-8 file. Otherwise
            # special character like umlaut could not successfully read.
            try:
                parser = ConfigParser()
                with codecs.open(event.src_path, 'r', encoding='UTF-8-sig') as f:
                    parser.readfp(f)
            except:
                print("Failed to open ini-file \"%s\"" %event.src_path)
                print("--> Be sure file is encode as \"UTF-8 BOM\"")
                print("--------------------------------------------------\n\n")
                return
             
            try:    
                show = parser.get('General', 'show') 
            except: 
                print("Failed to read variable \"show\" in section [General]")
                return
                
            
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
                try:    AddMsg       = parser.get('ObjectInfo', 'entire_msg')
                except: AddMsg       = ""
                
                try:    OverviewPic  = parser.get('ObjectInfo', 'picture_overview')
                except: OverviewPic  = ""
                
                try:    DetailPic    = parser.get('ObjectInfo', 'pciture_detail')
                except: DetailPic    = ""
                
                try:    category     = parser.get('ObjectInfo', 'category')
                except: category     = ""
                
                try:    sound        = parser.get('ObjectInfo', 'sound')
                except: sound        = "None"
                
                try:    repeat       = parser.getint('ObjectInfo', 'repeat')
                except: repeat       = 1
                
                try:    showPB       = parser.getboolean('ObjectInfo', 'show_progress')
                except: showPB       = False
                
                try:    timePB       = parser.getint('ObjectInfo', 'progresstime')
                except: timePB       = 0
                
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
                    try:    truck[x] = parser.get('TruckInfo', s)
                    except: truck[x] = ""
                    s = (('truck_%01i_trailer') %(x))
                    try:    trail[x] = parser.get('TruckInfo', s)
                    except: trail[x] = ""
                    
                self.setTruck(truck = truck, trailer = trail)
                
                self.controller.show_frame(ScreenTruck)
                self.HDMIout.set_Visual('On')
                print("show truck")
                
            if show.lower() == 'quit':
                self.alarmSound.stop()
                self.HDMIout.set_Visual('On')
                print("Try to close programm")
                os._exit(0)
  

######################################################################## 
class SwitchTelevision:
    def __init__(self):
        self.__actGraficOutput      = 'On'
        self.__actTelevisionState   = 'Off'
        self.__pathToReactivateMonitor = os.path.join(wdr, HDMI_script)
        
        # if running on a linux system, disable power saving
        if os.name == 'posix':
            try:    subprocess.call(["xset", "s", "noblank"])
            except: pass
            try:    subprocess.call(["xset", "s", "noblank"])
            except: pass
            try:    subprocess.call(["xset", "-dpms"])
            except: pass
        else:
            pass
    
    #----------------------------------------------------------------------
    def get_Visual(self):
        """
        Return the status of the grafical output. If CEC is enabled, both
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
        Activate or deactivate the grafical output to force monitor to
        standby. If CEC is enabled, the television is triggered too,
        otherwise only the grafic output is driven.
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
                # Before disabling the grafic output, be sure there is a
                # shell-script for reactivation available
                if os.path.isfile(self.__pathToReactivateMonitor) == True:
                    try:    subprocess.call(["/opt/vc/bin/tvservice", "-o"])
                    except: pass
                    self.__actGraficOutput = newState
                else:
                    print("No file to reactivate grafical output")
                    
    #----------------------------------------------------------------------                
    def __switchTelevisionState(self, newState):
        print("Da kommt noch was")
            
                    
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
