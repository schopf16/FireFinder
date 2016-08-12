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

from tkinter import font as tkfont
from threading import Thread
from firefinder.ff_miscellaneous import create_image, get_text_font_size


class ProgressBar(tk.Frame):
    def __init__(self, parent, width, height, pixel_per_slice=1):
        super(ProgressBar, self).__init__(parent)

        if pixel_per_slice <= 0:
            pixel_per_slice = 1

        self.parent = parent  # master of this widget

        # size dependend variables
        self.borderwidth = 2  # the canvas borderwidth
        self.width = width - (2 * self.borderwidth)  # total width of widget
        self.height = height - (2 * self.borderwidth)  # total height of widget

        # grafical dependend variables
        self.frame = None  # the frame holding canvas & label
        self.canvas = None  # the canvas holding the progress bar
        self.progressBar = None  # the progress bar geometry
        self.backgroundBar = None  # the background bar geometry
        self.textLabel = None  # the Text shown in the progress bar
        self.text = ''  # the text string of the label
        self.increment = 0  # stores the width of the progress in pixel
        self.pixelPerSlice = pixel_per_slice  # Amount of pixel per slice
        # less pixel seems more fluence, but needs
        # more processor time

        self.progressActiv = False

        # Timings
        self.timeStartMs = 0  # store the time at which the progress bar was launched
        self.durationMs = 0  # Store the duration of the progress bar

        self.msPerSlice = 0
        self.bgColor = 'grey'
        self.fgColor = 'red'
        self.txtColor = 'white'
        self.colorScheme = [[0, 'red'],
                            [90, 'orange'],
                            [100, 'green']]

        self.textScheme = [[0, "Warte auf Atemschutz-Geräteträger"],
                           [90, "Bereitmachen zum Ausrücken"],
                           [100, "Losfahren, auch bei zuwenig Atemschutz-Geräteträger"]]

        self.create_widget()  # create the widget

    # ----------------------------------------------------------------------
    def create_widget(self):

        self.canvas = tk.Canvas(self,
                                width=self.width,
                                height=self.height)

        # create the background bar geometry
        self.backgroundBar = self.canvas.create_rectangle(
            self.borderwidth,
            self.borderwidth,
            self.width,
            self.height,
            fill=self.bgColor)

        # create the progress bar geometry
        self.progressBar = self.canvas.create_rectangle(
            self.borderwidth,
            self.borderwidth,
            0,  # Start without any progress bar
            self.height,
            fill=self.fgColor)

        # create a text lable in the middle of the progess bar
        if self.text == '':
            font = tkfont.Font(family='Arial', size=10)
        else:
            font_size = get_text_font_size(text=self.text,
                                           max_height=self.height,
                                           max_width=self.width * 0.98)

            font = tkfont.Font(family='Arial', size=font_size)

        self.textLabel = self.canvas.create_text(
            int(self.width / 2),
            int((self.height / 2) + self.borderwidth),
            text=self.text,
            fill=self.txtColor,
            font=font,
            justify='center')

        # pack the canvas into the frame
        self.canvas.pack()

    # ----------------------------------------------------------------------
    def update_grafic(self):
        self.canvas.coords(self.progressBar,
                           self.borderwidth,
                           self.borderwidth,
                           self.increment,
                           self.height)

    # ----------------------------------------------------------------------
    def set_text(self, text=''):
        if text == '':
            self.canvas.itemconfig(self.textLabel, text='')
        else:
            font_size = get_text_font_size(text=text,
                                           max_height=self.height,
                                           max_width=self.width * 0.98)
            font = tkfont.Font(family='Arial', size=font_size)
            self.canvas.itemconfig(self.textLabel, text=text, font=font)

        self.text = text

    # ----------------------------------------------------------------------
    def set_color(self, color=''):
        if color == '':
            color = 'blue'
        self.fgColor = color
        self.canvas.itemconfig(self.progressBar, fill=color)

    # ----------------------------------------------------------------------
    def get(self):
        return (self.increment / self.width) * 100.0

    # ----------------------------------------------------------------------
    def reset(self):
        self.stop()
        self.increment = 0

    # ----------------------------------------------------------------------
    def start(self, time_in_seconds, start_value=None):

        # It seem senseless to have a progress time of 0 seconds...
        if time_in_seconds == 0:
            print("ERROR: PROGRESS-TIME CAN'T BE ZERO")
            return

        # The start_value can't be greater than the full time_in_seconds
        if start_value > time_in_seconds:
            start_value = time_in_seconds

        # Store necessary time informations
        self.timeStartMs = int(round(time.time() * 1000))
        self.durationMs = int(round(time_in_seconds * 1000))

        # To get a smooth progress, calculate the time in milliseconds in
        # which the draw function has to be called.
        self.msPerSlice = int((time_in_seconds * 1000) / (self.width / self.pixelPerSlice))

        if start_value is not None:
            if start_value > self.width:
                self.increment = self.width
            else:
                self.increment = start_value

        if self.progressActiv is False:
            self.progressActiv = True
            self.after_idle(self.auto_run_progressbar)

    # ----------------------------------------------------------------------
    def stop(self):
        self.progressActiv = False

    # ----------------------------------------------------------------------
    def auto_run_progressbar(self):

        # check if progressbar has to be terminated
        if self.progressActiv is not True:
            return

        '''
            Calculate the progress accurate as possible.
            This is done by the system time. This is more
            precise than the calculations with msPerSlice
            because with the system time I can decrease the
            jitter.
        '''
        act_time_ms = int(round(time.time() * 1000))
        time_elapse_ms = act_time_ms - self.timeStartMs
        progress = (100 / self.durationMs) * time_elapse_ms

        # handle overflow
        if progress > 100:
            progress = 100

        index_color = 0
        index_text = 0

        # check if the correct color scheme is chosen
        for i in range(len(self.colorScheme)):
            if progress >= self.colorScheme[i][0]:
                index_color = i
        if self.fgColor != self.colorScheme[index_color][1]:
            self.set_color(self.colorScheme[index_color][1])

            # check if the correct text scheme is chosen
        for i in range(len(self.textScheme)):
            if progress >= self.textScheme[i][0]:
                index_text = i
        if self.text != self.textScheme[index_text][1]:
            self.set_text(self.textScheme[index_text][1])

        # Update progress bar
        if self.increment < self.width:
            self.increment = int((self.width / 100) * progress)
            self.update_grafic()
            self.after(self.msPerSlice, self.auto_run_progressbar)
        else:
            self.increment = self.width
            self.update_grafic()
            self.progressActiv = False
            return

    # ----------------------------------------------------------------------
    def __del__(self):
        for widget in self.winfo_children():
            widget.destroy()


