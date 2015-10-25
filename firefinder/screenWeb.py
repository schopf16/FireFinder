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
import subprocess
import tkinter as tk

from threading import Thread


class ScreenWeb(tk.Frame):
    def __init__(self, parent, controller):
        
        # store parent objects
        self.parent = parent
        self.controller = controller 
        
        # store size of the parent frame        
        self.controller.update()
        self.screenWidth = self.controller.winfo_width()
        self.screenHeight= self.controller.winfo_height()
        
        # store working directory
        try:    self.wdr = os.path.dirname( __file__ )
        except: self.wdr = os.getcwd()
        
        self.url = ''
        self.local = ''
        self.pathToIniFile = ''
        
        self.createWidget(self.parent)
        pass
    
    #---------------------------------------------------------------------- 
    def createWidget(self, parent):
        
        tk.Frame.__init__(self, parent) 
                                          
        # Create a canvas to hold the top event bar
        self.blankBackground = tk.Canvas(   self                           , 
                                            width      = self.screenWidth  , 
                                            height     = self.screenHeight ,
                                            background = 'black'           , 
                                            highlightthickness = 0         )
        self.blankBackground.pack()
        
    #----------------------------------------------------------------------    
    def show(self, page):
        if page is 'url':
            homepage = self.url
        else:
            homepage = os.path.join(self.pathToIniFile, self.local)
            homepage = ("file:%s"%homepage)
        print(homepage)    
        if os.name == 'posix':
            print("Zeige Hoempage")
            try: subprocess.Popen(["epiphany-browser", homepage])
            except: print("Failed to open epiphany-browser")
        elif os.name == 'nt':
            pass

            
    #----------------------------------------------------------------------
    def configure(self, **kw):
        
        if len(kw)==0: # return a dict of the current configuration
            cfg = {}
            cfg['url']           = self.url
            cfg['local']         = self.local
            cfg['pathToIniFile'] = self.pathToIniFile
            return cfg
    
        else: # do a configure
            for key,value in list(kw.items()):
                if key=='url':
                    self.url = value
                    self.show('url')
                elif key=='local':
                    self.local = value
                    self.show('local')
                elif key=='pathToIniFile':
                    self.pathToIniFile = value
                    
            if self.pathToIniFile is '':
                print("WARNING: Path to ini-file yet not set")
                
    #----------------------------------------------------------------------
    def descentScreen(self):
        if os.name == 'posix':
            print("kill the browser")
            try: subprocess.Popen(["killall", "epiphany-browser"])
            except: print("failed to kill epiphany-browser")
        elif os.name == 'nt':
            pass
        
    #----------------------------------------------------------------------    
    def raiseScreen(self):
        # nothing to do while rise
        pass
    
    #----------------------------------------------------------------------  
    def __del__(self):
        self.descentScreen()
        for widget in self.winfo_children():
            widget.destroy()
    
########################################################################         
def testScreenAlarm():
    print("Start Test")
    time.sleep(1)
    
    screen.configure(pathToIniFile = '/home/pi/FireFinder')
    
#    screen.configure(url = 'https://www.google.ch')
#    time.sleep(10)

    screen.configure(local = 'Bahnhofsuhr/index.html')
    time.sleep(10)
    
#    screen.descentScreen()
    time.sleep(2)

#    screen.__del__()
    time.sleep(1)
    
    print("Test ende")
    
######################################################################## 
if __name__ == '__main__':
    
    
    root = tk.Tk() 
    root.geometry("%dx%d+0+0" % (root.winfo_screenwidth(), root.winfo_screenheight()-200))
    
    container = tk.Frame(root)        
    container.pack(side="top", fill="both", expand = False)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)
    
    screen = ScreenWeb(container, root)
    screen.grid(row=0, column=0, sticky="nsew")
    screen.tkraise()
    
    thread = Thread(target=testScreenAlarm, args=())
    thread.start()
    root.mainloop() 
