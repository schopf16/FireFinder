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

from PIL        import ImageTk, Image
from tkinter    import font as TkFont

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
def getTextFontSize(self, maxHeight, maxWidth, bold=False, minHeight=1, text=''):
        i=maxHeight
        # get the max font size        
        for i in range(minHeight, maxHeight):
            if bold is False:
                font=TkFont.Font(family='Arial', size=-i)
            else:
                font=TkFont.Font(family='Arial', size=-i, weight='bold')
            lenght = font.measure(text)
            
            if (lenght >= maxWidth) or (font.metrics('linespace') >= maxHeight):
                break
          
        return -i 