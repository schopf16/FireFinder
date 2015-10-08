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

'''
A very simple  clock.

The program transforms worldcoordinates into screencoordinates 
and vice versa according to an algorithm found in: "Programming 
principles in computer graphics" by Leendert Ammeraal.

'''

from datetime           import datetime
from math               import sin, cos, pi, atan, hypot
import tkinter as tk


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
        self.circlesize  = 0.10
        self._ALL        = 'all'
        self.pad         = 25
        
        # Calculate high depend of the resolution
        self.aspect_ratio = self.winfo_screenwidth() / self.winfo_screenheight()
        
        # check if monitor has a portrait or landscape format
        if self.aspect_ratio < 1:
            # portrait format
            HEIGHT = self.self.winfo_screenwidth()
            
        else:
            # landscape format
            HEIGHT = self.winfo_screenheight()
            
        
        # Create a canvas to put clock in it
        self.canvas = tk.Canvas(self, 
                                width               = self.winfo_screenwidth(), #WIDTH,
                                height              = self.winfo_screenheight(), #HEIGHT,
                                background          = self.bgcolor,
                                highlightthickness  = 0)
      
        # divide opposite leg (Gegenkathete) with adjacent side (Ankathete)
        ratio = (HEIGHT/2) / (self.winfo_screenwidth()/2)
                
        # calculate the radian of the arc tangent
        alpharad = atan(ratio)
        
        # get the hypotenuse of the smaller triangle outside of th clock circle
        hypotenuse = hypot(HEIGHT/2, self.winfo_screenwidth()/2) - (HEIGHT/2)
        
        # get the opposite side of the triangle
        oppositeSide = sin(alpharad)*hypotenuse
        
        # calculate fontsize according the screen resolution and ratio
        # 1.77 is the ratio for a 1920x1080 resolution
        fontsize = int(oppositeSide/(2.8+(1.77-self.aspect_ratio)))
        
        # Create a lable for time and date inside canvas and place
        # the lable on the bottom left and right side        
        self.timeLabel = tk.Label(self.canvas, font=("Arial", fontsize), bg='black', fg='white')
        self.dateLabel = tk.Label(self.canvas, font=("Arial", fontsize), bg='black', fg='white')
            
        # if the ratio is greate than 1.5, place the time and date
        # in a digital way too
        if self.aspect_ratio > 1.5:    
            self.timeLabel.place(y=self.winfo_screenheight(), x=0,                        anchor='sw')
            self.dateLabel.place(y=self.winfo_screenheight(), x=self.winfo_screenwidth(), anchor='se')
        
        # create viewport an pack canvas to screen
        viewport = (self.pad,self.pad,HEIGHT-self.pad,HEIGHT-self.pad)
        self.T = transformer(self.world,viewport)
        self.canvas.bind("<Configure>",self.configure())
        self.canvas.pack(fill=tk.BOTH, expand=tk.NO)
    
        # start poll the clock
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
        T = datetime.timetuple(datetime.now())
        year,month,day,h,m,s,x,x,x = T  # @UnusedVariable
        
#         if self.aspect_ratio >= 1.5: # If wide-screen available, show seconds too
#             self.timeLabel["text"] = ('%02i:%02i:%02i'  %(h,m,s))
#         else:
#             self.timeLabel["text"] = ('%02i:%02i'       %(h,m))
        self.timeLabel["text"] = ('%02i:%02i'       %(h,m))
        self.dateLabel["text"] = ('%02i.%02i.%04i'  %(day, month, year))

        # Draw hour hand
        angle = -pi/2 + (pi/6)*h + (pi/6)*(m/60.0)
        x, y = cos(angle)*.60,sin(angle)*.60   
        scl = self.canvas.create_line
        scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, width = 20)
        
        # Draw minute hand
        angle = -pi/2 + (pi/30)*m + (pi/30)*(s/60.0)
        x, y = cos(angle)*.80,sin(angle)*.80   
        scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, width = 12)
        
        # Draw seconds hand
#         angle = -pi/2 + (pi/30)*s
#         x, y = cos(angle)*.95,sin(angle)*.95   
#         scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, arrow = 'last', width = 5)
           
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
        
        