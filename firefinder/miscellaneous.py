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

import os
import math

from PIL        import ImageTk, Image
from tkinter    import font as TkFont
from threading  import Timer

def createImage(self, path, width=0, height=0, crop=False, keepRatio=True):
    """
    The function creates a ImageTk.PhotoImage from a given picture with
    path. If width and height of the picture is known, the picture can be
    crop. The function will automatically crop the image around the middle
    to fit onto the given width and height.
    If one side of the picture is unknown, the function will fit the image
    to the given side while the other side will grove or reduce to fit to
    the resolution of the picture.
    
    crop        If set to True, the function will resize the image to fit
                as god as possible to the given width and height. If the 
                image is on one side bigger than expected, the side will be
                croped on both sides.
                
    keepRatio   If set to True, the function will resize the image while
                keeping the same resolution. If set to False, the fuction
                will resize the image to the given width and height even if
                the ratio is not the same.

                
    """
    
    # check if a file is found at given path    
    if os.path.isfile(path) is False:
        print(("ERROR:  Failed to open picture at path \'%s\'") %(path))
        return ""
        
    with Image.open(path) as image:     
          
        # force dimension to integer
        width  = int( width  )
        height = int( height )
        
        # if one axes is equal, set this to maximum
        if width  == 0: width = self.winfo_screenwidth()
        if height == 0: height = self.winfo_screenheight()
    
        # define which axes is the base
        if ((width / image.size[0]) * image.size[1]) > height: 
            base = 'height'
        else:
            base = 'width'
        
        # If the picture can crop afterwards, switch the base
        if crop == True:
            if base == 'height':    base = 'width'
            else:                   base = 'height'
        
        # Calculate the new dimenson according the given values
        if keepRatio == True:     
            if base == 'width':        
                wpercent = (width / float(image.size[0]))
                hsize    = int( (float(image.size[1]) * float(wpercent)) )
                wsize    = int( width )
            else:          
                hpercent = (height / float(image.size[1]))
                wsize = int( (float(image.size[0]) * float(hpercent)) )
                hsize = int( height )
        else:
            wsize = int( width )
            hsize = int( height )
                                           
        # Resize the image
        image = image.resize((wsize, hsize), Image.ANTIALIAS)        
                
        if crop == True:
            # Crop image if its bigger than expected
            wOffset = int( (image.size[0] - width ) / 2 )
            hOffset = int( (image.size[1] - height) / 2 )  
            image = image.crop((wOffset, hOffset, wOffset + width, hOffset + height)) 
                   
        return ImageTk.PhotoImage(image)

'''
    Get font height in pixel
'''    
def getTextFontSize(self, maxHeight, maxWidth, text='', bold=False, minHeight=1, lineBreak=False):
    """
    The function calculates the possible maximal font height. The family is
    fixed to Arial.
    
    maxHeight   Give the maximal available heigth space in pixel
    
    maxWidth    Give the maximal available width space in pixel
    
    text        String to which the maximum size is to be calculated
    
    bold        If set to True, the function calculates the font with
                setting bold
                
    minHeight   If set, the function will not return font height smaller than
                the given value. If not set, the minHeight is set to 1
                
    lineBreak   If set to True, the function will keep a possible line break
                in mind and calculate the font with the possibility of a line
                break.               
    """
    # get the max font size        
    for i in range(minHeight, maxHeight):
        if bold is False:
            font=TkFont.Font(family='Arial', size=-i)
        else:
            font=TkFont.Font(family='Arial', size=-i, weight='bold')
        
        # get width and height of the string
        w, h = (font.measure(text), font.metrics("linespace"))

        # depend of available line break, decide to quit loop
        if lineBreak is True:
            # calculate the expected lines depend on the width of the
            # screen. Round up to reach the save side
            expectLines   = math.ceil(float(w) / float(maxWidth))
            
            # calculate the over all height by considering the amount of lines
            heightOverAll = h * expectLines
            if heightOverAll >= maxHeight:
                break
        else:
            if (w >= maxWidth) or (h >= maxHeight):
                break
      
    return -i 

########################################################################         
class RepeatingTimer(object):
    
    def __init__(self, interval, f, *args, **kwargs):
        self.interval = interval
        self.f = f
        self.args = args
        self.kwargs = kwargs

        self.timer = None

    #---------------------------------------------------------------------- 
    def callback(self):        
        self.f(*self.args, **self.kwargs)
        self.start()

    #---------------------------------------------------------------------- 
    def cancel(self):
        # increase robustness
        if self.is_alive():
            self.timer.cancel()
    
    #----------------------------------------------------------------------    
    def start(self):
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()
     
    #----------------------------------------------------------------------    
    def is_alive(self):
        if self.timer is None:
            return False
        else:
            return self.timer.is_alive()
    
    #---------------------------------------------------------------------- 
    def join(self, timeout):
        if self.timer is None:
            return
        else:
            return self.timer.join(timeout)
        