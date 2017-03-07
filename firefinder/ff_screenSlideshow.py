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

## @package screenSlideshow
#  Documentation for this module.
#
#  More details.

import os
import time
import random
# import tkinter as tk
import pygame
import platform
from pygame.locals import *

from threading import Thread
from itertools import cycle

# my very own classes
from firefinder.ff_miscellaneous import create_image
from firefinder.ff_top import TopBar


class ScreenSlideshow(pygame.Surface):
    def __init__(self):

        # super(ScreenSlideshow, self).__init__(parent)
        pygame.Surface.__init__(self)

        # store parent objects
        self.parent = parent
        self.controller = controller

        # store size of the parent frame        
        self.controller.update()
        self.screenWidth = self.controller.winfo_width()
        self.screenHeight = self.controller.winfo_height()
        self.topBarHeight = 40
        self.pictureHeight = self.screenHeight - self.topBarHeight

        # set time between slides in seconds
        self.delay = 12

        # store path where the pictures for the slideshow are stored
        self.pathToIniFile = ''
        self.pathToImages = ''

        # Store settings for header-bar
        self.show_header_bar = True
        self.path_logo_file = ''
        self.company_name = ''

        # rebuild list of pictures
        self.pictures = 0
        self.file_names = []
        self.cycledList = ''
        self.fileInFolder = 0

        # default sort by alphabetical
        self.sortAlphabetically = False

        # store a object to cancel pending jobs
        self.__job = None

        # create some instance for the widget
        self.topHeader = TopBar(self, height=self.topBarHeight)
        self.picture_area = tk.Canvas(self)
        self.pic_1 = tk.Label(self.picture_area)

        self.create_widget()

    # ----------------------------------------------------------------------
    def create_widget(self):

        """ Create a TopBar object """
        self.topHeader.configure(showTime=False)
        self.topHeader.configure(background='grey')
        self.topHeader.configure(companyName="")

        # Configure the canvas and the label for the picture inside the canvas
        self.picture_area.config(width=self.screenWidth,  # WIDTH,
                                 height=self.pictureHeight,  # HEIGHT,
                                 background='black',
                                 highlightthickness=0)

        self.pic_1.config(bd=0, background='black', foreground='black', font=("Arial", 60))

        # Refresh the widget structure
        self.refresh_widget_structure()

    # ----------------------------------------------------------------------
    def refresh_widget_structure(self):
        # First delete all widgets
        self.topHeader.pack_forget()
        self.picture_area.pack_forget()

        # Show top header if available and calculate the max height of the
        # canvas which is shown below
        if self.show_header_bar is True:
            self.topHeader.pack(side='top', fill='both')
            self.pictureHeight = self.screenHeight - self.topBarHeight
        else:
            self.pictureHeight = self.screenHeight

        # Configure canvas depended of the header bar
        self.picture_area.config(width=self.screenWidth, height=self.pictureHeight)
        self.picture_area.pack(side='top', fill='both')

    # ----------------------------------------------------------------------
    def show_slides(self):
        # Check if path already set
        if self.pathToImages is '':
            print("ERROR: Path to slideshow folder not set yet")
            return

        # check if slideshow directory exists and create it if necessary 
        if not os.path.exists(self.pathToImages):
            os.makedirs(self.pathToImages)

        # check if there are new images or some are deleted
        count_file = len(
            [name for name in os.listdir(self.pathToImages) if os.path.isfile(os.path.join(self.pathToImages, name))])
        if count_file != self.fileInFolder:

            # delete the list
            self.file_names = []

            # load all images which could be shown
            included_extenstions = ['.jpg', '.jpeg', '.bmp', '.png', '.gif', '.eps', '.tif', '.tiff']
            for file in os.listdir(self.pathToImages):

                # get extension
                ext = os.path.splitext(file)[1]

                # check if extension is available
                if ext.lower() in included_extenstions:
                    self.file_names.append(os.path.join(self.pathToImages, file))

            # only proceed if there are any pictures found
            if self.file_names:
                if self.sortAlphabetically is True:
                    # put the list in alphabetical order
                    self.file_names = sorted(self.file_names)
                else:
                    # shuffle the list randomly
                    random.shuffle(self.file_names)
                # put list in a cycle
                self.cycledList = cycle(self.file_names)

            # store the amount of files
            self.fileInFolder = count_file

        # check if there is at least an image available
        if len(self.file_names):
            path = next(self.cycledList)  # get next picture from cycle
            self.pictures = create_image(self, path=path, keep_ratio=True, height=self.pictureHeight, width=self.screenWidth)
            left_padding = int((self.screenWidth / 2) - (self.pictures.width() / 2))
            self.pic_1.config(text="", image=self.pictures)
            self.pic_1.pack(side='left', ipadx=left_padding)
        else:
            self.pic_1.config(text="Keine Bilder zum Anzeigen :-(", image='')

            # wait to show the next picture
        self.__job = self.after(int(self.delay * 1000), self.show_slides)

    # ----------------------------------------------------------------------
    def configure(self, **kw):

        if len(kw) == 0:  # return a dict of the current configuration
            cfg = {'pathToIniFile': self.pathToIniFile, 'secondsBetweenImages': self.delay,
                   'sortAlphabetically': self.sortAlphabetically}
            return cfg

        else:  # do a configure
            for key, value in list(kw.items()):
                if key == 'pathToIniFile':
                    self.pathToIniFile = value
                    self.pathToImages = os.path.join(self.pathToIniFile, 'Slideshow')
                elif key == 'secondsBetweenImages':
                    if value is not self.delay:
                        self.set_delay(value)
                elif key == 'sortAlphabetically':
                    self.sortAlphabetically = value
                    self.fileInFolder = 0  # clear to force refresh folder
                elif key == 'logoPathAndFile':
                    self.path_logo_file = value
                    self.topHeader.configure(logoPathAndFile=self.path_logo_file)
                elif key == 'companyName':
                    self.company_name = value
                    self.topHeader.configure(companyName=self.company_name)
                elif key == 'showHeaderBar':
                    self.show_header_bar = value
                    self.refresh_widget_structure()

    # ----------------------------------------------------------------------
    def set_delay(self, value):
        self.delay = value
        # force restart slideshow
        if self.__job is not None:
            self.after_cancel(self.__job)
            self.__job = None
        self.__job = self.after_idle(self.show_slides)
        pass

    # ----------------------------------------------------------------------
    def descent_screen(self):
        if self.__job is not None:
            self.after_cancel(self.__job)
            self.__job = None
        self.topHeader.descent_screen()
        pass

    # ----------------------------------------------------------------------
    def raise_screen(self):
        if self.__job is None:
            self.__job = self.after_idle(self.show_slides)
        self.topHeader.raise_screen()
        pass


