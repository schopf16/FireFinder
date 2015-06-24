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
    def __init__(self, master=None, wsize=0, hsize=0, bg='', fg='', value= 50, maximum=100.0, wdr=''):
        self.master    = master
        self.wsize     = wsize
        self.hsize     = hsize
        self.bg        = bg
        self.fg        = fg
        self.maximum   = maximum
        self.value     = value
        self.wdr       = wdr
        self.textFrame = ''
                       
        self.pbContainer = tk.Canvas(self.master            , 
                                     width      = wsize     , 
                                     height     = hsize     ,
                                     background = bg        , 
                                     highlightthickness = 0 ) 
        
        self.pbImage = self.pbContainer.create_image(0, 0, anchor = 'nw')
        self.pbText  = self.pbContainer.create_text(int(wsize/2), int(hsize/2), anchor='center' )
        self.pbContainer.itemconfig(self.pbText     , 
                                 fill = "white"     ,  
                                 font=('Arial', 60) )
      
    #----------------------------------------------------------------------  
    def step(self, step, fg):
        
        self.value += step
        
        path = os.path.join(self.wdr, 'pic', 'bg', ('%s_pb.png') %(fg) ) 
        if os.path.isfile(path) == True:               
            colorBar = Image.open(path) 
            barwidth = int( self.wsize *( self.value / self.maximum) )
            colorBar = colorBar.resize((barwidth, self.hsize), Image.ANTIALIAS)
            self.eventBgColor = ImageTk.PhotoImage(colorBar) 
        self.pbContainer.itemconfig(self.pbImage, image=self.eventBgColor)
    
    #----------------------------------------------------------------------
    def setValue(self, value, maximum):
        self.value   = value
        self.maximum = maximum
          
    #----------------------------------------------------------------------    
    def text(self, text):        
        if self.textFrame != text:
            self.textFrame = text
            self.pbContainer.itemconfig(self.pbText, text="%s" %text)
     
    #----------------------------------------------------------------------   
    def place(self, x=0, y=0):
        self.pbContainer.place(x=x, y=y)
        
    def forget(self):
        self.pbContainer.place_forget()
        