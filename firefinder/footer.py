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
import tkinter as tk


from tkinter                  import font as TkFont
from threading                import Thread
from firefinder.miscellaneous import createImage


class ProgressBar:

    def __init__(self, width, height, master=None, pixelPerSlice=1):

        if pixelPerSlice <= 0:
            pixelPerSlice = 1
            
        if master is None:
            master = tk.Toplevel()
            master.protocol('WM_DELETE_WINDOW', self.hide )
        self.master = master            # master of this widget
        
        
        
        # size dependend variables
        self.borderwidth = 2                        # the canvas borderwidth
        self.width = width   -(2*self.borderwidth)  # total width of widget
        self.height = height -(2*self.borderwidth)  # total height of widget
        
        # grafical dependend variables
        self.frame         = None           # the frame holding canvas & label
        self.canvas        = None           # the canvas holding the progress bar
        self.progressBar   = None           # the progress bar geometry
        self.backgroundBar = None           # the background bar geometry
        self.textLabel     = None           # the Text shown in the progress bar
        self.text          = ''             # the text string of the label
        self.increment     = 0              # stores the width of the progress in pixel
        self.pixelPerSlice = pixelPerSlice  # Amount of pixel per slice
                                            # less pixel seems more fluence, but needs
                                            # more processor time
                                            
        self.msPerSlice    = 0
        self.bgColor       = 'grey'
        self.fgColor       = 'red'
        self.txtColor      = 'white' 
        self.colorScheme   = [[  0,'red'   ],
                              [ 90,'orange'],
                              [100,'green' ]]
        
        self.textScheme    = [[  0,'Warte auf Atemschutz-Geräteträger'                  ],
                              [ 90,'Bereitmachen zum Ausrücken'                         ],
                              [100,'Losfahren, auch bei zuwenig Atemschutz-Geräteträger']]
        
        self.ONOFF = 'off'
        self.createWidget()                 # create the widget

    #---------------------------------------------------------------------- 
    def createWidget(self):
        self.frame = tk.Frame(  self.master                 ,
                                borderwidth=self.borderwidth,
                                relief='sunken'             )
        
        self.canvas = tk.Canvas(self.frame,
                                width=self.width, 
                                height=self.height)
        
        # create the background bar geometry
        self.backgroundBar = self.canvas.create_rectangle( 
                self.borderwidth    , 
                self.borderwidth    , 
                self.width          , 
                self.height         , 
                fill=self.bgColor   )
        
        # create the progress bar geometry
        self.progressBar = self.canvas.create_rectangle(
                self.borderwidth    , 
                self.borderwidth    , 
                0                   , # Start without any progress bar
                self.height         , 
                fill=self.fgColor   )
        
        # create a text lable in the middle of the progess bar
        if self.text == '':
            font = TkFont.Font(family='Arial', size=10 )
        else:
            font = TkFont.Font(family='Arial'                       , 
                               size=self.getTextFontSize(self.text) )
        
        self.textLabel = self.canvas.create_text(
                            int(self.width/2)                       , 
                            int((self.height/2)+3+self.borderwidth) ,
                            text   = self.text                      ,
                            fill   = self.txtColor                  , 
                            font   = font                           ,
                            width  = self.width                     ,
                            justify = 'center'                      )
        
        # pack the canvas into the frame
        self.canvas.pack()
        
        # create a thread to handle the progressBar
        self.thread = Thread(target=self.autoRunProgressBar, args=())
                    
    #---------------------------------------------------------------------- 
    def updateGrafic(self):
        self.canvas.coords(self.progressBar ,
                           self.borderwidth , 
                           self.borderwidth , 
                           self.increment   , 
                           self.height      )

    #---------------------------------------------------------------------- 
    def getTextFontSize(self, text=''):
        if text == '':
            self.canvas.itemconfig(self.textLabel, text='')
        else:
            # get the max font size           
            for i in range(1, self.height):
                font=TkFont.Font(family='Arial', size=i)
                lenght = font.measure(text)
                if lenght >= self.width:
                    return i-2          
            return i    
 
    #---------------------------------------------------------------------- 
    def setText(self, text=''):
        if text == '':
            self.canvas.itemconfig(self.textLabel, text='')
        else:
            fontSize = self.getTextFontSize(text)
            font = TkFont.Font(family='Arial', size=fontSize )           
            self.canvas.itemconfig(self.textLabel, text=text, font=font)
        
        self.text = text
            
    #---------------------------------------------------------------------- 
    def setColor(self, color=''):
        if color == '':
            color = 'blue'
        self.fgColor = color        
        self.canvas.itemconfig(self.progressBar,fill=color)
     
    #---------------------------------------------------------------------- 
    def get(self):
        return (self.increment/self.width)*100.0
    
    #---------------------------------------------------------------------- 
    def reset(self):
        self.thread.stop()
        self.increment = 0
        
    #---------------------------------------------------------------------- 
    def start(self, timeInSeconds, startValue=None):
        self.msPerSlice = int(  (timeInSeconds*1000           )  / 
                                (self.width/self.pixelPerSlice)  )
        
        if startValue is not None:
            if startValue > self.width:
                self.increment = self.width
            else:
                self.increment = startValue
        self.ONOFF = 'on'
        self.thread.start()
        
    #---------------------------------------------------------------------- 
    def stop(self):
        self.ONOFF = 'off'
        self.thread.stop()
    
    #---------------------------------------------------------------------- 
    def show(self, x=None, y=None, anchor=None):
        self.frame.place(x=x, y=y, anchor=anchor)
    
    #---------------------------------------------------------------------- 
    def hide(self):
        if isinstance(self.master, tk.Toplevel):
            self.master.withdraw()
        else:
            self.frame.forget()
        self.ONOFF = 'off'
              
    #----------------------------------------------------------------------
    def autoRunProgressBar(self):
        
        if self.ONOFF == 'off':
            return
        
        progress = (self.increment / self.width) * 100
        colorIndex = 0
        textIndex  = 0
        
        # check if the correct color scheme is chosen
        for i in range(len(self.colorScheme)):
            if progress >= self.colorScheme[i][0]:
                colorIndex = i
        if self.fgColor != self.colorScheme[colorIndex][1]:
            self.setColor(self.colorScheme[colorIndex][1])    
        
        # check if the correct test scheme is chosen
        for i in range(len(self.textScheme)):
            if progress >= self.textScheme[i][0]:
                textIndex = i 
        if self.text != self.textScheme[textIndex][1]:
            self.setText(self.textScheme[textIndex][1])
             
        # Update progress bar
        if self.increment < self.width:
            self.increment += self.pixelPerSlice
            self.updateGrafic()
            self.frame.after(self.msPerSlice, self.autoRunProgressBar)
        else:
            self.increment = self.width
            self.updateGrafic()
        
        return
    