########################################################################         
def test_screenslideshow():
    print("Start Test")
    time.sleep(1)

    screen.raise_screen()
    time.sleep(1)

    screen.configure(pathToIniFile='D:\Firefinder')
    time.sleep(1)

    screen.raise_screen()
    time.sleep(10)

    print("change display time to 3 seconds")
    screen.configure(secondsBetweenImages=3)
    time.sleep(15)

    print("delete header")
    screen.configure(showHeaderBar=False)
    time.sleep(10)

    print("set header")
    screen.configure(showHeaderBar=True)
    time.sleep(5)

    print("change display time to 6 seconds")
    screen.configure(secondsBetweenImages=6)
    time.sleep(15)

    print('descent')
    screen.descent_screen()
    time.sleep(15)

    print('raise')
    screen.raise_screen()
    time.sleep(15)

    print("Test ende")


######################################################################## 
if __name__ == '__main__':

    fps = 30

    if platform.system == "Windows":
        os.environ['SDL_VIDEODRIVER'] = 'windib'

    pygame.init()
    infoObject = pygame.display.Info()
    # width = infoObject.current_w
    # height= infoObject.current_h
    width = infoObject.current_w - 100
    height = infoObject.current_h - 200
    print("Screen size {} x {}".format(width, height))
    screen = pygame.display.set_mode((width, height))

    # Clock-Objekt erstellen, das wir benötigen, um die Framerate zu begrenzen.
    clock = pygame.time.Clock()

    # Titel des Fensters setzen, Mauszeiger verstecken.
    pygame.display.set_caption("Test ff_screenSlideshow")
    pygame.mouse.set_visible(False)

    surface_slideshow = ScreenSlideshow()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

        screen.blit(surface_slideshow)
        pygame.display.update()
        clock.tick(fps)
    # container = tk.Frame(root)
    # container.pack(side="top", fill="both", expand=True)
    # container.grid_rowconfigure(0, weight=1)
    # container.grid_columnconfigure(0, weight=1)
    #
    # screen = ScreenSlideshow(container, root)
    # screen.grid(row=0, column=0, sticky="nsew")
    # screen.tkraise()
    #
    # thread = Thread(target=test_screenslideshow, args=())
    # thread.start()
    # root.mainloop()
