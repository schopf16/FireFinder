#!/usr/bin/env python
# -*- coding: latin-1-*-

"""
    Copyright (C) 2016  Michael Anderegg <m.anderegg@gmail.com>

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

from tkinter import font as tkfont
from datetime import datetime
from threading import Thread
from firefinder.ff_miscellaneous import create_image

""" Path's """
# ffLogo = 'pic/Logo.png'  # Firefighter Logo


########################################################################    
class TopBar(tk.Frame):
    def __init__(self, parent, height):

        super(TopBar, self).__init__(parent)

        self.parent = parent  # master of this widget
        self.wdr = ""
        self.time_date_string = ""

        # size dependend variables
        self.borderwidth = 0  # the canvas borderwidth
        self.width = self.winfo_screenwidth()  # total width of widget
        self.height = height - (2 * self.borderwidth)  # total height of widget

        # configs for the clock
        self.showTime = True
        self.showSeconds = True
        self.showDate = True
        self.showWeekDay = True
        self.WeekDayString = ['Montag',  # Weekday 0
                              'Dienstag',  # Weekday 1
                              'Mittwoch',  # Weekday 2
                              'Donnerstag',  # Weekday 3
                              'Freitag',  # Weekday 4
                              'Samstag',  # Weekday 5
                              'Sonntag']  # Weekday 6

        # configs for miscellaneous
        self.showLogo = True  # True if Logo has to be display
        self.pathLogo = None  # Path and filename with extending
        self.picLogo = None  # Hold the picutre
        self.companyName = ""  # Shows the company name on the rightside of the logo

        # store label container
        self.canvas = None
        self.lblLogo = None
        self.lblTime = None
        self.lblCompany = None

        self.background = 'black'
        self.foreground = 'white'

        # store a object to cancel pending jobs
        self.__job = None

        self.create_widget()  # create the widget
        self.paint_logo()
        self.painthms()

    # ----------------------------------------------------------------------
    def create_widget(self):

        # If the images doesn't fit to the full width of the screen
        # add a dummy canvas to force filling the full width of the
        # screen. This is a ugly hack, change it as soon as you know
        # why the f*** this happen
        self.canvas = tk.Canvas(self,
                                width=self.width,
                                height=self.height,
                                background=self.background,
                                borderwidth=self.borderwidth,
                                highlightthickness=0)

        self.canvas.pack(side='left', fill='both', expand=True)

        # create a font depend from the height of the widget
        font = tkfont.Font(family='Arial', size=-self.height, weight='bold')

        # Create labels for logo and time
        self.lblLogo = tk.Label(self.canvas,
                                background=self.background)
        self.lblTime = tk.Label(self.canvas,
                                background=self.background,
                                foreground=self.foreground,
                                font=font)
        self.lblCompany = tk.Label(self.canvas,
                                   background=self.background,
                                   foreground=self.foreground,
                                   font=font)

        # Pack label on canvas
        self.lblLogo.pack(side='left')
        self.lblCompany.pack(side='left')
        self.lblTime.pack(side='right')

    # ----------------------------------------------------------------------
    def paint_logo(self):

        if self.showLogo is True and self.pathLogo is not None:
            # check if path is ok
            if os.path.isfile(self.pathLogo) is True:
                self.picLogo = create_image(self,
                                            path=self.pathLogo,
                                            height=self.height)
            else:
                print("ERROR: SLIDESOW COMPANY LOGO CAN'T BE SHOWN")
                self.picLogo = ''

            self.lblLogo["image"] = self.picLogo
        else:
            self.lblLogo["image"] = ""

        self.lblCompany["text"] = " " + self.companyName
        pass

    # ----------------------------------------------------------------------
    def painthms(self):
        act_time = datetime.timetuple(datetime.now())
        year, month, day, h, m, s, wd, x, x = act_time  # @UnusedVariable

        # Create a string, depend on the user settings
        if self.showSeconds is True:
            time_string = ('%02i:%02i:%02i' % (h, m, s))
        else:
            time_string = ('%02i:%02i' % (h, m))

        if self.showWeekDay is True:
            date_string = ('%s, %02i.%02i.%04i' % (self.WeekDayString[wd], day, month, year))
        else:
            date_string = ('%02i.%02i.%04i' % (day, month, year))

        # Put the strings together to fit the needs of the configuration   
        self.time_date_string = ""
        if self.showTime is True and self.showDate is False:
            self.time_date_string = time_string

        if self.showTime is False and self.showDate is True:
            self.time_date_string = date_string

        if self.showTime is True and self.showDate is True:
            self.time_date_string = time_string + "  //  " + date_string

        self.lblTime["text"] = self.time_date_string + "  "

    # ----------------------------------------------------------------------
    def configure(self, **kw):

        change_time_settings = False
        change_logo_settings = False

        if len(kw) == 0:  # return a dict of the current configuration
            cfg = {'showSecond': self.showSeconds, 'showTime': self.showTime, 'showDate': self.showDate,
                   'showWeekDay': self.showWeekDay, 'setPathAndFile': self.pathLogo, 'showLogo': self.showLogo,
                   'companyName': self.companyName, 'background': self.background, 'foreground': self.foreground}
            return cfg

        else:  # do a configure
            for key, value in list(kw.items()):
                if key == 'showSecond':
                    self.showSeconds = value
                    change_time_settings = True
                elif key == 'showTime':
                    self.showTime = value
                    change_time_settings = True
                elif key == 'showDate':
                    self.showDate = value
                    change_time_settings = True
                elif key == 'showWeekDay':
                    self.showWeekDay = value
                    change_time_settings = True
                elif key == 'background':
                    self.background = value
                    self.canvas["background"] = value
                    self.lblTime["background"] = value
                    self.lblLogo["background"] = value
                    self.lblCompany["background"] = value
                    change_time_settings = True
                    change_logo_settings = True
                elif key == 'foreground':
                    self.foreground = value
                    self.lblTime["foreground"] = value
                    self.lblLogo["foreground"] = value
                    self.lblCompany["foreground"] = value
                    change_time_settings = True
                    change_logo_settings = True
                elif key == 'setPathAndFile':
                    self.pathLogo = value
                    change_logo_settings = True
                elif key == 'showLogo':
                    self.showLogo = value
                    change_logo_settings = True
                elif key == 'companyName':
                    self.companyName = value
                    change_logo_settings = True
                elif key == 'logoPathAndFile':
                    self.pathLogo = value
                    change_logo_settings = True

            if change_time_settings is True:
                self.painthms()

            if change_logo_settings is True:
                self.paint_logo()

    # ----------------------------------------------------------------------
    def poll(self):
        self.painthms()
        self.__job = self.after(200, self.poll)

    # ----------------------------------------------------------------------
    def __del__(self):
        pass
        # for widget in self.winfo_children():
        # widget.destroy()

    # ----------------------------------------------------------------------
    def descent_screen(self):
        if self.__job is not None:
            self.after_cancel(self.__job)
            self.__job = None
        pass

    # ----------------------------------------------------------------------
    def raise_screen(self):
        if self.__job is None:
            self.__job = self.after_idle(self.poll)
        pass


