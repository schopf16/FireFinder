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

import os
import time
import tkinter as tk

from threading import Thread
from tkinter   import font as TkFont
from PIL       import ImageTk, Image

# my very own classes
from firefinder.miscellaneous import createImage, getTextFontSize
from firefinder.footer        import ProgressBar, ResponseOrder

""" Path's """
backgroundImage = 'pic/bg'              # Path to background Image for alarm message
noImage         = 'pic/bg/no_image.png' # Image, of desired image is not found



"""
callable object to call the screen object configure method.
Used to overwrite methods of class instances
"""
class ScreenObjectConf:
        
    def __init__(self, screen):
        self.screen = screen

    def __call__(self, **kw):
        self.screen.configure(*(), **kw)
 
        
class ScreenObject(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        # store parent objects
        self.parent = parent
        self.controller = controller 
        
        # store size of the parent frame        
        self.controller.update()
        self.screenWidth = self.controller.winfo_width()
        self.screenHeight= self.controller.winfo_height()
        if (self.screenWidth < 640) or (self.screenHeight < 480):
            print("WARNING: Low screen resolution %d x %d!!" %(self.screenWidth, self.screenHeight))
        
        # Store the height of the several places
        self.alarmMessageBarHeight = 220 # Pixel
        self.progressBarHeight     = 100 # Pixel
        self.responseOrderHeight   = 150 # Pixel

        # store working directory
        try:    self.wdr = os.path.dirname( __file__ )
        except: self.wdr = os.getcwd() 
        self.pathToIniFile = ''
        
        
        self.alarmMessageUseTicker  = False
        self.alarmMessage           = ''
        self.category               = ''
        self.categoryImage          = ''
        self.nameOfPicture_1        = ''    
        self.nameOfPicture_2        = ''
        self.cropPicture            = False
        
        
        self.showProgressBar   = False
        self.progressBarTime   = 0
        
        # Response order bar
        self.responseOrderBar  = None
        self.showResponseOrder = False
        self.responseOrder     = ''
        self.borderwidthROB    = 2 
        self.backgroundROB     = 'gray'
        self.equipment         = {}
        self.equipmentImg      = {}

        
        self.createWidget(parent)
        
    #---------------------------------------------------------------------- 
    def createWidget(self, parent):
        
        tk.Frame.__init__(self, parent)
        
        """
        
        +-------alarmMessageBar-------+
        |                             |
        |                             |
        +-----------------------------+
        
        +----------pictureBar---------+
        |+-------------+-------------+|
        ||             |             ||
        ||  Left       | Right       ||
        ||  Picture    | Picture     ||
        ||  (pic_1)    | (pic_2)     ||
        |+-------------+-------------+|
        +-----------------------------+
        
        +---------progressBar---------+
        |XXXXXXXX                     |        
        +-----------------------------+
        
        +------responseOrderBar-------+
        |                             |
        +-----------------------------+

        This function creates 4 frames. Each can shown or 
        hide independently.

        """
      

        heightPictureBar = self.screenHeight - self.alarmMessageBarHeight      
                                          
        # Create a canvas to hold the top event bar
        self.alarmMessageBar = tk.Canvas(   self                                , 
                                            width  = self.screenWidth           , 
                                            height = self.alarmMessageBarHeight , 
                                            highlightthickness = 0              )
         
        self.alarmMessageBarImage = self.alarmMessageBar.create_image(
                                            0                                   , 
                                            0                                   , 
                                            anchor = 'nw'                       ) 
        self.alarmMessageBarText  = self.alarmMessageBar.create_text(
                                            self.screenWidth/2                  , 
                                            self.alarmMessageBarHeight/2        ,                                 
                                            fill   = "black"                    ,
                                            justify = 'center'                  ) 
        
        # Create a canvas to hold the map
        self.pictureBar= tk.Canvas( self, 
                                    width               = self.screenWidth  , #WIDTH,
                                    height              = heightPictureBar  , #HEIGHT,
                                    background          = 'black'           ,
                                    highlightthickness  = 0                 )
        
        # Place both Canvas
        self.alarmMessageBar.pack(side='top')
        self.pictureBar.pack(side='top', fill='both')
        
        """ Create a label for the left picture """
        self.pic_1 = tk.Label(self.pictureBar, bd=0, background='black', foreground='black')
        
        """ Create a label for the right picture """
        self.pic_2 = tk.Label(self.pictureBar, bd=0, background='black', foreground='black')
        
        """ Create a progressBar object """
        self.progressBar = ProgressBar( self                                    , 
                                        width         = self.screenWidth        , 
                                        height        = self.progressBarHeight  , 
                                        pixelPerSlice = 1                       )
         
        """ Create a responseOrder object """
        self.responseOrderBar = ResponseOrder(self                              , 
                                              width=self.screenWidth            , 
                                              height=self.responseOrderHeight   )
        
        
    #----------------------------------------------------------------------
    def configure(self, **kw):
        
        changePicture = False
        
        if len(kw)==0: # return a dict of the current configuration
            cfg = {}
            cfg['alarmMessage']      = self.alarmMessage
            cfg['picture_1']         = self.nameOfPicture_1
            cfg['picture_2']         = self.nameOfPicture_2
            cfg['cropPicture']       = self.cropPicture
            cfg['category']          = self.category
            cfg['showProgressBar']   = self.showProgressBar
            cfg['progressBarTime']   = self.progressBarTime
            cfg['showResponseOrder'] = self.showResponseOrder
            cfg['responseOrder']     = self.responseOrder
            cfg['pathToIniFile']     = self.pathToIniFile
            return cfg
    
        else: # do a configure
            for key,value in list(kw.items()):
                if key=='pathToIniFile':
                    self.pathToIniFile = value
                if key=='category':
                    if value.lower() is not self.category:
                        self.setCategory(value)
                elif key=='cropPicture':
                    if value is not self.cropPicture:
                        self.setCropPicture(value)
                elif key=='alarmMessage':
                    if value is not self.alarmMessage:
                        self.setAlarmMessage(value)
                elif key=='picture_1':
                    changePicture = True
                    self.nameOfPicture_1 = value
                elif key=='picture_2':
                    changePicture = True
                    self.nameOfPicture_2 = value
                elif key=='showResponseOrder':
                    if value is not self.showResponseOrder:
                        self.setShowResponseOrder(value)
                elif key=='responseOrder':
                    if value is not self.responseOrder:
                        self.setResponseOrder(value)
                elif key=='showProgressBar':
                    if value is not self.showProgressBar:
                        self.setShowProgressBar(value)
                elif key=='progressBarTime':
                    if value is not self.progressBarTime:
                        self.setProgressBarTime(value)
            
            if self.pathToIniFile is '':
                print("WARNING: Path to ini-file yet not set")
                        
            if changePicture is True:
                self.setPicture()

    #----------------------------------------------------------------------
    def setCategory(self, value):
        self.category = value.lower()
        path = os.path.join(self.wdr, backgroundImage, ('%s.png') %(self.category))
        if os.path.isfile(path) == True: 
            with Image.open(path) as logo:
                logo = logo.resize((self.screenWidth    , 
                                    self.alarmMessageBarHeight) , 
                                    Image.ANTIALIAS             )
                self.categoryImage = ImageTk.PhotoImage(logo)
                self.alarmMessageBar.itemconfig(self.alarmMessageBarImage, 
                                                image=self.categoryImage)
        else:
            print(("ERROR:  Path \'%s\' does not lead to a background color") %(path))
    
    #----------------------------------------------------------------------   
    def setCropPicture(self, value):
        self.cropPicture = value
        self.setPicture()
        
    #----------------------------------------------------------------------
    def setAlarmMessage(self, value):
        self.alarmMessage = value
        fontSize= getTextFontSize(self,
                                  maxHeight= int(self.alarmMessageBarHeight),
                                  minHeight= 70, 
                                  maxWidth = int(self.screenWidth*1.8), 
                                  text     = self.alarmMessage,
                                  bold     = True)
        
        font = TkFont.Font( family='Arial', size  =fontSize, weight='bold')
              
        self.alarmMessageBar.itemconfig(self.alarmMessageBarText    , 
                                        text="%s" %self.alarmMessage,
                                        font= font                  ,
                                        width=self.screenWidth)
    
    #----------------------------------------------------------------------
    def setPicture(self):
          
        # Calculate size of Images
        progressHeight = int(self.showProgressBar)  * self.progressBarHeight
        responseHeight = int(self.showResponseOrder)* self.responseOrderHeight
        alarmHeight    = int(self.alarmMessageBarHeight)
        
        picHeight = int(self.screenHeight - alarmHeight - progressHeight - responseHeight)
        picWidth  = int(self.screenWidth)
        
        # if picture 2 is empty, show picture 1 as fullscreen and clear picture 2
        if self.nameOfPicture_2 is not '':
            picWidth = int(picWidth / 2) 
        else:  
            self.pic_2.pack_forget()
                  
        # Change and resize picture 1   
        path = os.path.join(self.pathToIniFile, self.nameOfPicture_1)
        if os.path.isfile(path) == True:   
            self.pic1Img = createImage(self, 
                                       path   = path, 
                                       width  = picWidth, 
                                       height = picHeight, 
                                       crop   = self.cropPicture)
        else:     
            self.pic1Img = createImage(self, 
                                       path      = noImage, 
                                       width     = picWidth, 
                                       height    = picHeight, 
                                       keepRatio = False)             
        
        # recalculate left padding depend of the second picture        
        if self.nameOfPicture_2 is not '':
            leftPadding = int( (self.screenWidth/4) - (self.pic1Img.width()/2) )
        else:
            leftPadding = int( (self.screenWidth/2) - (self.pic1Img.width()/2) )
        
        # Put picture on the screen    
        self.pic_1["image"] = self.pic1Img
        self.pic_1.pack(side='left', ipadx=leftPadding )
        
           
        # Change and resize picture 2
        if self.nameOfPicture_2 is not '':
            path = os.path.join(self.pathToIniFile, self.nameOfPicture_2)
            if os.path.isfile(path) == True:   
                self.pic2Img = createImage(self, 
                                           path   = path, 
                                           width  = picWidth, 
                                           height = picHeight, 
                                           crop   = self.cropPicture)
            else:    
                self.pic2Img = createImage(self, 
                                           path      = noImage, 
                                           width     = picWidth, 
                                           height    = picHeight, 
                                           keepRatio = False) 
            
            # reposition picture and put it on the screen
            self.pic_2['image'] = self.pic2Img
            self.pic_2.pack(side='left', ipadx=leftPadding)
        
    #----------------------------------------------------------------------
    def setShowResponseOrder(self, value):
        self.showResponseOrder = value       
        if self.showResponseOrder is True: 
            self.responseOrderBar.pack(side='top', fill='both')
        else:
            self.responseOrderBar.pack_forget()
        
        # redraw picture
        self.setPicture()
            
    #----------------------------------------------------------------------
    def setResponseOrder(self, value):
        self.responseOrder = value
        self.responseOrderBar.setEquipment(self.responseOrder)
        
    #----------------------------------------------------------------------
    def setShowProgressBar(self, value):
        self.showProgressBar = value    
        if self.showProgressBar is True:
            self.progressBar.pack(side='top', fill='both', after=self.pictureBar)
            self.progressBar.start(timeInSeconds=self.progressBarTime, startValue=0)
        else:
            self.progressBar.pack_forget()
        
        # redraw picture
        self.setPicture()
    
    #----------------------------------------------------------------------
    def setProgressBarTime(self, value):
        self.progressBarTime = value
        
    #----------------------------------------------------------------------
    def hide(self):
        self.progressBar.stop()
        
    #----------------------------------------------------------------------    
    def rise(self):
        # nothing to do while rise
        pass
    
    #----------------------------------------------------------------------  
    def __del__(self):
        print (self.id, 'died')
        for widget in self.winfo_children():
            widget.destroy()

########################################################################         
def testScreenAlarm():
    print("Start Test")
    time.sleep(1)
    
    screen.configure(category = 'green')
    time.sleep(1)
    
    screen.configure(pathToIniFile = 'D:\Firefinder')
    time.sleep(1)

    screen.configure(picture_1='detail.jpg', picture_2='direction_1.jpg')
    time.sleep(1)
    
    screen.configure(alarmMessage = 'test message')    
    time.sleep(1)
    
    screen.configure(category = 'blue')
    time.sleep(1)
    
    screen.configure(picture_1='detail.jpg', picture_2='')
    time.sleep(1)
    
    screen.configure(picture_1='detail.jpg', picture_2='1.jpg')
    time.sleep(1)
    
    screen.configure(cropPicture = True)
    time.sleep(1)
    
    screen.configure(alarmMessage = 'Kp. 25, AA Sprinkler, Ittigen, Mühlestrasse 2, Verwaltungszentrum UVEK Ittigen')    
    time.sleep(1)
    
    screen.configure(category = 'red')
    time.sleep(1)
    
    screen.configure(picture_1='detail.jpg', picture_2='detail.jpg')
    time.sleep(1)
    
    screen.configure(cropPicture = False)
    time.sleep(1)
    
    screen.configure(alarmMessage = 'Und nun folgt zum Testen eine wirklich lange Testnachricht. Damit soll ' 
                                    'geprüft werden, ob auch bei sehr langen Texten diese Schriftgrösse nie'
                                    'kleiner als 70 Pixel sein wird...')    
    time.sleep(1)
    
    screen.configure(showResponseOrder = True)
    time.sleep(1)
    
    equipment = {}
    for x in range(1,12):
        equipment[x] = 'Fz_5.png'
    for x in range(6,12):
        equipment[x] =""
    screen.configure(responseOrder = equipment)
    time.sleep(1)
    
    screen.configure(showResponseOrder = False)
    time.sleep(1)
    
    screen.configure(showResponseOrder = True)
    time.sleep(1)
    
    screen.configure(progressBarTime = 30)
    time.sleep(1)
    
    screen.configure(showProgressBar = True)
    time.sleep(1)
    
    screen.configure(showResponseOrder = False)
    time.sleep(1)
    
    screen.configure(showResponseOrder = True)
    time.sleep(1)
    
    screen.configure(progressBarTime = 20)
    time.sleep(1)
    
    screen.configure(showProgressBar = False)
    time.sleep(1)
    
    screen.configure(showProgressBar = True)
    time.sleep(1)
    
    screen.hide()
    time.sleep(1)
    
    print("Test ende")
    
######################################################################## 
if __name__ == '__main__':
    
    
    root = tk.Tk() 
    root.geometry("%dx%d+0+0" % (root.winfo_screenwidth(), root.winfo_screenheight()-200))
    
    container = tk.Frame(root)        
    container.pack(side="top", fill="both", expand = True)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)
#     container.update()
    
    screen = ScreenObject(container, root)
    screen.grid(row=0, column=0, sticky="nsew")
    screen.tkraise()
    
    thread = Thread(target=testScreenAlarm, args=())
    thread.start()
    root.mainloop() 

