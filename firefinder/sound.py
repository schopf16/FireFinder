#!/usr/bin/env python
# -*- coding: UTF-8-*-

'''
    Copyright (C) 2015  Michael Anderegg

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

from pygame import mixer
import os
import threading
import time

class alarmSound():
    '''
    classdocs
    '''

    def __init__(self, path):
        '''
        Constructor
        '''
        mixer.init(frequency=22050, size=16, channels=2, buffer=4096)
        self.set_volume(0.75) # set volume to maximum
                
        self.actLoadedTitle         = 'none'        
        self.pathToSoundfolder      = path
        self.threadRunning          = False
        self.musicLoadSuccessfully  = False
        
    #----------------------------------------------------------------------    
    def start(self, loops=0, start=0.0, delay=0, pause=0):
        """        
        This will play the loaded music stream. If the music is already playing 
        it will be restarted.
        
        The loops argument controls the number of repeats a music will play. 
        play(5) will cause the music to played once, then repeated five times, 
        for a total of six. If the loops is -1 then the music will repeat 
        indefinitely.

        The starting position argument controls where in the music the song starts 
        playing. The starting position is dependent on the format of music playing.
        MP3 and OGG use the position as time (in seconds). MOD music it is the
        pattern order number. Passing a startpos will raise a NotImplementedError
        if it cannot set the start position
        """
        
        # do not start thread as long as the one is still runing
        if self.threadRunning != True:
            
            # start thread only if a music is loaded successfully
            if self.musicLoadSuccessfully == True:
                self.threadRunning     = True
                
                self.startDelay        = delay  # delay in seconds
                self.pauseBetweenTrack = pause  # pause between tracks in seconds
                self.loops             = loops  # number of repeats
                self.startOffset       = start  # starting position
                            
                self.st = threading.Thread(target=self.__soundThread)
                self.st.start() # start the thread which plays the given music
    
    #----------------------------------------------------------------------   
    def stop(self):
        """
        Stops the music playback if it is currently playing.
        """
        
        self.threadRunning = False
        
        try:    mixer.music.stop()
        except: print("Failed to stop music")
            
    #----------------------------------------------------------------------  
    def set_volume(self, volume = 0.5):
        """
        Set the volume of the music playback. The value argument is between 
        0.0 and 1.0. When new music is loaded the volume is reset.
        """
        mixer.music.set_volume(volume)
    
    #----------------------------------------------------------------------   
    def loadMusic(self, file):
        """
        Load a file into the music class. If the file remain the same,
        do not load again
        """
        if self.actLoadedTitle != file:
            path = os.path.join(self.pathToSoundfolder, file)
            try:    
                mixer.music.load(path)
                self.musicLoadSuccessfully = True
                self.actLoadedTitle        = file 
                self.stop()
            except: 
                self.musicLoadSuccessfully = False
                print(("Failed load music path: \"%s\"") %(path))
              
    #----------------------------------------------------------------------       
    def __soundThread(self):
                
        if self.startDelay != 0: 
            time.sleep(self.startDelay)
            
        while self.loops != 0:
            
            if self.threadRunning == False:
                return; 
            
            self.__playTrackOne(self.startOffset)
            
            while mixer.music.get_busy() == True:
                continue
            
            if self.loops != -1:    # Check if loop is infinit
                self.loops -= 1     # no, so decrement varaible by 1
            
            if self.pauseBetweenTrack != 0:
                time.sleep(self.pauseBetweenTrack)
        
        # Music played completely
        self.threadRunning = False               
                
    #----------------------------------------------------------------------     
    def __playTrackOne(self, offset):
        try:    
            mixer.music.play(loops=0, start=offset)
        except: 
            self.threadRunning          = False
            self.musicLoadSuccessfully  = False
            print("Failed to start music, aboard thread")
    
        
