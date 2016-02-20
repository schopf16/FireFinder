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

import time
import tkinter as tk

from threading import Thread
from datetime import datetime
from math import sin, cos, pi
from tkinter import font as tkfont


########################################################################
class Transformer:
    def __init__(self, world, viewport):
        """Constructor"""
        self.world = world
        self.viewport = viewport

    # ----------------------------------------------------------------------
    def point(self, x1, y1):
        x1_min, y1_min, x1_max, y1_max = self.world
        x2_min, y2_min, x2_max, y2_max = self.viewport
        f_x = float(x2_max - x2_min) / float(x1_max - x1_min)
        f_y = float(y2_max - y2_min) / float(y1_max - y1_min)
        f = min(f_x, f_y)
        x1_c = 0.5 * (x1_min + x1_max)
        y1_c = 0.5 * (y1_min + y1_max)
        x2_c = 0.5 * (x2_min + x2_max)
        y2_c = 0.5 * (y2_min + y2_max)
        c_1 = x2_c - f * x1_c
        c_2 = y2_c - f * y1_c
        x2 = f * x1 + c_1
        y2 = f * y1 + c_2
        return x2, y2

    # ----------------------------------------------------------------------
    def twopoints(self, x1, y1, x2, y2):
        return self.point(x1, y1), self.point(x2, y2)


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
        self.screenHeight = self.controller.winfo_height() - 200

        # Store which hands have to be shown
        self.showSecondHand = True
        self.showMinuteHand = True
        self.showHourHand = True
        self.showDigitalTime = True
        self.showDigitalDate = True
        self.showDigitalSeconds = False  # self.showDigitalTime must be True

        self.world = [-1, -1, 1, 1]
        self.bgcolor = '#000000'
        self.circlecolor = 'red'  # '#A0A0A0' #'#808080'
        self.timecolor = '#ffffff'
        self.circlesize = 0.10
        self._ALL = 'all'
        self.pad = 25

        self.WeekDayString = ['Montag',  # Weekday 0
                              'Dienstag',  # Weekday 1
                              'Mittwoch',  # Weekday 2
                              'Donnerstag',  # Weekday 3
                              'Freitag',  # Weekday 4
                              'Samstag',  # Weekday 5
                              'Sonntag']  # Weekday 6

        # Calculate ratio of the resolution
        self.aspectRatio = self.screenWidth / self.screenHeight

        # check if monitor has a portrait or landscape format
        if self.aspectRatio < 1:
            # portrait format
            height = self.screenWidth
        else:
            # landscape format
            height = self.screenHeight

        self.secondHandThickness = height / 180
        self.minuteHandThickness = height / 90
        self.hourHandThickness = height / 50
        self.heightAnalogClock = height

        # create viewport an pack canvas to screen
        viewport = (self.pad, self.pad, height - self.pad, height - self.pad)
        self.T = Transformer(self.world, viewport)

        # store a object to cancel pending jobs
        self.__job = None

        # create some instance for the widget
        self.analogClock = tk.Canvas(self)
        self.digitalClock = tk.Canvas(self)
        self.timeLabel = tk.Label(self.digitalClock)
        self.dateLabel = tk.Label(self.digitalClock)

        self.create_widget()

    # ----------------------------------------------------------------------
    def create_widget(self):
        """
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
        """

        ''' Create a object to hold the analog clock '''
        self.analogClock.config(width=self.screenWidth,
                                height=self.screenHeight,
                                background=self.bgcolor,
                                highlightthickness=0)

        self.analogClock.pack(side='top', fill='both')

        ''' Create a object to hold the digital clock '''
        self.digitalClock.config(width=self.screenWidth,
                                 height=5,
                                 background=self.bgcolor,
                                 highlightthickness=0)

        font = tkfont.Font(family='Arial', size=-120, weight='bold')
        self.timeLabel.config(bg='black', font=font, fg='white')
        self.dateLabel.config(bg='black', font=font, fg='white')
        self.timeLabel.pack(side='left', fill='both')
        self.dateLabel.pack(side='right', fill='both')
        self.digitalClock.pack(side='top', fill='both')

    # ----------------------------------------------------------------------
    def redraw(self):
        sc = self.analogClock
        sc.delete(self._ALL)
        width = self.screenWidth
        height = self.screenHeight
        sc.create_rectangle([[0, 0], [width, height]], fill=self.bgcolor, tag=self._ALL)
        viewport = (self.pad, self.pad, width - self.pad, height - self.pad)
        self.T = Transformer(self.world, viewport)
        self.paintgrafics()

    # ----------------------------------------------------------------------
    def paintgrafics(self):
        start = -pi / 2
        step = pi / 6
        for i in range(12):
            angle = start + i * step
            x, y = cos(angle), sin(angle)
            self.paintcircle(x, y)
        self.painthms()
        self.paintcircle(0, 0)

    # ----------------------------------------------------------------------
    def painthms(self):
        act_time = datetime.timetuple(datetime.now())
        year, month, day, h, m, s, wd, x, x = act_time  # @UnusedVariable

        # Adapt digital time
        if self.showDigitalSeconds is True:
            self.timeLabel["text"] = ('%02i:%02i:%02i' % (h, m, s))
        else:
            self.timeLabel["text"] = ('%02i:%02i' % (h, m))

        if self.showDigitalTime is True:
            self.dateLabel["text"] = ('%02i.%02i.%04i' % (day, month, year))
        else:
            self.dateLabel["text"] = ('%s, %02i.%02i.%04i' % (self.WeekDayString[wd], day, month, year))

        scl = self.analogClock.create_line

        # Draw hour hand
        if self.showHourHand is True:
            angle = -pi / 2 + (pi / 6) * h + (pi / 6) * (m / 60.0)
            x, y = cos(angle) * .60, sin(angle) * .60
            scl(self.T.twopoints(*[0, 0, x, y]), fill=self.timecolor, tag=self._ALL, width=self.hourHandThickness)

        # Draw minute hand
        if self.showMinuteHand is True:
            angle = -pi / 2 + (pi / 30) * m + (pi / 30) * (s / 60.0)
            x, y = cos(angle) * .80, sin(angle) * .80
            scl(self.T.twopoints(*[0, 0, x, y]), fill=self.timecolor, tag=self._ALL, width=self.minuteHandThickness)

        # Draw seconds hand
        if self.showSecondHand is True:
            angle = -pi / 2 + (pi / 30) * s
            x, y = cos(angle) * .95, sin(angle) * .95
            scl(self.T.twopoints(*[0, 0, x, y]), fill=self.timecolor, tag=self._ALL, arrow='last',
                width=self.secondHandThickness)

    # ----------------------------------------------------------------------
    def paintcircle(self, x, y):
        ss = self.circlesize / 2.0
        mybbox = [-ss + x, -ss + y, ss + x, ss + y]
        sco = self.analogClock.create_oval
        sco(self.T.twopoints(*mybbox), fill=self.circlecolor, tag=self._ALL)

    # ----------------------------------------------------------------------
    def poll(self):
        self.redraw()
        self.__job = self.after(200, self.poll)

    # ----------------------------------------------------------------------
    def set_geometry(self, value):
        self.screenWidth = value[0]
        self.screenHeight = value[1]

        # Calculate ratio of the resolution
        self.aspectRatio = self.screenWidth / self.screenHeight
        if self.aspectRatio < 1:
            # portrait format
            height = self.screenWidth
        else:
            # landscape format
            height = self.screenHeight

        self.secondHandThickness = height / 216
        self.minuteHandThickness = height / 90
        self.hourHandThickness = height / 50

        self.analogClock.config(width=self.screenWidth, height=self.screenHeight)
        self.digitalClock.config(width=self.screenWidth, height=self.screenHeight)

    # ----------------------------------------------------------------------
    def change_digital_time(self):
        # delete both from screen. They will packed below
        self.timeLabel.pack_forget()
        self.dateLabel.pack_forget()

        if (self.showDigitalTime is True) and (self.showDigitalDate is True):
            self.timeLabel.pack(side='left', fill='both')
            self.dateLabel.pack(side='right', fill='both')
            return

        if (self.showDigitalTime is False) and (self.showDigitalDate is True):
            self.dateLabel.pack(ipadx=int(self.screenWidth / 2))
            return

        if (self.showDigitalTime is True) and (self.showDigitalDate is False):
            self.timeLabel.pack(ipadx=int(self.screenWidth / 2))
            return
        pass

    # ----------------------------------------------------------------------
    def configure(self, **kw):

        if len(kw) == 0:  # return a dict of the current configuration
            cfg = {'showSecondHand': self.showSecondHand, 'showMinuteHand': self.showMinuteHand,
                   'showHourHand': self.showHourHand, 'set_geometry': [self.screenWidth, self.screenHeight],
                   'showDigitalTime': self.showDigitalTime, 'showDigitalDate': self.showDigitalDate,
                   'showDigitalSeconds': self.showDigitalSeconds}
            return cfg

        else:  # do a configure
            for key, value in list(kw.items()):
                if key == 'showSecondHand':
                    self.showSecondHand = value
                elif key == 'showMinuteHand':
                    self.showMinuteHand = value
                elif key == 'showHourHand':
                    self.showHourHand = value
                elif key == 'set_geometry':
                    self.set_geometry(value)
                elif key == 'showDigitalTime':
                    self.showDigitalTime = value
                    self.change_digital_time()
                elif key == 'showDigitalDate':
                    self.showDigitalDate = value
                    self.change_digital_time()
                elif key == 'showDigitalSeconds':
                    self.showDigitalSeconds = value

            self.redraw()

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
def test_screenclock():
    print("Start Test")
    time.sleep(1)

    screen.configure(showSecondHand=False)
    time.sleep(1)

    screen.configure(showMinuteHand=False)
    time.sleep(1)

    screen.configure(showHourHand=False)
    time.sleep(1)

    screen.configure(showSecondHand=True)
    time.sleep(1)

    screen.configure(showMinuteHand=True)
    time.sleep(1)

    screen.configure(showHourHand=True)
    time.sleep(1)

    screen.configure(showDigitalSeconds=True)
    time.sleep(10)

    screen.configure(setGeometry=[400, 200])
    time.sleep(1)

    screen.configure(setGeometry=[400, 400])
    time.sleep(1)

    screen.configure(setGeometry=[200, 200])
    time.sleep(1)

    screen.configure(setGeometry=[800, 800])
    time.sleep(1)

    screen.configure(showDigitalDate=False)
    time.sleep(1)

    screen.configure(showDigitalDate=True)
    time.sleep(1)

    screen.configure(showDigitalTime=False)
    time.sleep(1)

    screen.descent_screen()
    time.sleep(1)

    print("Test ende")


######################################################################## 
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("%dx%d+0+0" % (root.winfo_screenwidth(), root.winfo_screenheight() - 200))

    container = tk.Frame(root)
    container.pack(side="top", fill="both", expand=True)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    screen = ScreenClock(container, root)
    screen.grid(row=0, column=0, sticky="nsew")
    screen.tkraise()

    thread = Thread(target=test_screenclock, args=())
    thread.start()
    root.mainloop()
