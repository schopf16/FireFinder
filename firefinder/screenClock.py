#!/usr/bin/env python
# -*- coding: UTF-8-*-

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
from calendar import month

'''
A very simple  clock.

The program transforms worldcoordinates into screencoordinates 
and vice versa according to an algorithm found in: "Programming 
principles in computer graphics" by Leendert Ammeraal.

'''

import time
import tkinter as tk

from threading      import Thread
from datetime       import datetime
from math           import sin, cos, pi
from tkinter        import font as TkFont



########################################################################
class transformer:

    def __init__(self, world, viewport):
        """Constructor""" 
        self.world    = world 
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
        
        # store parent objects
        self.parent = parent
        self.controller = controller 
        
        # store size of the parent frame        
        self.controller.update()
        self.screenWidth = self.controller.winfo_width()
        self.screenHeight= self.controller.winfo_height()-200
        
        # Store which hands have to be shown
        self.showSecondHand = True
        self.showMinuteHand = True
        self.showHourHand   = True
        self.showAnalogTime = True
        self.showDigitalTime= True
        
                
        self.world       = [-1,-1,1,1]
        self.bgcolor     = '#000000'
        self.circlecolor = 'red'#'#A0A0A0' #'#808080'
        self.timecolor   = '#ffffff'
        self.circlesize  = 0.10
        self._ALL        = 'all'
        self.pad         = 25
        
        # Calculate ratio of the resolution
        self.aspectRatio = self.screenWidth / self.screenHeight
        
        # check if monitor has a portrait or landscape format
        if self.aspectRatio < 1:
            # portrait format
            HEIGHT = self.screenWidth          
        else:
            # landscape format
            HEIGHT = self.screenHeight
            
        
        self.secondHandThickness = HEIGHT / 216
        self.minuteHandThickness = HEIGHT / 90
        self.hourHandThickness   = HEIGHT / 50
        
      
#         # divide opposite leg (Gegenkathete) with adjacent side (Ankathete)
#         ratio = (HEIGHT/2) / (self.screenWidth/2)
#                 
#         # calculate the radian of the arc tangent
#         alpharad = atan(ratio)
#         
#         # get the hypotenuse of the smaller triangle outside of th clock circle
#         hypotenuse = hypot(HEIGHT/2, self.screenWidth/2) - (HEIGHT/2)
#         
#         # get the opposite side of the triangle
#         oppositeSide = sin(alpharad)*hypotenuse
#         
#         # calculate fontsize according the screen resolution and ratio
#         # 1.77 is the ratio for a 1920x1080 resolution
#         fontsize = int(oppositeSide/(2.8+(1.77-self.aspectRatio)))
#         
#         
#             
#         # if the ratio is greate than 1.5, place the time and date
#         # in a digital way too
#         if self.aspectRatio > 1.5:    
#             self.timeLabel.place(y=self.screenHeight, x=0,                anchor='sw')
#             self.dateLabel.place(y=self.screenHeight, x=self.screenWidth, anchor='se')
        
        # create viewport an pack canvas to screen
        viewport = (self.pad,self.pad,HEIGHT-self.pad,HEIGHT-self.pad)
        self.T = transformer(self.world,viewport)
#         self.canvas.bind("<Configure>",self.configure())
#         self.canvas.bind("<Configure>",self.redraw())
#         self.canvas.pack(fill=tk.BOTH, expand=tk.NO)
    
        self.createWidget(self.parent)
        
        # start poll the clock
        self.poll()
 
    #---------------------------------------------------------------------- 
    def createWidget(self, parent):   
        '''
        +---------analogClock---------+
        |                             |
        |                             |
        |                             |
        |                             |
        |                             |
        |                             |
        |                             |
        |                             |
        |                             |
        |                             |
        +-----------------------------+
        
        +--------digitalClock---------+
        |+-------------+-------------+|
        ||  timeLabel  |  dateLabel  ||
        |+-------------+-------------+|
        +-----------------------------+
        '''  
         
        tk.Frame.__init__(self,parent)
        tk.Frame.config(self, bg='black')
        
        ''' Create a object to hold the analog clock '''
        self.analogClock = tk.Canvas(self                                    , 
                                     width               = self.screenWidth  , 
                                     height              = self.screenHeight , 
                                     background          = self.bgcolor      ,
                                     highlightthickness  = 0                 )
        
        self.analogClock.pack(side='top', fill='both')
        
        ''' Create a object to hold the digital clock '''
        self.digitalClock = tk.Canvas(self                                    , 
                                      width               = self.screenWidth  , 
#                                       height              = self.screenHeight , 
                                      height              = 5,
                                      background          = self.bgcolor      ,
                                      highlightthickness  = 0                 )     
      
        font = TkFont.Font( family='Arial', size  =-70, weight='bold')
        self.timeLabel = tk.Label(self.digitalClock, bg='black', font=font, fg='white')
        self.emptLabel = tk.Label(self.digitalClock, bg='black', font=font, fg='white', text=' // ')
        self.dateLabel = tk.Label(self.digitalClock, bg='black', font=font, fg='white')
        self.timeLabel.pack(side='left', fill='both')