########################################################################
class ResponseOrder(tk.Frame):
    def __init__(self, parent, width, height):

        super(ResponseOrder, self).__init__(parent)

        self.parent = parent  # master of this widget

        # size dependend variables
        self.borderwidth = 2  # the canvas borderwidth
        self.width = width - (2 * self.borderwidth)  # total width of widget
        self.height = height - (2 * self.borderwidth)  # total height of widget

        # grafical dependend variables
        self.frame = None  # the frame holding canvas & label
        self.frameVisual = None
        self.canvas = None  # the canvas holding the progress bar

        self.equipment = {}
        self.equipmentImg = {}
        self.wdr = ""

        self.background = 'gray'

        self.create_widget()  # create the widget

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

        # Create a set of 12 labels to hold the truck and trailer-images
        for x in range(1, 10):
            self.equipment[x] = tk.Label(self.canvas, background=self.background)
            self.equipment[x].pack(side='left', fill='both')

            # store working directory
        try:
            self.wdr = os.path.dirname(__file__)
        except:
            self.wdr = os.getcwd()

    # ----------------------------------------------------------------------
    def set_equipment(self, equipment):
        # generate the truck pictures concerning inputs
        for x in equipment:
            if equipment[x] is not '':
                path = os.path.join(self.wdr, 'pic', equipment[x])
                self.equipmentImg[x] = create_image(self.master, path, height=self.height)
                self.equipment[x]["image"] = self.equipmentImg[x]
            else:
                self.equipmentImg[x] = ''

    # ----------------------------------------------------------------------
    def __del__(self):
        for widget in self.winfo_children():
            widget.destroy()


########################################################################
def test_screen_footer():
    print("Start Test")
    time.sleep(1)

    bar.start(time_in_seconds=30, start_value=0)
    time.sleep(1)

    # create a tulpe and clear it
    equipment = {}
    for x in range(1, 12):
        equipment[x] = ''

    # add 5 car to footer
    equipment[1] = 'Fz_5.png'
    equipment[2] = 'Fz_6.png'
    equipment[3] = 'Fz_7.png'
    equipment[4] = 'Fz_1.png'
    equipment[5] = 'Fz_4.png'
    print("Add cars")
    truck.set_equipment(equipment=equipment)
    time.sleep(1)

    # delete the three last cars
    equipment[1] = 'Fz_5.png'
    equipment[2] = 'Fz_6.png'
    equipment[3] = ''
    equipment[4] = ''
    equipment[5] = ''
    print("delete the three last cars")
    truck.set_equipment(equipment=equipment)
    time.sleep(1)

    # add them again
    equipment[1] = 'Fz_5.png'
    equipment[2] = 'Fz_6.png'
    equipment[3] = 'Fz_4.png'
    equipment[4] = 'Fz_7.png'
    equipment[5] = 'Fz_1.png'
    print("add them again")
    truck.set_equipment(equipment=equipment)
    time.sleep(1)

    bar.stop()
    time.sleep(2)

    bar.start(time_in_seconds=420, start_value=0)
    time.sleep(1)

    print("Test ende")


########################################################################
if __name__ == '__main__':

    wbar = 1700
    hbar = 200
    wres = 1700
    hres = 100

    root = tk.Tk()
    if wbar > wres:
        root.geometry("%dx%d+0+0" % (wbar + 10, hres + hbar + 10))
    else:
        root.geometry("%dx%d+0+0" % (wres + 10, hres + hbar + 10))

    bar = ProgressBar(root, width=wbar, height=hbar, pixel_per_slice=1)
    bar.pack(fill='both')

    truck = ResponseOrder(root, width=wres, height=100)
    truck.pack(fill='both')

    thread = Thread(target=test_screen_footer, args=())
    thread.start()

    root.mainloop()
