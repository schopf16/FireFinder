#!/usr/bin/env python
# -*- coding: latin-1-*-

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
import tkinter as tk

# my very own classes
from firefinder.miscellaneous import create_image
from firefinder.top import TopBar

""" Path's """
ffLogo = 'pic/Logo.png'  # Firefighter Logo


class ScreenOff(tk.Frame):
    def __init__(self, parent, controller, **kw):

        # store parent objects
        super().__init__(**kw)
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller

        # store working directory
        try:
            self.wdr = os.path.dirname(__file__)
        except:
            self.wdr = os.getcwd()

        # store size of the parent frame        
        self.controller.update()
        self.screenWidth = self.controller.winfo_width()
        self.screenHeight = self.controller.winfo_height()
        self.topBarHeight = 30
        self.emblemBarHeight = self.screenHeight - self.topBarHeight

        # create some instance for the widget
        self.topHeader = TopBar(self, height=self.topBarHeight)
        self.emblemBar = tk.Canvas(self)
        self.picture = tk.Label(self.emblemBar)
        self.emptyBar = tk.Canvas(self)
        self.image = ''

        # create widget
        self.create_widget()

        # show as soon as mainloop is idle
        self.after_idle(self.show)

    # ----------------------------------------------------------------------
    def create_widget(self):

        """ Create a TopBar object """
        self.topHeader.configure(showLogo=False)
        self.topHeader.pack(fill='both')

        ''' Create a canvas to hold the top emblem '''
        self.emblemBar.config(width=self.screenWidth,
                              height=self.emblemBarHeight,
                              background='black',
                              highlightthickness=0)

        self.picture.config(bd=0,
                            background='black',
                            foreground='black')

        ''' Create a canvas to hold a failure image '''
        self.emptyBar.config(width=self.screenWidth,
                             height=self.emblemBarHeight,
                             background='black',
                             highlightthickness=0)

        self.emptyBar.create_line(0, 0, self.screenWidth, self.screenHeight, fill='red', width=5)
        self.emptyBar.create_line(self.screenWidth, 0, 0, self.screenHeight, fill='red', width=5)

    # ----------------------------------------------------------------------
    def show(self):

        # Create a logo with the firefighter Emblem
        path = os.path.join(self.wdr, ffLogo)
        if os.path.isfile(path):
            # create screen for object
            self.image = create_image(self,
                                      path=path,
                                      width=self.screenWidth - 20,
                                      height=self.emblemBarHeight - 20)

            self.picture['image'] = self.image
            self.emptyBar.pack_forget()
            self.emblemBar.pack(fill='both')
            top_paddy = int((self.emblemBarHeight / 2) - (self.image.height() / 2))
            self.picture.pack(fill='both', ipady=top_paddy)
        else:
            self.emblemBar.pack_forget()
            self.emptyBar.pack(fill='both')

    # ----------------------------------------------------------------------
    def configure(self, **kwargs):
        # nothing to do
        pass

    # ----------------------------------------------------------------------
    def descent_screen(self):
        self.topHeader.descent_screen()
        pass

    # ----------------------------------------------------------------------
    def raise_screen(self):
        self.topHeader.raise_screen()
        pass


######################################################################## 
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("%dx%d+0+0" % (root.winfo_screenwidth(), root.winfo_screenheight() - 200))

    container = tk.Frame(root)
    container.pack(side="top", fill="both", expand=True)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    screen = ScreenOff(container, root)
    screen.grid(row=0, column=0, sticky="nsew")
    screen.tkraise()

    #     thread = Thread(target=test_screenevent, args=())
    #     thread.start()
    root.mainloop()
