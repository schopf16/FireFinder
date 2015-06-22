'''
Created on 22.06.2015

@author: andmi
'''

import tkinter as tk
import os

from PIL                import ImageTk, Image

class progressBar:
    """
    ProgressBar
    This class creates a canvas which is used as progressBar.
    
    """
    #----------------------------------------------------------------------
    def __init__(self, wsize, hsize, bg, fg, value= 50, maximum=100.0, wdr):
        self.wsize     = wsize
        self.hsize     = hsize
        self.bg        = bg
        self.fg        = fg
        self.maximum   = maximum
        self.value     = value
        self.wdr       = wdr
        self.colorLoad = ''
        
        path = os.path.join(self.wdr, 'pic', 'bg', 'red_pb.png' ) 
        if os.path.isfile(path) == True:               
            self.colorBar = Image.open(path)
            barwidth = int( (self.wsize / self.maximum) * self.value )
            self.colorBar = self.colorBar.resize((barwidth, self.hsize), Image.ANTIALIAS)
            self.eventBgColor = ImageTk.PhotoImage(self.colorBar) 
            self.colorLoad = 'red'
                
        self.pbContainer = tk.Canvas(self                  , 
                                     width  = wsize        , 
                                     height = hsize        , 
                                     highlightthickness = 0) 
        
        self.pbImage = self.pbContainer.create_image(0, 0, anchor = 'nw')
        self.pbText  = self.pbContainer.create_text(15, 30 )
        self.pbContainer.itemconfig(self.pbImage, image=self.eventBgColor)
        
        print("Init progressBar")
      
    #----------------------------------------------------------------------  
    def step(self, value, bg):
        
        self.value = value
        
        # Do I have to change the color?
        if bg != self.colorLoad:
            path = os.path.join(self.wdr, 'pic', 'bg', ('%s_pb.png') %(bg) ) 
            if os.path.isfile(path) == True:               
                self.colorBar = Image.open(path)
                self.colorLoad = 'bg'
            
        barwidth = int( (self.wsize / self.maximum) * self.value )
        self.colorBar = self.colorBar.resize((barwidth, self.hsize), Image.ANTIALIAS)
        self.eventBgColor = ImageTk.PhotoImage(self.colorBar) 
        self.pbContainer.itemconfig(self.pbImage, image=self.eventBgColor)
      
    #----------------------------------------------------------------------    
    def text(self, text):
        print("Text")
     
    #----------------------------------------------------------------------   
    def place(self, x=0, y=0):
        self.pbContainer.place(x=x, y=y)
        