#!/usr/bin/env python
# -*- coding: UTF-8-*-

"""
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
"""

import os
import math

from PIL import Image, ImageTk
from tkinter import font as tkfont
from threading import Timer


def create_image(self, path, width=0, height=0, crop=False, keep_ratio=True):
    """
    The function creates a ImageTk.PhotoImage from a given picture with
    path. If width and height of the picture is known, the picture can be
    crop. The function will automatically crop the image around the middle
    to fit onto the given width and height.
    If one side of the picture is unknown, the function will fit the image
    to the given side while the other side will grove or reduce to fit to
    the resolution of the picture.

    :param keep_ratio:  If set to True, the function will resize the image
                        while keeping the same resolution. If set to False,
                        the fuction will resize the image to the given
                        width and height even if the ratio is not the same.
    :param crop:        If set to True, the function will resize the image
                        to fit as god as possible to the given width and
                        height. If the image is on one side bigger than
                        expected, the side will be croped on both sides.
    :param height:      height of the picture. If unused the height will be
                        calculated automatically
    :param width:       width of the picture. If unused the width will be
                        calculated automatically
    :param path:        path and file
    :param self:        Instance of the actual widget

                
    """

    # check if a file is found at given path    
    if os.path.isfile(path) is False:
        print("ERROR:  Failed to open picture at path \'%s\'" % path)
        return ""

    with Image.open(path) as image:

        # force dimension to integer
        width = int(width)
        height = int(height)

        # if one axes is equal, set this to maximum
        if width == 0:
            width = self.winfo_screenwidth()
        if height == 0:
            height = self.winfo_screenheight()

        # define which axes is the base
        if ((width / image.size[0]) * image.size[1]) > height:
            base = 'height'
        else:
            base = 'width'

        # If the picture can crop afterwards, switch the base
        if crop:
            if base == 'height':
                base = 'width'
            else:
                base = 'height'

        # Calculate the new dimenson according the given values
        if keep_ratio:
            if base == 'width':
                wpercent = (width / float(image.size[0]))
                hsize = int((float(image.size[1]) * float(wpercent)))
                wsize = int(width)
            else:
                hpercent = (height / float(image.size[1]))
                wsize = int((float(image.size[0]) * float(hpercent)))
                hsize = int(height)
        else:
            wsize = int(width)
            hsize = int(height)

        # Resize the image
        image = image.resize((wsize, hsize), Image.ANTIALIAS)

        if crop:
            # Crop image if its bigger than expected
            woffset = int((image.size[0] - width) / 2)
            hoffset = int((image.size[1] - height) / 2)
            image = image.crop((woffset, hoffset, woffset + width, hoffset + height))

        return ImageTk.PhotoImage(image)


'''
    Get font height in pixel
'''


def get_text_font_size(max_height, max_width, text='', bold=False, min_height=1, line_break=False):
    """
    The function calculates the possible maximal font height. The family is
    fixed to Arial.

    :param line_break:  If set to True, the function will keep a possible line break
                        in mind and calculate the font with the possibility of a line
                        break.
    :param min_height:  If set, the function will not return font height smaller than
                        the given value. If not set, the min_height is set to 1
    :param bold:        If set to True, the function calculates the font with
                        setting bold
    :param text:        String to which the maximum size is to be calculated
    :param max_width:   Give the maximal available width space in pixel
    :param max_height:  Give the maximal available heigth space in pixel
    """

    i = min_height

    # get the max font size        
    for i in range(min_height, max_height):
        if bold is False:
            font = tkfont.Font(family='Arial', size=-i)
        else:
            font = tkfont.Font(family='Arial', size=-i, weight='bold')

        # get width and height of the string
        w, h = (font.measure(text), font.metrics("linespace"))

        # depend of available line break, decide to quit loop
        if line_break is True:
            # calculate the expected lines depend on the width of the
            # screen. Round up to reach the save side
            expect_lines = math.ceil(float(w) / float(max_width))

            # calculate the over all height by considering the amount of lines
            height_over_all = h * expect_lines
            if height_over_all >= max_height:
                break
        else:
            if (w >= max_width) or (h >= max_height):
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

    # ----------------------------------------------------------------------
    def callback(self):
        self.f(*self.args, **self.kwargs)
        self.start()

    # ----------------------------------------------------------------------
    def cancel(self):
        # increase robustness
        if self.is_alive():
            self.timer.cancel()

    # ----------------------------------------------------------------------
    def start(self):
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()

    # ----------------------------------------------------------------------
    def is_alive(self):
        if self.timer is None:
            return False
        else:
            return self.timer.is_alive()

    # ----------------------------------------------------------------------
    def join(self, timeout):
        if self.timer is None:
            return
        else:
            return self.timer.join(timeout)
