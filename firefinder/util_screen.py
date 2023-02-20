# -*- coding: utf-8-*-

import os
import sys
import time
import queue
import random
import pygame
import threading

from pathlib2 import Path
from datetime import datetime
from firefinder.util_logger import Logger

pygame.init()
screen_info = pygame.display.Info()


# Colors
BLACK = (0, 0, 0)
GREY  = (128, 128, 128)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
WHITE = (255, 255, 255)

FPS = 30

def scale_image(image_obj, max_width=None, max_height=None, crop=False, keep_ratio=True):
    # Get the original image dimensions
    width, height = image_obj.get_size()

    # Determine the scaling factor for width and height
    width_scale = float(max_width) / width if max_width else 1.0
    height_scale = float(max_height) / height if max_height else 1.0

    # Determine the scaling factor to use based on the largest dimension
    if crop:
        # Crop the image if necessary to fit within the given dimensions
        scale_factor = max(width_scale, height_scale)
    else:
        # Scale the image down proportionally to fit within the given dimensions
        scale_factor = min(width_scale, height_scale)

    # Calculate the new image size after scaling
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # Scale the image using the new dimensions
    scaled_image = pygame.transform.smoothscale(image_obj, (new_width, new_height))

    if crop:
        # If cropping, create a new surface with the target dimensions and blit the scaled image onto it
        target_surface = pygame.Surface((max_width, max_height))
        target_surface.blit(scaled_image, ((max_width - new_width) // 2, (max_height - new_height) // 2))
        return target_surface
    else:
        # If scaling, return the scaled image directly
        return scaled_image


class GuiThread(threading.Thread):
    def __init__(self, full_screen, logger=None):
        threading.Thread.__init__(self)

        if logger is None:
            logger = Logger(verbose=True, file_path=".\\GuiHandler.log")

        self.logger = logger
        self.full_screen = full_screen
        self._running = False
        self._queue = queue.Queue()

        self._fps = FPS

    def set_screen(self, surface_obj):
        self._queue.put(surface_obj)

    def run(self):

        resolution = (screen_info.current_w, screen_info.current_h)
        if self.full_screen:
            window = pygame.display.set_mode(resolution, pygame.FULLSCREEN)
        else:
            window = pygame.display.set_mode(resolution)

        surface_obj = OffSurface(logger=self.logger)
        pygame.display.set_caption("FireFinder")
        clock = pygame.time.Clock()

        self._running = True
        while self._running:

            for event in pygame.event.get():
                # Did the user click the window close button?
                if event.type == pygame.QUIT:
                    self._running = False

                # Did the user press ESC-button?
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._running = False

            # Check queue for data
            try:
                surface_obj = self._queue.get_nowait()
                get_surface = getattr(surface_obj, "get_surface", None)
                assert callable(get_surface)
            except queue.Empty:
                pass

            # Fill the background with white
            window.fill((255, 255, 255))
            window.blit(surface_obj.get_surface(), (0, 0))
            pygame.display.flip()

            # Control the FPS
            clock.tick(self._fps)

    def stop(self):
        self._running = False
        pygame.quit()


class GuiHandler(object):
    def __init__(self, logger=None, **kwargs):
        if logger is None:
            logger = Logger(verbose=True, file_path=".\\GuiHandler.log")

        full_screen = kwargs.get("full_screen", True)
        company_path_logo = kwargs.get("company_path_logo")
        company_name = kwargs.get("company_name")

        self.full_screen = full_screen
        self.logger = logger
        self._thread = None

        self._off_surface_obj = OffSurface(logger=logger,
                                           show_time=True,
                                           show_second=True,
                                           show_date=True,
                                           show_weekday=True,
                                           path_logo=company_path_logo,
                                           company_name=company_name)

    def set_screen(self, surface_obj):
        self._thread.set_screen(surface_obj)

    def start(self):
        self._thread = GuiThread(full_screen=self.full_screen, logger=self.logger)
        self.set_screen(surface_obj=self._off_surface_obj)
        self._thread.start()

    def stop(self):
        self._thread.stop()
        self._thread.join()

    def is_running(self):
        return self._thread.is_alive()


class HeaderSurface(object):
    def __init__(self, height, logger=None, **kwargs):

        if logger is None:
            logger = Logger(verbose=True, file_path=".\\HeaderSurface.log")
        self.logger = logger
        screen_width = screen_info.current_w
        screen_height = height
        resolution = (screen_width, screen_height)
        self._surface = pygame.Surface(resolution)
        self._font = pygame.font.SysFont(name='Arial', size=screen_height-4, bold=True)

        self.bg_color = kwargs.get("bg_color", BLACK)
        self.fg_color = kwargs.get("fg_color", WHITE)

        self.show_time    = kwargs.get("show_time",    True)
        self.show_second  = kwargs.get("show_second",  True)
        self.show_date    = kwargs.get("show_date",    True)
        self.show_weekday = kwargs.get("show_weekday", True)
        self.weekday_list = ['Montag',      # Weekday 0
                             'Dienstag',    # Weekday 1
                             'Mittwoch',    # Weekday 2
                             'Donnerstag',  # Weekday 3
                             'Freitag',     # Weekday 4
                             'Samstag',     # Weekday 5
                             'Sonntag']     # Weekday 6

        # configs for miscellaneous
        self.show_logo    = kwargs.get("show_logo", True)
        self.path_logo    = kwargs.get("path_logo", "")
        self.company_name = kwargs.get("company_name", "")

        self.image = self._get_logo_surface()

    def _get_date_time_str(self):
        act_time = datetime.timetuple(datetime.now())
        year, month, day, h, m, s, wd, x, x = act_time

        time_string = "{:02d}:{:02d}".format(h, m)
        if self.show_second is True:
            time_string = "{}:{:02d}".format(time_string, s)

        date_string = "{:02d}.{:02d}.{:04d}".format(day, month, year)
        if self.show_weekday is True:
            date_string = "{}, {}".format(self.weekday_list[wd], date_string)

        time_date_string = ""
        if self.show_time and not self.show_date:
            time_date_string = time_string
        if self.show_date and not self.show_time:
            time_date_string = date_string
        if self.show_time and self.show_date:
            time_date_string = "{} // {}".format(time_string, date_string)

        return time_date_string

    def _get_logo_surface(self):
        image = None
        if os.path.isfile(self.path_logo):
            # Load image
            image = pygame.image.load(self.path_logo)

            # The image shall be 4 pixel smaller than the available space
            image = scale_image(image_obj=image, max_height=self._surface.get_height() - 4)

        return image

    def configure(self, **kw):

        if len(kw) == 0:  # return a dict of the current configuration
            cfg = {'show_second': self.show_second, 'show_time': self.show_time, 'show_date': self.show_date,
                   'show_weekday': self.show_weekday, 'path_logo': self.path_logo, 'show_logo': self.show_logo,
                   'company_name': self.company_name, 'bg_color': self.bg_color, 'fg_color': self.fg_color}
            return cfg

        else:  # do a configure
            for key, value in list(kw.items()):
                if key == 'show_second':
                    self.show_second = value
                    self.logger.info("Set 'show_second' to {}".format(value))
                elif key == 'show_time':
                    self.show_time = value
                    self.logger.info("Set 'show_time' to {}".format(value))
                elif key == 'show_date':
                    self.show_date = value
                    self.logger.info("Set 'show_date' to {}".format(value))
                elif key == 'show_weekday':
                    self.show_weekday = value
                    self.logger.info("Set 'show_weekday' to {}".format(value))
                elif key == 'bg_color':
                    self.bg_color = value
                    self.logger.info("Set 'bg_color' to {}".format(value))
                elif key == 'fg_color':
                    self.fg_color = value
                    self.logger.info("Set 'fg_color' to {}".format(value))
                elif key == 'path_logo':
                    self.path_logo = value
                    self.logger.info("Set 'path_logo' to {}".format(value))
                    self.image = self._get_logo_surface()
                elif key == 'show_logo':
                    self.show_logo = value
                    self.logger.info("Set 'show_logo' to {}".format(value))
                elif key == 'company_name':
                    self.company_name = value
                    self.logger.info("Set 'company_name' to {}".format(value))

    def get_surface(self):

        self._surface.fill(self.bg_color)

        # Render text for date and time
        time_date_string = self._get_date_time_str()
        text_date_time = self._font.render(time_date_string, True, self.fg_color, self.bg_color)

        # blit text on the right position of the header
        text_rect = text_date_time.get_rect()
        text_rect.right = self._surface.get_width() - 10
        text_rect.centery = self._surface.get_height() // 2
        self._surface.blit(text_date_time, text_rect)

        if self.show_logo and self.image is not None:
            # Blit the image on the left position of the header
            image_rect = self.image.get_rect()
            image_rect.left = 10
            image_rect.centery = self._surface.get_height() // 2
            self._surface.blit(self.image, image_rect)

        if self.company_name:
            image_width = 0
            if self.image is not None:
                image_rect = self.image.get_rect()
                image_width = image_rect.right + 10

            # blit text on the right position of the company logo
            text_company = self._font.render(self.company_name, True, self.fg_color, self.bg_color)
            text_rect = text_company.get_rect()
            text_rect.left = image_width + 10
            text_rect.centery = self._surface.get_height() // 2
            self._surface.blit(text_company, text_rect)

        return self._surface


class OffSurface(object):
    def __init__(self, logger=None, **kwargs):

        if logger is None:
            logger = Logger(verbose=True, file_path=".\\OffSurface.log")
        self.logger = logger
        self.path_logo = kwargs.get("path_logo", "")

        self.bg_color = kwargs.get("bg_color", BLACK)
        self.fg_color = kwargs.get("fg_color", WHITE)

        screen_width = screen_info.current_w
        screen_height = screen_info.current_h
        resolution = (screen_width, screen_height)
        self._surface = pygame.Surface(resolution)

        # Do not show logo in the header, it's already present in main surface. Use same value as
        kwargs.update({"show_logo": False,
                       "bg_color": self.bg_color,
                       "fg_color": self.fg_color,
                       })
        header_height = 30
        self._header_surface_obj = HeaderSurface(height=header_height, logger=logger, **kwargs)
        self._main_surface = pygame.Surface((screen_width, screen_height-header_height))
        self._set_logo()

    def _set_logo(self):
        surface_width = self._main_surface.get_width()
        surface_height = self._main_surface.get_height()
        max_image_width = surface_width - 50
        max_image_height = surface_height - 50

        self._main_surface.fill(self.bg_color)

        if os.path.isfile(self.path_logo):
            # Load image
            image = pygame.image.load(self.path_logo)
            image = scale_image(image_obj=image, max_width=max_image_width, max_height=max_image_height)

            # Center image in the middle of the surface
            x = (surface_width - image.get_width()) // 2
            y = (surface_height - image.get_height()) // 2
            self._main_surface.blit(image, (x, y))
        else:
            pygame.draw.line(self._main_surface, RED, (0, 0), (surface_width, surface_height), 5)
            pygame.draw.line(self._main_surface, RED, (surface_width, 0), (0, surface_height), 5)

    def get_surface(self):
        self._surface.fill(self.bg_color)

        header_surface = self._header_surface_obj.get_surface()
        self._surface.blit(header_surface, (0, 0))
        self._surface.blit(self._main_surface, (0, header_surface.get_height() + 1))
        return self._surface


class SlideshowSurface(object):
    def __init__(self, logger=None, **kwargs):
        if logger is None:
            logger = Logger(verbose=True, file_path=".\\SlideshowSurface.log")

        self.logger = logger

        # store path where the pictures for the slideshow are stored
        self.path_to_images      = kwargs.get("path_to_images", "")
        self.sort_alphabetically = kwargs.get("short_alphabetically", False)
        self.display_duration    = kwargs.get("seconds_between_images", 15)

        self.last_image_time     = None
        self.image_list          = []
        self.new_image           = None
        self.current_image       = None
        self.current_image_index = 0
        self.fade_alpha          = 0  # can be -1 ... 1 where -1 is the old image and 1 the new
        if self.path_to_images:
            self.load_images()

        # Store settings for header-bar
        self.show_header   = kwargs.get("show_header", True)
        self.path_logo     = kwargs.get("path_logo", "")
        self.company_name  = kwargs.get("company_name", "")
        self.header_height = 40
        self._header_surface_obj = HeaderSurface(height       = self.header_height,
                                                 logger       = logger,
                                                 show_time    = False,
                                                 bg_color     = GREY,
                                                 path_logo    = self.path_logo,
                                                 company_name = self.company_name)

        self._font = pygame.font.SysFont(name='Arial', size=50, bold=True)

        self.bg_color = BLACK
        self.fg_color = RED
        resolution = (screen_info.current_w, screen_info.current_h)
        self._surface = pygame.Surface(resolution)

    def load_images(self):
        images = []
        successful = True

        # Check if path to images is defined
        if self.path_to_images == '':
            self.logger.error("ERROR: Path to slideshow folder not set yet")
            successful = False

        # check if slideshow folder already exists and create it if necessary
        if not os.path.exists(self.path_to_images):
            os.makedirs(self.path_to_images)

        for filename in os.listdir(self.path_to_images):
            if filename.lower().endswith(('.jpg', '.jpeg', '.bmp', '.png', '.gif', '.eps', '.tif', '.tiff')):
                # path = os.path.join(self.path_to_images, filename)
                # image = pygame.image.load(path)
                images.append(filename)

        self.current_image_index = 0
        self.image_list = images
        self.sort_images()
        return successful

    def sort_images(self):
        if self.sort_alphabetically:
            print("Start sort")
            self.image_list = sorted(self.image_list)
            print("End sort")
        else:
            self.image_list = random.sample(self.image_list, len(self.image_list))

    def get_next_image_obj(self):
        if self.image_list:

            if self.current_image_index >= len(self.image_list):
                self.current_image_index = 0

            max_height = screen_info.current_h
            if self.show_header:
                max_height -= self.header_height

            path = os.path.join(self.path_to_images, self.image_list[self.current_image_index])
            image = pygame.image.load(path)
            image = scale_image(image_obj  = image,
                                max_height = max_height,
                                max_width  = screen_info.current_w)

            self.current_image_index += 1
        else:
            image = self._font.render("Keine Bilder zum Anzeigen :(", True, self.fg_color, self.bg_color)

        return image

    def get_surface(self):

        self._surface.fill(self.bg_color)

        # If this is the first call, the current image is empty
        if self.current_image is None:
            self.current_image = self.get_next_image_obj()
            self.last_image_time = time.time()
            self.fade_alpha = 1  # Completely faded

        # Check if picture shall be updated
        if self.fade_alpha >= 1 and time.time() - self.last_image_time >= self.display_duration:
            self.new_image = self.get_next_image_obj()
            self.fade_alpha = -1  # start new fade
            self.last_image_time = None

        # If fading is in progress, the alpha channel is less than 1
        if self.fade_alpha < 1:
            header_height = self.header_height if self.show_header else 0
            fade_surface = pygame.Surface((screen_info.current_w, screen_info.current_h-header_height))
            fade_surface.fill(BLACK)

            # The fade range is -1 ... 1 where -1 is the complete old image while 1 is the complete new image
            if self.fade_alpha < 0:
                # Fade out old picture
                fade_surface.set_alpha(255 - int(abs(self.fade_alpha) * 255))
                x = (screen_info.current_w - self.current_image.get_width()) // 2
                y = (screen_info.current_h - self.current_image.get_height()) // 2
                if self.show_header:
                    y += self.header_height
                self._surface.blit(self.current_image, (x, y))
                self._surface.blit(fade_surface, (x, y))
            else:
                # Fade in new picture
                fade_surface.set_alpha(255 - int(self.fade_alpha * 255))
                x = (screen_info.current_w - self.new_image.get_width()) // 2
                y = (screen_info.current_h - self.new_image.get_height()) // 2
                if self.show_header:
                    y += self.header_height
                self._surface.blit(self.new_image, (x, y))
                self._surface.blit(fade_surface, (x, y))

            # Increment fade step and check if fading is finished
            self.fade_alpha += 1/FPS
            if self.fade_alpha >= 1:
                self.last_image_time = time.time()
                self.current_image = self.new_image
                self.new_image = None
        else:
            # No fade, just show picture
            x = (screen_info.current_w - self.current_image.get_width()) // 2
            y = (screen_info.current_h - self.current_image.get_height()) // 2
            if self.show_header:
                y += self.header_height
            self._surface.blit(self.current_image, (x, y))

        # Update header
        if self.show_header:
            self._surface.blit(self._header_surface_obj.get_surface(), (0, 0))

        return self._surface

    def configure(self, **kw):

        if len(kw) == 0:  # return a dict of the current configuration
            cfg = {'seconds_between_images': self.display_duration, 'sort_alphabetically': self.sort_alphabetically,
                   'path_to_images': self.path_to_images, 'path_logo': self.path_logo,
                   'company_name': self.company_name, 'show_header': self.show_header}
            return cfg

        else:  # do a configure
            for key, value in list(kw.items()):
                if key == 'seconds_between_images':
                    self.display_duration = value
                    self.logger.info("Set 'seconds_between_images' to {}".format(value))
                elif key == 'sort_alphabetically':
                    self.sort_alphabetically = value
                    self.logger.info("Set 'sort_alphabetically' to {}".format(value))
                    self.sort_images()
                elif key == 'path_to_images':
                    self.path_to_images = value
                    self.logger.info("Set 'path_to_images' to {}".format(value))
                    self.load_images()
                elif key == 'path_logo':
                    self.path_logo = value
                    self._header_surface_obj.configure(path_logo=self.path_logo)
                elif key == 'company_name':
                    self.company_name = value
                    self._header_surface_obj.configure(company_name=self.company_name)
                elif key == 'show_header':
                    self.show_header = value
                    self.logger.info("Set 'show_header' to {}".format(value))


def test_screen_top(screen_obj):
    def update_screen():
        screen_obj.blit(header_obj.get_surface(), (0, 0))
        pygame.display.flip()

    header_obj = HeaderSurface(height=30)

    print("Start Test")

    time.sleep(1)

    header_obj.configure(company_name="Feuerwehr Ittigen")
    update_screen()
    time.sleep(1)

    header_obj.configure(show_logo=False)
    update_screen()
    time.sleep(1)

    header_obj.configure(show_time=False)
    update_screen()
    time.sleep(1)

    header_obj.configure(show_date=False)
    update_screen()
    time.sleep(1)

    header_obj.configure(show_logo=True)
    update_screen()
    time.sleep(1)

    header_obj.configure(path_logo="D:\\Firefinder\\logo.png")
    update_screen()
    time.sleep(1)

    header_obj.configure(company_name="")
    update_screen()
    time.sleep(1)

    header_obj.configure(fg_color=(0, 0, 255))
    update_screen()
    time.sleep(1)

    header_obj.configure(show_date=True)
    update_screen()
    time.sleep(1)

    header_obj.configure(company_name="Feuerwehr Ittigen")
    update_screen()
    time.sleep(1)

    header_obj.configure(show_weekday=False)
    update_screen()
    time.sleep(1)

    header_obj.configure(bg_color=(0, 255, 0))
    update_screen()
    time.sleep(1)

    header_obj.configure(show_time=True)
    update_screen()
    time.sleep(1)

    header_obj.configure(bg_color=(128, 128, 128))
    update_screen()
    time.sleep(1)

    header_obj.configure(fg_color=(255, 0, 0))
    update_screen()
    time.sleep(1)

    header_obj.configure(show_weekday=True)
    update_screen()
    time.sleep(3)

    print("Test ende")


def test_slideshow(screen_obj):
    def update_screen():
        screen_obj.blit(slideshow_obj.get_surface(), (0, 0))
        pygame.display.flip()

    clock = pygame.time.Clock()
    slideshow_obj = SlideshowSurface()

    print("Start Test")

    time.sleep(1)

    slideshow_obj.configure(path_to_images="D:\\Firefinder\\Slideshow")
    update_screen()
    time.sleep(1)

    slideshow_obj.configure(company_name="Feuerwehr Ittigen")
    update_screen()
    time.sleep(1)

    slideshow_obj.configure(path_logo="D:\\Firefinder\\logo.png")
    update_screen()
    time.sleep(1)

    slideshow_obj.configure(show_header=False)
    update_screen()
    time.sleep(1)

    slideshow_obj.configure(seconds_between_images=4)
    update_screen()
    time.sleep(1)

    slideshow_obj.configure(sort_alphabetically=True)
    update_screen()
    time.sleep(1)

    print("Test ende")


if __name__ == "__main__":
    screen = pygame.display.set_mode((screen_info.current_w, screen_info.current_h))
    # screen = pygame.display.set_mode((1000, 800))
    # off_obj = OffSurface(path_logo="D:\\Firefinder\\logo.png")
    # slideshow_obj = SlideshowSurface(path_to_images="D:\\Firefinder\\Slideshow")
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

        screen.fill((255, 255, 255))
        # test_screen_top(screen_obj=screen)
        test_slideshow(screen_obj=screen)
        pygame.quit()
        break

        # screen.blit(off_obj.get_surface(), (0, 0))
        # screen.blit(slideshow_obj.get_surface(), (0, 0))
        # pygame.display.flip()
        # clock.tick(FPS)

