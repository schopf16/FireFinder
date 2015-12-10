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


from tkinter                  import font as TkFont
from threading                import Thread
from firefinder.miscellaneous import createImage, getTextFontSize


class ProgressBar(tk.Frame):

    def __init__(self, parent, width, height, pixelPerSlice=1):
         
        tk.Frame.__init__(self, parent)

        if pixelPerSlice <= 0:
            pixelPerSlice = 1
            
        self.parent = parent            # master of this widget
        
              
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
                                            
        self.progressActiv = False
                                            
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
        
        self.createWidget()                 # create the widget

    #---------------------------------------------------------------------- 
    def createWidget(self):
        
        self.canvas = tk.Canvas(self,
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
            fontSize = getTextFontSize(self                         , 
                                       text      = self.text        , 
                                       maxHeight = self.height      , 
                                       maxWidth  = self.width*0.98  )
            
            font = TkFont.Font(family='Arial', size = fontSize )
        
        self.textLabel = self.canvas.create_text(
                            int(self.width/2)                       , 
                            int((self.height/2)+self.borderwidth)   ,
                            text   = self.text                      ,
                            fill   = self.txtColor                  , 
                            font   = font                           ,
                            justify = 'center'                      )
        
        # pack the canvas into the frame
        self.canvas.pack()
                    
    #---------------------------------------------------------------------- 
    def updateGrafic(self):
        self.canvas.coords(self.progressBar ,
                           self.borderwidth , 
                           self.borderwidth , 
                           self.increment   , 
                           self.height      )


    #---------------------------------------------------------------------- 
    def setText(self, text=''):
        if text == '':
            self.canvas.itemconfig(self.textLabel, text='')
        else:
            fontSize = getTextFontSize(self                         , 
                                       text      = text             , 
                                       maxHeight = self.height      , 
                                       maxWidth  = self.width*0.98  )
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
        self.stop()
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

        if self.progressActiv is False:
            self.progressActiv = True
            self.after_idle(self.autoRunProgressBar)
        
    #---------------------------------------------------------------------- 
    def stop(self):
        self.progressActiv = False
              
    #----------------------------------------------------------------------
#     def autoRunProgressBar(self, arg1, stop_event):
    def autoRunProgressBar(self):
        
        # check if progressbar has to be terminated
        if self.progressActiv is not True:
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
        
        # check if the correct text scheme is chosen
        for i in range(len(self.textScheme)):
            if progress >= self.textScheme[i][0]:
                textIndex = i 
        if self.text != self.textScheme[textIndex][1]:
            self.setText(self.textScheme[textIndex][1])
             
        # Update progress bar
        if self.increment < self.width:
            self.increment += self.pixelPerSlice
            self.updateGrafic()
            self.after(self.msPerSlice, self.autoRunProgressBar)
        else:
            self.increment = self.width
            self.updateGrafic()
            self.progressActiv = False
            return        
   
    #----------------------------------------------------------------------  
    def __del__(self):
        for widget in self.winfo_children():
            widget.destroy()


########################################################################    
class ResponseOrder(tk.Frame):

    def __init__(self, parent, width, height):
         
        tk.Frame.__init__(self, parent)   

        self.parent = parent            # master of this widget
        
    
        # size dependend variables
        self.borderwidth = 2                        # the canvas borderwidth
        self.width = width   -(2*self.borderwidth)  # total width of widget
        self.height = height -(2*self.borderwidth)  # total height of widget
        
        # grafical dependend variables
        self.frame         = None           # the frame holding canvas & label
        self.frameVisual   = None
        self.canvas        = None           # the canvas holding the progress bar
        
        self.background    = 'gray'
        
        self.createWidget()                 # create the widget

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
               
        # Create a set of 12 labels to hold the truck and trailer-images
        self.equipment    = {}
        self.equipmentImg = {} 
        for x in range(1,10):
            self.equipment[x] = tk.Label(self.canvas, background=self.background)
            self.equipment[x].pack(side='left', fill='both')   
            
        # store working directory
        try:    self.wdr = os.path.dirname( __file__ )
        except: self.wdr = os.getcwd()    
        

    #----------------------------------------------------------------------   
    def setEquipment(self, equipment):              
        # generate the truck pictures concerning inputs
        for x in equipment:
            if equipment[x] is not '':
                path = os.path.join(self.wdr, 'pic', equipment[x])
                self.equipmentImg[x] = createImage(self.master, path, height=self.height)
                self.equipment[x]["image"] = self.equipmentImg[x]
    
    #----------------------------------------------------------------------  
    def __del__(self):
        for widget in self.winfo_children():
            widget.destroy()



########################################################################         
def testScreenFooter():
    print("Start Test")
    time.sleep(1)
    
    bar.start(timeInSeconds=30, startValue=0)
    time.sleep(1)
    
    # create a tulpe and clear it
    equipment = {}
    for x in range(1,12):
        equipment[x] = ''
    
    # add 5 car to footer   
    equipment[1] = 'Fz_5.png'
    equipment[2] = 'Fz_6.png'
    equipment[3] = 'Fz_7.png'
    equipment[4] = 'Fz_1.png'
    equipment[5] = 'Fz_4.png'
    print("Add cars")
    truck.setEquipment(equipment = equipment)
    time.sleep(1)
    
    # clear even car slots
    equipment[1] = ''
    equipment[2] = 'Fz_6.png'
    equipment[3] = ''
    equipment[4] = 'Fz_1.png'
    equipment[5] = ''
    print("Clear even car slots")
    truck.setEquipment(equipment = equipment)
    time.sleep(1)
    
    bar.stop()
    time.sleep(2)
    
    bar.start(timeInSeconds=15, startValue=0)
    time.sleep(1)
    
    print("Test ende")
           
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
    
    bar = ProgressBar(root, width=wbar, height=hbar, pixelPerSlice=1) 
    bar.pack(fill='both')

        
    truck = ResponseOrder(root, width=wres, height=100)
    truck.pack(fill='both')
    
  
    thread = Thread(target=testScreenFooter, args=())
    thread.start()

    root.mainloop() 


