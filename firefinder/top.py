#!/usr/bin/env python
# -*- coding: latin-1-*-

'''
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
'''

import os
import time
import tkinter as tk

from tkinter                  import font as TkFont
from datetime                 import datetime
from threading                import Thread
from firefinder.miscellaneous import createImage, getTextFontSize
from django.utils.termcolors import foreground

""" Path's """
ffLogo          = 'pic/Logo.png'        # Firefighter Logo


########################################################################    
class TopBar(tk.Frame):

    def __init__(self, parent, height):
         
        tk.Frame.__init__(self, parent)   

        self.parent = parent            # master of this widget
        
    
        # size dependend variables
        self.borderwidth = 0                        # the canvas borderwidth
        self.width = self.winfo_screenwidth()       # total width of widget
        self.height = height -(2*self.borderwidth)  # total height of widget
        
        # configs for the clock
        self.showTime      = True
        self.showSeconds   = True
        self.showDate      = True
        self.showWeekDay   = True
        self.WeekDayString = ['Montag'   , # Weekday 0
                             'Dienstag'  , # Weekday 1
                             'Mittwoch'  , # Weekday 2
                             'Donnerstag', # Weekday 3
                             'Freitag'   , # Weekday 4
                             'Samstag'   , # Weekday 5
                             'Sonntag'   ] # Weekday 6
        
        # configs for miscellaneous
        self.showLogo      = True       # True if Logo has to be display
        self.pathLogo      = None       # Path and filename with extending
        self.picLogo       = None       # Hold the picutre
        self.companyName   = ""         # Shows the company name on the rightside of the logo
#         self.font          = None
               
        # store label container
        self.canvas        = None           
        self.lblLogo       = None
        self.lblTime       = None  
        self.lblCompany    = None
        
        self.background    = 'black'
        self.foreground    = 'white'
        
        # store a object to cancel pending jobs
        self.__job = None
        
        self.createWidget()                 # create the widget
        self.paintLogo()
        self.painthms()

    #---------------------------------------------------------------------- 
    def createWidget(self):
        
        # If the images doesn't fit to the full width of the screen
        # add a dummy canvas to force filling the full width of the
        # screen. This is a ugly hack, change it as soon as you know
        # why the f*** this happen
        self.canvas = tk.Canvas(self                        ,
                                width=self.width            , 
                                height=self.height          ,
                                background=self.background  ,
                                borderwidth=self.borderwidth,
                                highlightthickness=0        )
        
        self.canvas.pack(side='left', fill='both', expand=True)
        
        # create a font depend from the height of the widget
        font = TkFont.Font( family='Arial', size=-self.height, weight='bold')
        
        # Create labels for logo and time
        self.lblLogo = tk.Label(   self.canvas               , 
                                   background=self.background)
        self.lblTime = tk.Label(   self.canvas                 , 
                                   background = self.background, 
                                   foreground = self.foreground,
                                   font       = font           )
        self.lblCompany = tk.Label(self.canvas                 ,
                                   background = self.background,
                                   foreground = self.foreground,
                                   font       = font           )
        

        # Pack label on canvas
        self.lblLogo.pack(side='left')
        self.lblCompany.pack(side='left')
        self.lblTime.pack(side='right')
           
        # store working directory
        try:    self.wdr = os.path.dirname( __file__ )
        except: self.wdr = os.getcwd()    
        
        # set path to Logo
        self.pathLogo = os.path.join(self.wdr, ffLogo)             

    
    #----------------------------------------------------------------------
    def paintLogo(self):
        
        if self.showLogo is True and self.pathLogo is not None:
            # check if path is ok
            if os.path.isfile(self.pathLogo) is True:
                self.picLogo = createImage(self, 
                                           path   = self.pathLogo, 
                                           height = self.height)
            else:
                print("%s is not a file" %self.pathLogo)
                self.picLogo = ''
                
            self.lblLogo["image"] = self.picLogo
        else:
            self.lblLogo["image"] = ""
            
        self.lblCompany["text"] = " " + self.companyName
        pass
    
    #----------------------------------------------------------------------
    def painthms(self):
        actTime = datetime.timetuple(datetime.now())
        year,month,day,h,m,s,wd,x,x = actTime  # @UnusedVariable
        
        # Create a string, depend on the user settings
        if self.showSeconds is True:
            timeString = ('%02i:%02i:%02i' %(h,m,s))
        else:
            timeString = ('%02i:%02i'       %(h,m))
            
        if self.showWeekDay is True:
            dateString = ('%s, %02i.%02i.%04i'  %(self.WeekDayString[wd], day, month, year))  
        else:
            dateString = ('%02i.%02i.%04i'  %(day, month, year))
            
        # Put the strings together to fit the needs of the configuration   
        self.timeAndDateString = ""
        if self.showTime is True and self.showDate is False:
            self.timeAndDateString = timeString
            
        if self.showTime is False and self.showDate is True:
            self.timeAndDateString = dateString
            
        if self.showTime is True and self.showDate is True:
            self.timeAndDateString = timeString + "  //  " + dateString
        
        self.lblTime["text"] = self.timeAndDateString + "  "

    #----------------------------------------------------------------------    
    def configure(self, **kw):
        
        changeTimeSettings = False
        changeLogoSettings = False
        
        if len(kw)==0: # return a dict of the current configuration
            cfg = {}
            cfg['showSecond']        = self.showSeconds
            cfg['showTime']          = self.showTime 
            cfg['showDate']          = self.showDate
            cfg['showWeekDay']       = self.showWeekDay
            cfg['setPathAndFile']    = self.pathLogo
            cfg['showLogo']          = self.showLogo
            cfg['companyName']       = self.companyName
            cfg['background']        = self.background
            cfg['foreground']        = self.foreground
            return cfg

        
        else: # do a configure
            for key,value in list(kw.items()):
                if key=='showSecond':
                    self.showSeconds = value
                    changeTimeSettings = True
                elif key=='showTime':
                    self.showTime = value
                    changeTimeSettings = True
                elif key=='showDate':
                    self.showDate = value
                    changeTimeSettings = True
                elif key=='showWeekDay':
                    self.showWeekDay = value                   
                    changeTimeSettings = True                    
                elif key=='background':
                    self.background = value
                    self.canvas["background"]     = value
                    self.lblTime["background"]    = value
                    self.lblLogo["background"]    = value
                    self.lblCompany["background"] = value
                    changeTimeSettings = True
                    changeLogoSettings = True
                elif key=='foreground':
                    self.foreground = value
                    self.lblTime["foreground"]    = value
                    self.lblLogo["foreground"]    = value
                    self.lblCompany["foreground"] = value
                    changeTimeSettings = True
                    changeLogoSettings = True
                elif key=='setPathAndFile':
                    self.pathLogo = value
                    changeLogoSettings = True
                elif key=='showLogo':
                    self.showLogo = value
                    changeLogoSettings = True
                elif key=='companyName':
                    self.companyName = value
                    changeLogoSettings = True

            if changeTimeSettings is True:
                self.painthms()
                
            if changeLogoSettings is True:
                self.paintLogo() 
            
                    
    #----------------------------------------------------------------------
    def poll(self):
        self.painthms()
        self.__job = self.after(200,self.poll)
                      
    #----------------------------------------------------------------------  
    def __del__(self):
        for widget in self.winfo_children():
            widget.destroy()
            
    #----------------------------------------------------------------------
    def descentScreen(self):
        if self.__job is not None:
            self.after_cancel(self.__job)
            self.__job = None
        pass
        
    #----------------------------------------------------------------------    
    def raiseScreen(self):
        if self.__job is None:
            self.__job = self.after_idle(self.poll)
        pass



