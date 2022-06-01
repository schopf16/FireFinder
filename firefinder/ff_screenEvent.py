#!/usr/bin/env python
# -*- coding: latin-1-*-

"""
    Copyright (C) 2016  Michael Anderegg <michael@anderegg.be>

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
import time
import tkinter as tk

from threading import Thread
from tkinter import font as tkfont
from PIL import ImageTk, Image

# my very own classes
from firefinder.ff_miscellaneous import create_image, get_text_font_size
from firefinder.ff_footer import ProgressBar, ResponseOrder

""" Path's """
backgroundImage = 'pic/bg'  # Path to background Image for alarm message
noImage = 'pic/bg/no_image.png'  # Image, of desired image is not found

"""
callable object to call the screen object configure method.
Used to overwrite methods of class instances
"""


class ScreenEvent(tk.Frame):
    def __init__(self, parent, controller):

        super(ScreenEvent, self).__init__(parent)

        # store parent objects
        self.parent = parent
        self.controller = controller

        # store size of the parent frame
        self.controller.update()
        self.screenWidth = self.controller.winfo_width()
        self.screenHeight = self.controller.winfo_height()
        if (self.screenWidth < 640) or (self.screenHeight < 480):
            print("WARNING: Low screen resolution {} x {}!!".format(self.screenWidth, self.screenHeight))

        # Store the height of the several places
        self.alarmMessageBarHeight = 220  # Pixel
        self.progressBarHeight = 100  # Pixel
        self.responseOrderHeight = 150  # Pixel

        # store working directory
        try:
            self.wdr = os.path.dirname(__file__)
        except:
            self.wdr = os.getcwd()
        self.pathToIniFile = ''

        self.alarmMessageUseTicker = False
        self.alarmMessage = ''
        self.category = ''
        self.categoryImage = ''
        self.nameOfPicture_1 = ''
        self.nameOfPicture_2 = ''
        self.cropPicture = False
        self.pic1Img = ''
        self.pic2Img = ''

        self.showProgressBar = False
        self.progressBarTime = 0

        # Response order bar
        self.responseOrderBar = None
        self.showResponseOrder = False
        self.responseOrder = ''
        self.borderwidthROB = 2
        self.backgroundROB = 'gray'
        self.equipment = {}
        self.equipmentImg = {}

        # create some instance for the widget
        self.alarmMessageBar = tk.Canvas(self)
        self.pictureBar = tk.Canvas(self)
        self.pic_1 = tk.Label(self.pictureBar)
        self.pic_2 = tk.Label(self.pictureBar)
        self.progressBar = ProgressBar(self,
                                       width=self.screenWidth,
                                       height=self.progressBarHeight,
                                       pixel_per_slice=1)
        self.responseOrderBar = ResponseOrder(self,
                                              width=self.screenWidth,
                                              height=self.responseOrderHeight)
        self.alarmMessageBarImage = self.alarmMessageBar.create_image(0, 0, anchor='nw')
        self.alarmMessageBarText = self.alarmMessageBar.create_text(self.screenWidth / 2,
                                                                    self.alarmMessageBarHeight / 2,
                                                                    fill="black",
                                                                    justify='center')

        self.create_widget()

    # ----------------------------------------------------------------------
    def create_widget(self):

        """
        +-------alarmMessageBar-------+
        |                             |
        |                             |
        +-----------------------------+

        +----------pictureBar---------+
        |+-------------+-------------+|
        ||             |             ||
        ||  Left       | Right       ||
        ||  Picture    | Picture     ||
        ||  (pic_1)    | (pic_2)     ||
        |+-------------+-------------+|
        +-----------------------------+

        +---------progressBar---------+
        |XXXXXXXX                     |
        +-----------------------------+

        +------responseOrderBar-------+
        |                             |
        +-----------------------------+

        This function creates 4 frames. Each can shown or
        hide independently.
        """

        height_picture_bar = self.screenHeight - self.alarmMessageBarHeight

        # Create a canvas to hold the top event bar
        self.alarmMessageBar.config(width=self.screenWidth,
                                    height=self.alarmMessageBarHeight,
                                    highlightthickness=0)

        # Create a canvas to hold the map
        self.pictureBar.config(width=self.screenWidth,  # WIDTH,
                               height=height_picture_bar,  # HEIGHT,
                               background='black',
                               highlightthickness=0)

        # Place both Canvas
        self.alarmMessageBar.pack(side='top')
        self.pictureBar.pack(side='top', fill='both')

        # Disable auto resize to its childs wigets
        self.pictureBar.pack_propagate(False)

        """ Create a label for the left picture """
        self.pic_1.config(bd=0, background='black', foreground='black')
        self.pic_2.config(bd=0, background='black', foreground='black')

    # ----------------------------------------------------------------------
    def configure(self, **kw):

        change_pciture = False

        if len(kw) == 0:  # return a dict of the current configuration
            cfg = {'alarmMessage'     : self.alarmMessage,
                   'picture_1'        : self.nameOfPicture_1,
                   'picture_2'        : self.nameOfPicture_2,
                   'cropPicture'      : self.cropPicture,
                   'category'         : self.category,
                   'showProgressBar'  : self.showProgressBar,
                   'progressBarTime'  : self.progressBarTime,
                   'showResponseOrder': self.showResponseOrder,
                   'responseOrder'    : self.responseOrder,
                   'pathToIniFile'    : self.pathToIniFile}
            return cfg

        else:  # do a configure
            for key, value in list(kw.items()):
                if key == 'pathToIniFile':
                    self.pathToIniFile = value
                elif key == 'category':
                    if value.lower() is not self.category:
                        self.set_category(value)
                elif key == 'cropPicture':
                    if value is not self.cropPicture:
                        self.set_crop_picture(value)
                elif key == 'alarmMessage':
                    if value is not self.alarmMessage:
                        self.set_event_message(value)
                elif key == 'picture_1':
                    change_pciture = True
                    self.nameOfPicture_1 = value
                elif key == 'picture_2':
                    change_pciture = True
                    self.nameOfPicture_2 = value
                elif key == 'showResponseOrder':
                    if value is not self.showResponseOrder:
                        self.set_show_response_order(value)
                elif key == 'responseOrder':
                    if value is not self.responseOrder:
                        self.set_response_order(value)
                elif key == 'showProgressBar':
                    self.set_show_progressbar(value)
                elif key == 'progressBarTime':
                    if value is not self.progressBarTime:
                        self.set_progressbar_time(value)

            if self.pathToIniFile == '':
                print("WARNING: Path to ini-file yet not set")

            if change_pciture is True:
                self.set_picture()

    # ----------------------------------------------------------------------
    def set_category(self, value):
        self.category = value.lower()
        path = os.path.join(self.wdr, backgroundImage, '%s.png' % self.category)
        if os.path.isfile(path):
            with Image.open(path) as logo:
                logo = logo.resize((self.screenWidth,
                                    self.alarmMessageBarHeight),
                                   Image.ANTIALIAS)
                self.categoryImage = ImageTk.PhotoImage(logo)
                self.alarmMessageBar.itemconfig(self.alarmMessageBarImage,
                                                image=self.categoryImage)
        else:
            print("ERROR:  Path \'%s\' does not lead to a background color" % path)

    # ----------------------------------------------------------------------
    def set_crop_picture(self, value):
        self.cropPicture = value
        self.set_picture()

    # ----------------------------------------------------------------------
    def set_event_message(self, value):
        self.alarmMessage = value

        font_size = get_text_font_size(max_height=int(self.alarmMessageBarHeight),
                                       min_height=70,
                                       max_width=int(self.screenWidth * .95),
                                       text=self.alarmMessage,
                                       line_break=True,
                                       bold=True)

        font = tkfont.Font(family='Arial', size=font_size, weight='bold')

        self.alarmMessageBar.itemconfig(self.alarmMessageBarText,
                                        text="%s" % self.alarmMessage,
                                        font=font,
                                        width=self.screenWidth)

    # ----------------------------------------------------------------------
    def set_picture(self):

        left_padding = 0

        # Calculate size of Images
        progress_height = int(self.showProgressBar) * self.progressBarHeight
        response_height = int(self.showResponseOrder) * self.responseOrderHeight
        event_height = int(self.alarmMessageBarHeight)

        # calculate height and width and resize the canvas afterwards
        pic_height = int(self.screenHeight - event_height - progress_height - response_height)
        pic_width = int(self.screenWidth)
        self.pictureBar.config(width=pic_width, height=pic_height)

        # if picture 2 is empty, show picture 1 as fullscreen and clear picture 2
        if self.nameOfPicture_2 != '':
            pic_width = int(pic_width / 2)
        else:
            self.pic_2.pack_forget()

        # Change and resize picture 1
        path = os.path.join(self.pathToIniFile, self.nameOfPicture_1)
        if os.path.isfile(path):
            self.pic1Img = create_image(self,
                                        path=path,
                                        width=pic_width,
                                        height=pic_height,
                                        crop=self.cropPicture)
        else:
            path = os.path.join(self.wdr, noImage)
            if os.path.isfile(path):
                self.pic1Img = create_image(self,
                                            path=path,
                                            width=pic_width,
                                            height=pic_height,
                                            keep_ratio=False)

        # Put picture on the screen
        self.pic_1["image"] = self.pic1Img
        if self.pic1Img != '':
            # recalculate left padding depend of the second picture
            if self.nameOfPicture_2 != '':
                left_padding = int((self.screenWidth / 4) - (self.pic1Img.width() / 2))
            else:
                left_padding = int((self.screenWidth / 2) - (self.pic1Img.width() / 2))

            self.pic_1.pack(side='left', ipadx=left_padding)
        else:
            print("ERROR: FAILED TO PLACE IMAGE 1")

            # Change and resize picture 2
        if self.nameOfPicture_2 != '':
            path = os.path.join(self.pathToIniFile, self.nameOfPicture_2)
            if os.path.isfile(path):
                self.pic2Img = create_image(self,
                                            path=path,
                                            width=pic_width,
                                            height=pic_height,
                                            crop=self.cropPicture)
            else:
                path = os.path.join(self.wdr, noImage)
                if os.path.isfile(path):
                    self.pic2Img = create_image(self,
                                                path=path,
                                                width=pic_width,
                                                height=pic_height,
                                                keep_ratio=False)

            # reposition picture and put it on the screen
            self.pic_2['image'] = self.pic2Img
            self.pic_2.pack(side='left', ipadx=left_padding)

    # ----------------------------------------------------------------------
    def set_show_response_order(self, value):
        self.showResponseOrder = value
        if self.showResponseOrder is True:
            self.responseOrderBar.pack(side='top', fill='both')
        else:
            self.responseOrderBar.pack_forget()

        # redraw picture
        self.set_picture()

    # ----------------------------------------------------------------------
    def set_response_order(self, value):
        self.responseOrder = value
        self.responseOrderBar.set_equipment(self.responseOrder)

    # ----------------------------------------------------------------------
    def set_show_progressbar(self, value):
        self.showProgressBar = value
        if self.showProgressBar is True:
            self.progressBar.pack(side='top', fill='both', after=self.pictureBar)
            self.progressBar.start(time_in_seconds=self.progressBarTime, start_value=0)
        else:
            self.progressBar.pack_forget()

        # redraw picture
        self.set_picture()

    # ----------------------------------------------------------------------
    def set_progressbar_time(self, value):
        self.progressBarTime = value

    # ----------------------------------------------------------------------
    def descent_screen(self):
        self.progressBar.stop()

    # ----------------------------------------------------------------------
    def raise_screen(self):
        # nothing to do while rise
        pass

    # ----------------------------------------------------------------------
    def __del__(self):
        for widget in self.winfo_children():
            widget.destroy()