class ResponseOrder:

    def __init__(self, width, height, master=None):
            
        if master is None:
            master = tk.Toplevel()
            master.protocol('WM_DELETE_WINDOW', self.hide )
        self.master = master            # master of this widget
        
    
        # size dependend variables
        self.borderwidth = 2                        # the canvas borderwidth
        self.width = width   -(2*self.borderwidth)  # total width of widget
        self.height = height -(2*self.borderwidth)  # total height of widget
        
        # grafical dependend variables
        self.frame         = None           # the frame holding canvas & label
        self.canvas        = None           # the canvas holding the progress bar
        
        self.background    = 'gray'
        
        self.createWidget()                 # create the widget

    #---------------------------------------------------------------------- 
    def createWidget(self):
        self.frame = tk.Frame(  self.master                 ,
                                borderwidth=self.borderwidth,
                                background=self.background  ,
                                relief='sunken'             )
        
        # If the images doesn't fit to the full width of the screen
        # add a dummy canvas to force filling the full width of the
        # screen. This is a ugly hack, change it as soon as you know
        # why the f*** this happen
        self.canvas = tk.Canvas(self.frame                  ,
                                width=self.width            , 
                                height=0                    ,
                                background=self.background  ,
                                highlightthickness=0        )
               
        # Create a set of 12 labels to hold the truck and trailer-images
        self.equipment    = {}
        self.equipmentImg = {} 
        for x in range(1,12):
            self.equipment[x] = tk.Label(self.frame, background='gray')
            self.equipment[x].pack(side='left', fill='both')   
            
        # store working directory
        try:    self.wdr = os.path.dirname( __file__ )
        except: self.wdr = os.getcwd()    
    
        # pack the canvas into the frame
        self.canvas.pack(side='left', fill='both', expand=True)

    #----------------------------------------------------------------------   
    def setTruck(self, equipment):
        
        spaceUsed = 0
        
        # generate the truck pictures concerning inputs
        for x in equipment:
            path = os.path.join(self.wdr, 'pic', equipment[x])
            self.equipmentImg[x] = createImage(self.master, path, height=self.height)
            self.equipment[x]["image"] = self.equipmentImg[x]
            spaceUsed += self.equipment[x]["width"]
            
        # resize the ugly hack
#        self.canvas.config(width = self.width - 2*self.borderwidth - spaceUsed)
        
    #---------------------------------------------------------------------- 
    def show(self, x=None, y=None, anchor=None):
        self.frame.place(x=x, y=y, anchor=anchor)               
    
    #---------------------------------------------------------------------- 
    def hide(self):
        if isinstance(self.master, tk.Toplevel):
            self.master.withdraw()
        else:
            self.frame.forget()
            
                
######################################################################## 
if __name__ == '__main__':
    
    wbar = 1920
    hbar = 200
    wres = 1920
    hres = 100
    
    root = tk.Tk() 
    if wbar > wres:
        root.geometry("%dx%d+0+0" % (wbar+10, hres+hbar+10))
    else:
        root.geometry("%dx%d+0+0" % (wres+10, hres+hbar+10))
    
    bar = ProgressBar(master=root, width=wbar, height=hbar, pixelPerSlice=1) 
    bar.show(x=0, y=0, anchor='nw')
    bar.start(timeInSeconds=100, startValue=0)
    
    equipment = {}
    for x in range(1,12):
        equipment[x] = 'Fz_5.png'
    for x in range(6,12):
        equipment[x] =""
        
    truck = ResponseOrder(master=root, width=wres, height=100)
    truck.setTruck(equipment = equipment)
    truck.show(x=0, y=hbar+5, anchor='nw')
  
    root.mainloop() 


