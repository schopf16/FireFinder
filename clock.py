'''
Created on 20.06.2015

@author: Michael
'''

from datetime           import timedelta,datetime
from math               import sin, cos, pi
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
        self.circlesize  = 0.09
        self._ALL        = 'all'
        self.pad         = 25
        
        # Calculate high depend of the resolution
        if self.winfo_screenheight() > self.winfo_screenwidth():
            # Anzeige im Hochformat
            WIDTH = self.winfo_screenheight() / 2
            
        else:
            # Anzeige im Querformat
            WIDTH = self.winfo_screenwidth() / 2
            
        # Uhr soll Quadratisch sein
        HEIGHT = WIDTH        

         
        
        # create a lable for digital time. If wide-screen is available, 
        self.aspect_ratio = self.winfo_screenwidth() / self.winfo_screenheight()
        if self.aspect_ratio >= 1.5:
            # Wide-screen avialalbe
            fontsize = int( (self.winfo_screenheight() - HEIGHT) / 1.5 )
            self.timeLabel = tk.Label(self, font=("Arial", fontsize), bg='black', fg='white')
            self.dateLabel = tk.Label(self, font=("Arial", fontsize-40), bg='black', fg='white')
            
        else:
            # No wide-screen availalble
            fontsize = int( (self.winfo_screenheight() - HEIGHT) / 3 )
            self.timeLabel = tk.Label(self, font=("Arial", fontsize+20), bg='black', fg='white')
            self.dateLabel = tk.Label(self, font=("Arial", fontsize-20), bg='black', fg='white')
        
        # create a canvas for the clock 
        self.canvas = tk.Canvas(self, 
                                width               = WIDTH,
                                height              = HEIGHT,
                                background          = self.bgcolor,
                                highlightthickness  = 0)
        viewport = (self.pad,self.pad,WIDTH-self.pad,HEIGHT-self.pad)
        self.T = transformer(self.world,viewport)
        self.canvas.bind("<Configure>",self.configure())
        
        # show 
        self.canvas.pack(fill=tk.BOTH, expand=tk.NO)
        # if wide-screen available, but them beside, if not, stack
        if self.aspect_ratio >= 1.5:
            self.timeLabel.pack(fill=tk.BOTH, side='left')
            self.dateLabel.pack(fill=tk.BOTH, side='right')
        else:            
            self.dateLabel.pack(fill=tk.BOTH, side='bottom')
            self.timeLabel.pack(fill=tk.BOTH, side='bottom')
       
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
        
        if self.aspect_ratio >= 1.5: # If wide-screen available, show seconds too
            self.timeLabel["text"] = ('%02i:%02i:%02i'  %(h,m,s))
        else:
            self.timeLabel["text"] = ('%02i:%02i'       %(h,m))
        self.dateLabel["text"] = ('%02i.%02i.%04i'      %(day, month, year))

        angle = -pi/2 + (pi/6)*h + (pi/6)*(m/60.0)
        x, y = cos(angle)*.60,sin(angle)*.60   
        scl = self.canvas.create_line
        scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, width = 6)
        angle = -pi/2 + (pi/30)*m + (pi/30)*(s/60.0)
        x, y = cos(angle)*.80,sin(angle)*.80   
        scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, width = 3)
        angle = -pi/2 + (pi/30)*s
        x, y = cos(angle)*.95,sin(angle)*.95   
        scl(self.T.twopoints(*[0,0,x,y]), fill = self.timecolor, tag =self._ALL, arrow = 'last')
           
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
        
        