########################################################################
def test_screenevent():
    print("Start Test")
    time.sleep(1)

    screen.configure(category='green')
    time.sleep(1)

    screen.configure(pathToIniFile='D:\Firefinder')
    time.sleep(1)

    screen.configure(picture_1='direction_1.jpg', picture_2='direction_detail_1.jpg')
    time.sleep(1)

    screen.configure(alarmMessage='test message')
    time.sleep(1)

    screen.configure(category='blue')
    time.sleep(1)

    screen.configure(picture_1='detail.jpg', picture_2='')
    time.sleep(1)

    screen.configure(picture_1='detail.jpg', picture_2='1.jpg')
    time.sleep(1)

    screen.configure(cropPicture=True)
    time.sleep(1)

    screen.configure(alarmMessage='Kp. 25, AA Sprinkler, Ittigen, Mühlestrasse 2, Verwaltungszentrum UVEK Ittigen')
    time.sleep(1)

    screen.configure(category='red')
    time.sleep(1)

    screen.configure(picture_1='detail.jpg', picture_2='detail.jpg')
    time.sleep(1)

    screen.configure(cropPicture=False)
    time.sleep(1)

    screen.configure(alarmMessage='Und nun folgt zum Testen eine wirklich lange Testnachricht. Damit soll '
                                  'geprüft werden, ob auch bei sehr langen Texten diese Schriftgrösse nie '
                                  'kleiner als 70 Pixel sein wird...')
    time.sleep(1)

    screen.configure(showResponseOrder=True)
    time.sleep(1)

    equipment = {}
    for x in range(1, 12):
        equipment[x] = 'Fz_5.png'
    for x in range(6, 12):
        equipment[x] = ""
    screen.configure(responseOrder=equipment)
    time.sleep(1)

    screen.configure(showResponseOrder=False)
    time.sleep(1)

    screen.configure(showResponseOrder=True)
    time.sleep(1)

    screen.configure(progressBarTime=30)
    time.sleep(1)

    screen.configure(showProgressBar=True)
    time.sleep(1)

    screen.configure(showResponseOrder=False)
    time.sleep(1)

    screen.configure(showResponseOrder=True)
    time.sleep(1)

    screen.configure(progressBarTime=20)
    time.sleep(1)

    screen.configure(showProgressBar=False)
    time.sleep(1)

    screen.configure(showProgressBar=True)
    time.sleep(1)

    screen.descent_screen()
    time.sleep(5)

    screen.__del__()

    print("Test ende")


########################################################################
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("%dx%d+0+0" % (root.winfo_screenwidth(), root.winfo_screenheight() - 200))

    container = tk.Frame(root)
    container.pack(side="top", fill="both", expand=False)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    screen = ScreenEvent(container, root)
    screen.grid(row=0, column=0, sticky="nsew")
    screen.tkraise()

    thread = Thread(target=test_screenevent, args=())
    thread.start()
    root.mainloop()
