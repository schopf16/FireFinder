# -*- coding: UTF-8-*-

import os
import time
import pygame
import threading

from pathlib import Path
from firefinder.util_logger import Logger


def set_volume(volume=0.5):
    """
    :param volume: Set the volume of the music playback.
                   The value argument is between 0.0 and
                   1.0. When new music is loaded the
                   volume is reset.
    """
    pygame.mixer.music.set_volume(volume)


class AlarmSound(object):
    def __init__(self, path, logger=None):
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\AlarmSound.log")
        self._thread = None
        self._running = False

        pygame.mixer.init(frequency=22050, size=16, channels=2, buffer=4096)
        set_volume(1.00)  # set volume to maximum and handle the volume manual at the TV

        self.sound_file_path = None
        self.sound_folder_path = path
        self.musicLoadSuccessfully = False

    def start(self, loops=0, offset=0.0, delay=0, pause=0):
        """
        This will play the loaded music stream. If the music is already playing
        it will be restarted.


        :param pause:  Define the pause between two plays
        :param delay:  Define the start delay of the first sound
        :param offset: Controls where in the music the song starts playing.
                       The starting position is dependent on the format of music
                       playing. MP3 and OGG use the position as time (in seconds).
                       MOD music it is the pattern order number. Passing a startpos
                       will raise a NotImplementedError if it cannot set the start
                       position.
        :param loops:  Controls the number of repeats a music will play.
                       play(5) will cause the music to played once, then repeated
                       five times, for a total of six. If the loops is -1 then
                       the music will repeat indefinitely.
        """

        # do not start thread as long as the one is still running
        if (self._thread is None or not self._thread.is_alive()) and self.sound_file_path:
            self._thread = threading.Thread(target=self.__sound_thread, args=(loops, offset, delay, pause), daemon=True)
            self._thread.start()  # start the thread which plays the given music
            self._running = True

    def stop(self):
        """
        Stops the music playback if it is currently playing.
        """

        self._running = False

        try:
            pygame.mixer.music.stop()
        except Exception as e:
            self.logger.error(f"Could not stop playing file '{self.sound_file_path}", exception=e.args)

    def load_music(self, file):
        """
        :param file: Load a file into the music class. If the file remain
                     the same, do not load again the path is put
                     automatically to the file
        """

        self.sound_file_path = ""
        full_file_path = os.path.join(self.sound_folder_path, file)
        path_obj = Path(full_file_path)
        if path_obj.is_file():
            try:
                pygame.mixer.music.load(path_obj.absolute())
                self.sound_file_path = file
                self.stop()
            except Exception as e:
                self.logger.error(f"Failed load music path: '{path_obj.absolute()}'", exception=e.args)
        else:
            self.logger.error(f"Could not find file '{path_obj.absolute()}' at given location, sorry I gave up")

        if self.sound_file_path:
            self.logger.info(f"successfully load sound file '{self.sound_file_path}'")

    def __sound_thread(self, loops=0, offset=0.0, delay=0, pause=0):
        # catch exceptions in this thread
        threading.excepthook = self.logger.thread_except_hook

        self.logger.info(f"Now playing sound file '{self.sound_file_path}'", loops=loops, offset=offset, delay=delay, pause=pause)

        # Check for delay before playing sound
        if delay != 0 and self._running:
            _delay = delay
            while _delay > 0:
                time.sleep(0.1)
                _delay -= 0.1
                if self._running is False:
                    break

        while loops != 0 and self._running:

            if not self._running:
                break

            self.__play_track_one(offset)

            while pygame.mixer.music.get_busy():
                continue

            if loops != -1:  # Check if loop is infinite
                loops -= 1  # no, so decrement variable by 1

            if pause != 0:
                time.sleep(pause)

        # Music played completely
        self._running = False

    def __play_track_one(self, offset):
        try:
            pygame.mixer.music.play(loops=0, start=offset)
        except Exception as e:
            self.logger.error(f"Error occurs during playing '{self.sound_file_path}'", exception=e.args)
            self._running = False
            self.sound_file_path = ""

    def is_running(self):
        return self._running


if __name__ == '__main__':

    THIS_FILE_PATH = os.path.dirname(__file__)
    sound = AlarmSound(path=os.path.join(THIS_FILE_PATH, 'sound'))

    # # load music
    # print("load file 01.mp3")
    # sound.load_music('01.mp3')
    # time.sleep(2)

    print("start song")
    sound.load_music('01.mp3')
    sound.start(loops=2, offset=0, delay=0, pause=0)
    time_start = time.time()
    while (time.time() - time_start <= 30) and sound.is_running():
        time.sleep(1)
    print("song played")

    sound.load_music('02.mp3')
    sound.start(loops=2, offset=0, delay=0, pause=0)
    time_start = time.time()
    while (time.time() - time_start <= 30) and sound.is_running():
        time.sleep(1)
    print("song played")

    sound.load_music('03.mp3')
    sound.start(loops=2, offset=0, delay=0, pause=0)
    time_start = time.time()
    while (time.time() - time_start <= 30) and sound.is_running():
        time.sleep(1)
    print("song played")

    sound.load_music('dummy.mp3')
    sound.start(loops=2, offset=0, delay=0, pause=0)
    time_start = time.time()
    while (time.time() - time_start <= 30) and sound.is_running():
        time.sleep(1)
    print("song played")

    time.sleep(20)
    print("Test end")