########################################################################         
def testScreenTop():
    print("Start Test")
    bar.raiseScreen()
    time.sleep(1)
    
    bar.configure(companyName = "Feuerwehr Ittigen")
    time.sleep(1)
    
    bar.configure(showLogo = False)
    time.sleep(1)
    
    bar.configure(showTime = False)
    time.sleep(1)
    
    bar.configure(showDate = False)
    time.sleep(1)
    
    bar.configure(showLogo = True)
    time.sleep(1)
    
    bar.configure(companyName = "")
    time.sleep(1)
    
    bar.configure(foreground = 'blue')
    time.sleep(1)
    
    bar.configure(showDate = True)
    time.sleep(1)
    
    bar.configure(companyName = "Feuerwehr Ittigen")
    time.sleep(1)
    
    bar.configure(showWeekDay = False)
    time.sleep(1)
    
    bar.configure(background = 'green')
    time.sleep(1)
    
    bar.configure(showTime = True)
    time.sleep(1)
    
    bar.configure(background = 'grey')
    time.sleep(1)
    
    bar.configure(foreground = 'red')
    time.sleep(1)
    
    bar.configure(showWeekDay = True)
    time.sleep(3)

    bar.descentScreen()
    time.sleep(1)
    
    bar.__del__()
    
    print("Test ende")
           
######################################################################## 
if __name__ == '__main__':
    
    #wbar = 1920
    wbar = 1800
    hbar = 40
    
    root = tk.Tk() 
    root.geometry("%dx%d+0+0" % (wbar+10, hbar+10))
    
    bar = TopBar(root, height=hbar) 
    bar.pack(fill='both')

    
  
    thread = Thread(target=testScreenTop, args=())
    thread.start()

    root.mainloop() 


