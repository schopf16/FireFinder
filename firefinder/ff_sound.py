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

from pygame import mixer
import os
import threading
import time


def set_volume(volume=0.5):
    """
    :param volume: Set the volume of the music playback.
                   The value argument is between 0.0 and
                   1.0. When new music is loaded the
                   volume is reset.
    """
    mixer.music.set_volume(volume)


class AlarmSound(object):
    def __init__(self, path):
        self.st = threading.Thread(target=self.__sound_thread)
        self.startOffset = 0  # starting position
        self.loops = 0  # number of repeats
        self.pauseBetweenTrack = 0  # pause between tracks in seconds
        self.startDelay = 0  # delay in seconds
        mixer.init(frequency=22050, size=16, channels=2, buffer=4096)
        set_volume(1.00)  # set volume to maximum and handle the volume manual at the TV

        self.actLoadedTitle = 'none'
        self.pathToSoundfolder = path
        self.threadRunning = False
        self.musicLoadSuccessfully = False

    # ----------------------------------------------------------------------
    def start(self, loops=0, start=0.0, delay=0, pause=0):
        """
        This will play the loaded music stream. If the music is already playing
        it will be restarted.


        :param pause: Define the pause between two plays
        :param delay: Define the start delay of the first sound
        :param start: Controls where in the music the song starts playing.
                      The starting position is dependent on the format of music
                      playing. MP3 and OGG use the position as time (in seconds).
                      MOD music it is the pattern order number. Passing a startpos
                      will raise a NotImplementedError if it cannot set the start
                      position.
        :param loops: Controls the number of repeats a music will play.
                      play(5) will cause the music to played once, then repeated
                      five times, for a total of six. If the loops is -1 then
                      the music will repeat indefinitely.
        """

        # do not start thread as long as the one is still runing
        if not self.threadRunning:

            # start thread only if a music is loaded successfully
            if self.musicLoadSuccessfully:
                self.threadRunning = True

                self.startOffset = start  # starting position
                self.loops = loops  # number of repeats
                self.pauseBetweenTrack = pause  # pause between tracks in seconds
                self.startDelay = delay  # delay in seconds

                self.st.start()  # start the thread which plays the given music

    # ----------------------------------------------------------------------
    def stop(self):
        """
        Stops the music playback if it is currently playing.
        """

        self.threadRunning = False

        try:
            mixer.music.stop()
        except:
            print("Failed to stop music")

    # ----------------------------------------------------------------------
    def load_music(self, file):
        """
        :param file: Load a file into the music class. If the file remain
                     the same, do not load again the path is put
                     automatically to the file
        """
        if self.actLoadedTitle != file:
            path = os.path.join(self.pathToSoundfolder, file)
            if os.path.isfile(path):
                try:
                    mixer.music.load(path)
                    self.musicLoadSuccessfully = True
                    self.actLoadedTitle = file
                    self.stop()
                except:
                    self.musicLoadSuccessfully = False
                    print("Failed load music path: \"%s\"" % path)
            else:
                print("Could not locate file \"%s\"" % path)

    # ----------------------------------------------------------------------
    def __sound_thread(self):

        if self.startDelay != 0:
            time.sleep(self.startDelay)

        while self.loops != 0:

            if not self.threadRunning:
                return

            self.__play_track_one(self.startOffset)

            while mixer.music.get_busy():
                continue

            if self.loops != -1:  # Check if loop is infinit
                self.loops -= 1  # no, so decrement varaible by 1

            if self.pauseBetweenTrack != 0:
                time.sleep(self.pauseBetweenTrack)

        # Music played completely
        self.threadRunning = False

    # ----------------------------------------------------------------------
    def __play_track_one(self, offset):
        try:
            mixer.music.play(loops=0, start=offset)
        except:
            self.threadRunning = False
            self.musicLoadSuccessfully = False
            print("Failed to start music, aboard thread")

########################################################################
if __name__ == '__main__':

    try:
        wdr = os.path.dirname(__file__)
    except:
        wdr = os.getcwd()

    sound = SoundGenerator(path=os.path.join(wdr, 'sound'))

    # load music
    print("load file 01.mp3")
    sound.load_music('01.mp3')
    time.sleep(2)

    print("start song")
    sound.start(loops=5, start=0, delay=0, pause=0)

    time.sleep(20)
    print("Test end")