########################################################################
def test_screen_top():
    print("Start Test")
    bar.raise_screen()
    time.sleep(1)

    bar.configure(companyName="Feuerwehr Ittigen")
    time.sleep(1)

    bar.configure(showLogo=False)
    time.sleep(1)

    bar.configure(showTime=False)
    time.sleep(1)

    bar.configure(showDate=False)
    time.sleep(1)

    bar.configure(showLogo=True)
    time.sleep(1)

    bar.configure(companyName="")
    time.sleep(1)

    bar.configure(foreground='blue')
    time.sleep(1)

    bar.configure(showDate=True)
    time.sleep(1)

    bar.configure(companyName="Feuerwehr Ittigen")
    time.sleep(1)

    bar.configure(showWeekDay=False)
    time.sleep(1)

    bar.configure(background='green')
    time.sleep(1)

    bar.configure(showTime=True)
    time.sleep(1)

    bar.configure(background='grey')
    time.sleep(1)

    bar.configure(foreground='red')
    time.sleep(1)

    bar.configure(showWeekDay=True)
    time.sleep(3)

    bar.descent_screen()
    time.sleep(1)

    bar.__del__()

    print("Test ende")


######################################################################## 
if __name__ == '__main__':
    # wbar = 1920
    wbar = 1800
    hbar = 40

    root = tk.Tk()
    root.geometry("%dx%d+0+0" % (wbar + 10, hbar + 10))

    bar = TopBar(root, height=hbar)
    bar.pack(fill='both')

    thread = Thread(target=test_screen_top, args=())
    thread.start()

    root.mainloop()
