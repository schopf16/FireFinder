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
import random
import tkinter as tk


from threading      import Thread
from itertools      import cycle

# my very own classes
from firefinder.miscellaneous import createImage
        
class ScreenSlideshow(tk.Frame):

    def __init__(self, parent, controller):

        # store parent objects
        self.parent = parent
        self.controller = controller 
        
        # store working directory
        try:    self.wdr = os.path.dirname( __file__ )
        except: self.wdr = os.getcwd() 
        
        # store size of the parent frame        
        self.controller.update()
        self.screenWidth = self.controller.winfo_width()
        self.screenHeight= self.controller.winfo_height()
             
        # set time between slides in seconds
        self.delay = 12
        
        # store path where the pictures for the slideshow are stored
        self.pathToIniFile = ''
        self.pathToImages = ''
        
        # rebuild list of pictures
        self.pictures     = 0
        self.file_names   = []
        self.fileInFolder = 0
        
        # default sort by alphabetical
        self.sortAlphabetically = True
        
        # store a object to cancel pending jobs
        self.__job = None
        
        self.createWidget(self.parent)
        
    #---------------------------------------------------------------------- 
    def createWidget(self, parent):      
        tk.Frame.__init__(self,parent)
        
        # create a lable to show the image
        self.picture_display = tk.Label(self)
        self.picture_display["bg"]     = "black"
        self.picture_display["fg"]     = "white"
        self.picture_display["width"]  = self.screenWidth
        self.picture_display["height"] = self.screenHeight
        self.picture_display["font"]   = ("Arial", 60) 
        self.picture_display.pack()
            
    #----------------------------------------------------------------------        
    def show_slides(self):
        print("picture")
        # Check if path already set
        if self.pathToImages is '':
            print("ERROR: Path to slideshow folder not set yet")
            return
        
        # check if slideshow directory exists and create it if necessary 
        if not os.path.exists(self.pathToImages):
            os.makedirs(self.pathToImages)

        # check if there are new images or some are deleted
        countFile = len([name for name in os.listdir(self.pathToImages) if os.path.isfile(os.path.join(self.pathToImages, name))])
        if countFile != self.fileInFolder:
            
            # delete the list
            self.file_names = []
            
            # load all images which could be shown
            included_extenstions = ['.jpg','.jpeg','.bmp','.png','.gif','.eps','.tif','.tiff'] ;
            for file in os.listdir(self.pathToImages):

                # get extension
                ext = os.path.splitext(file)[1]
                
                # check if extension is available
                if ext.lower() in included_extenstions:
                    self.file_names.append(os.path.join(self.pathToImages, file))

            # only proceed if there are any pictures found
            if self.file_names:
                if self.sortAlphabetically is True:
                    # put the list in alphabetical order
                    self.file_names = sorted( self.file_names )
                else:
                    # shuffle the list randomly
                    random.shuffle( self.file_names )
                # put list in a cycle
                self.cycledList = cycle(self.file_names)
            
            # store the amount of files
            self.fileInFolder = countFile
         
        # check if there is at least an image available
        if len(self.file_names):     
            path = next(self.cycledList) # get next picture from cycle
            self.pictures = createImage(self, path=path)         
            self.picture_display.config(image=self.pictures)
            self.picture_display.config(text = "")
        else:            
            self.picture_display.config(image= "")
            self.picture_display.config(text = "Keine Bilder zum Anzeigen :-(")      
        
        # wait to show the next picture
        self.__job = self.after(int(self.delay*1000), self.show_slides)
        
    #----------------------------------------------------------------------    
    def configure(self, **kw):
        
        if len(kw)==0: # return a dict of the current configuration
            cfg = {}
            cfg['pathToIniFile']        = self.pathToIniFile
            cfg['secondsBetweenImages'] = self.delay
            cfg['sortAlphabetically']   = self.sortAlphabetically
            return cfg
    
        else: # do a configure
            for key,value in list(kw.items()):
                if key=='pathToIniFile':
                    self.pathToIniFile = value
                    self.pathToImages  = os.path.join(self.pathToIniFile, 'Slideshow') 
                elif key=='secondsBetweenImages':
                    if value is not self.delay:
                        self.setDelay(value)                   
                elif key=='sortAlphabetically':
                    self.sortAlphabetically = value
                    self.fileInFolder = 0 # clear to force refresh folder

    #----------------------------------------------------------------------
    def setDelay(self, value):
        self.delay = value
        # force restart slideshow
        self.after_cancel(self.__job)
        self.__job = self.after_idle(self.show_slides)
        pass
            
    #----------------------------------------------------------------------
    def descentScreen(self):
        if self.__job is not None:
            self.after_cancel(self.__job)
            self.__job = None
        pass
        
    #----------------------------------------------------------------------    
    def raiseScreen(self):
        if self.__job is None:
            self.__job = self.after_idle(self.show_slides)
        pass
    
    
########################################################################         
def testScreenClock():
    print("Start Test")
    time.sleep(1)
       
    screen.raiseScreen()
    time.sleep(1)
    
    screen.configure(pathToIniFile = 'D:\Firefinder')
    time.sleep(1)
    
    screen.raiseScreen()
    time.sleep(10)
    
    print("change display time to 3 seconds")
    screen.configure(secondsBetweenImages = 3)
    time.sleep(15)
    
    print("change display time to 6 seconds")
    screen.configure(secondsBetweenImages = 6)
    time.sleep(15)
    
    print('descent')
    screen.descentScreen()
    time.sleep(15)
    
    print('raise')
    screen.raiseScreen()
    time.sleep(15)
    
    print("Test ende")
    
######################################################################## 
if __name__ == '__main__':
    
    
    root = tk.Tk() 
    root.geometry("%dx%d+0+0" % (root.winfo_screenwidth(), root.winfo_screenheight()-200))
    
    container = tk.Frame(root)        
    container.pack(side="top", fill="both", expand = True)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    
    screen = ScreenSlideshow(container, root)
    screen.grid(row=0, column=0, sticky="nsew")
    screen.tkraise()
    
    thread = Thread(target=testScreenClock, args=())
    thread.start()
    root.mainloop()  