#        self.emptLabel.pack(side='left', fill='both')
        self.dateLabel.pack(side='right', fill='both')
        self.digitalClock.pack(side='top', fill='both')
        
        
#     #----------------------------------------------------------------------
#     def configure(self):
#         self.redraw()
    
    #----------------------------------------------------------------------
    def redraw(self):
        sc = self.analogClock
        sc.delete(self._ALL)
        width = self.screenWidth
        height= self.screenHeight
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
        actTime = datetime.timetuple(datetime.now())
        year,month,day,h,m,s,x,x,x = actTime  # @UnusedVariable
        
        self.timeLabel["text"] = ('%02i:%02i'       %(h,m))
        self.dateLabel["text"] = ('%02i.%02i.%04i'  %(day, month, year))

        scl = self.analogClock.create_line
        
        # Draw hour hand
        if self.showHourHand is True:
            angle = -pi/2 + (pi/6)*h + (pi/6)*(m/60.0)
            x, y = cos(angle)*.60,sin(angle)*.60         
            scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, width = self.hourHandThickness)
        
        # Draw minute hand
        if self.showMinuteHand is True:
            angle = -pi/2 + (pi/30)*m + (pi/30)*(s/60.0)
            x, y = cos(angle)*.80,sin(angle)*.80   
            scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, width = self.minuteHandThickness)
        
        # Draw seconds hand
        if self.showSecondHand is True:
            angle = -pi/2 + (pi/30)*s
            x, y = cos(angle)*.95,sin(angle)*.95     
            scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, arrow = 'last', width = self.secondHandThickness)
           
    #----------------------------------------------------------------------
    def paintcircle(self,x,y):
        ss = self.circlesize / 2.0
        mybbox = [-ss+x,-ss+y,ss+x,ss+y]
        sco = self.analogClock.create_oval
        sco(self.T.twopoints(*mybbox), fill = self.circlecolor, tag =self._ALL)
   
    #----------------------------------------------------------------------
    def poll(self):
        self.redraw()
        self.after(200,self.poll)  
    
    #----------------------------------------------------------------------    
    def setGeometry(self, value):
        self.screenWidth  = value[0]
        self.screenHeight = value[1]
        
        # Calculate ratio of the resolution
        self.aspectRatio = self.screenWidth / self.screenHeight
        if self.aspectRatio < 1:
            # portrait format
            HEIGHT = self.screenWidth          
        else:
            # landscape format
            HEIGHT = self.screenHeight
                    
        self.secondHandThickness = HEIGHT / 216
        self.minuteHandThickness = HEIGHT / 90
        self.hourHandThickness   = HEIGHT / 50
        
        self.analogClock.config(width=self.screenWidth, height=self.screenHeight)
        self.digitalClock.config(width=self.screenWidth, height=self.screenHeight)
#         self.redraw()
       
    #----------------------------------------------------------------------    
    def configure(self, **kw):
        
        if len(kw)==0: # return a dict of the current configuration
            cfg = {}
            cfg['showSecondHand']    = self.showSecondHand
            cfg['showMinuteHand']    = self.showMinuteHand
            cfg['showHourHand']      = self.showHourHand
            cfg['setGeometry']       = [self.screenWidth, self.screenHeight] 
            return cfg
    
        else: # do a configure
            for key,value in list(kw.items()):
                if key=='showSecondHand':
                    self.showSecondHand = value
                elif key=='showMinuteHand':
                    self.showMinuteHand = value
                elif key=='showHourHand':
                    self.showHourHand = value
                elif key=='setGeometry':
                    self.setGeometry(value)

            self.redraw()
            
    #----------------------------------------------------------------------
    def descentScreen(self):
        # nothing to do while hide
        pass
        
    #----------------------------------------------------------------------    
    def raiseScreen(self):
        # nothing to do while rise
        pass
        

########################################################################         
def testScreenClock():
    print("Start Test")
    time.sleep(1)
       
    screen.configure(showSecondHand = False)
    time.sleep(1)
    
    screen.configure(showMinuteHand = False)
    time.sleep(1)
    
    screen.configure(showHourHand = False)
    time.sleep(1)
    
    screen.configure(showSecondHand = True)
    time.sleep(1)
    
    screen.configure(showMinuteHand = True)
    time.sleep(1)
    
    screen.configure(showHourHand = True)
    time.sleep(1)
    
    screen.configure(setGeometry = [400, 200])
    time.sleep(1)
    
    screen.configure(setGeometry = [400, 400])
    time.sleep(1)
    
    screen.configure(setGeometry = [200, 200])
    time.sleep(1)
    
    screen.configure(setGeometry = [800, 800])
    time.sleep(1)
    
    screen.descentScreen()
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

    
    screen = ScreenClock(container, root)
    screen.grid(row=0, column=0, sticky="nsew")
    screen.tkraise()
    
    thread = Thread(target=testScreenClock, args=())
    thread.start()
    root.mainloop()        