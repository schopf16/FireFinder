# -*- coding: utf-8-*-

import os
import re
import math
import time
import queue
import random
import pygame
import pathlib
import threading

from enum import Enum
from typing import Union
from datetime import datetime
from firefinder.util_power import GraphicOutputDriver, OutputState
from firefinder.util_logger import Logger
from firefinder.util_sound import AlarmSound

pygame.init()
pygame.display.set_caption("FireFinder")

# Colors
BLACK = (0, 0, 0)
GREY  = (128, 128, 128)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
WHITE = (255, 255, 255)

FPS = 30

THIS_FILE_PATH = os.path.dirname(__file__)
DEFAULT_FONT = os.path.join(THIS_FILE_PATH, "font", "Frutiger.ttf")
DEFAULT_FONT_BOLD = os.path.join(THIS_FILE_PATH, "font", "Frutiger_bold.ttf")
DEFAULT_PIC_DIR = os.path.join(THIS_FILE_PATH, "pic")
DEFAULT_NO_PIC = os.path.join(THIS_FILE_PATH, "pic", "bg", "no_image.png")
DEFAULT_SOUND_DIR = os.path.join(THIS_FILE_PATH, "sound")

CASE_LEVEL_DICT = {
    "AA": "Automatischer Alarm Feuer",
    "A1": "Brand klein",
    "A2": "Brand mittel",
    "A3": "Brand gross",
    "B1": "Elementar klein",
    "B2": "Elementar mittel",
    "B3": "Elementar gross",
    "C1": "Technische Hilfeleistung klein",
    "C2": "Technische Hilfeleistung mittel",
    "C3": "Technische Hilfeleistung gross",
    "D1": "Öl, Benzin, Gas klein",
    "D2": "Öl, Benzin, Gas mittel",
    "D3": "Öl, Benzin, Gas gross",
    "E1": "ABC klein",
    "E2": "ABC mittel",
    "E3": "ABC gross",
    "F1": "Personenrettung bei Unfall klein",
    "F2": "Personenrettung bei Unfall mittel",
    "F3": "Personenrettung bei Unfall gross",
    "G1": "Tierrettung klein",
    "G2": "Tierrettung mittel",
}
CASE_COLOR_DICT = {
    "AA": pygame.Color((255, 154, 153)),
    "A1": pygame.Color((255, 154, 153)),
    "A2": pygame.Color((255, 154, 153)),
    "A3": pygame.Color((255, 154, 153)),
    "B1": pygame.Color((175, 214, 255)),  # Lightblue
    "B2": pygame.Color((175, 214, 255)),
    "B3": pygame.Color((175, 214, 255)),
    "C1": pygame.Color((179, 255, 168)),
    "C2": pygame.Color((179, 255, 168)),
    "C3": pygame.Color((179, 255, 168)),
    "D1": pygame.Color((255, 255, 143)),
    "D2": pygame.Color((255, 255, 143)),
    "D3": pygame.Color((255, 255, 143)),
    "E1": pygame.Color((255, 184, 255)),
    "E2": pygame.Color((255, 184, 255)),
    "E3": pygame.Color((255, 184, 255)),
    "F1": pygame.Color((173, 255, 255)),
    "F2": pygame.Color((173, 255, 255)),
    "F3": pygame.Color((173, 255, 255)),
    "G1": pygame.Color('grey'),
    "G2": pygame.Color('grey'),
}


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
    try:
        scaled_image = pygame.transform.smoothscale(image_obj, (new_width, new_height))
    except ValueError:
        scaled_image = pygame.transform.scale(image_obj, (new_width, new_height))

    if crop:
        # If cropping, create a new surface with the target dimensions and blit the scaled image onto it
        target_surface = pygame.Surface((max_width, max_height))
        target_surface.blit(scaled_image, ((max_width - new_width) // 2, (max_height - new_height) // 2))
        return target_surface
    else:
        # If scaling, return the scaled image directly
        return scaled_image


def get_font_obj(font_name, font_size):
    # Check if font name is installed or is it a font-file
    if ".ttf" in font_name:
        font = pygame.font.Font(font_name, int(font_size))
    else:
        font = pygame.font.SysFont(font_name, int(font_size))
    return font


def get_screen_obj_from_string(screen_name: str):
    screen_name = screen_name.lower()
    if screen_name == "event":
        screen_obj = Screen.event
    elif screen_name == "clock":
        screen_obj = Screen.clock
    elif screen_name == "splashscreen":
        screen_obj = Screen.splash
    elif screen_name == "off":
        screen_obj = Screen.off
    elif screen_name == "slideshow":
        screen_obj = Screen.slideshow
    else:
        screen_obj = None
    return screen_obj


class EventInfo(object):
    """

    """
    def __init__(self, event_msg):
        self.message        = event_msg
        self.case_and_level = ""
        self.event_keyword  = ""
        self.city           = ""
        self.street_name    = ""
        self.street_number  = ""
        self.details        = ""  # May empty on an automatic alarm

        # Only available if self.case_and_level is 'AA'
        self.alarmnet_number = ""
        self.object_info     = ""

        self.parsed = self.parse()

    def parse(self):
        """
        example message:

        AA, AA Sprinkler, Ittigen;Ey,19, Geschäftshaus Bermuda Ittigen, 223 326 (Geschäftshaus Bermuda Ittigen)

        D1, Öl, Benzin, Ittigen;Allmitstrasse, Flüssigkeiten aufnehmen nach Pw-Pw, 1 Fahrzeug auf der Seite, POL vor
          Ort, Ittigen Schönbühl Kreuzung

        AA, AA Feuer, Ittigen;Mühlestrasse,2, Verwaltungszentrum UVEK Ittigen, 225 276 (Verwaltungszentrum Mühlestrasse
          Ittige

        Alarmmessage:
            [Fall + Stufe] [Einsatzstichwort] [Ort, Adresse] [Zusatz zu Ort] [Betrifft]
                optional für AA [Objekt-Info, Alarmnetnummer]
        :return:
        """

        parsed = False
        if ';' in self.message:

            # If the message is parsable, it contain a ';'
            event_list = self.message.split(';')
            first = event_list[0]
            second = " ".join(event_list[1:])  # In case there is a second ';' somewhere in the description

            # The _first_ part shall contain the case, level, event-keyword and city
            first_list = [s.strip() for s in first.split(',')]
            self.case_and_level = first_list[0]
            self.event_keyword = ",".join(first_list[1:-1])
            self.city = first_list[-1]

            # The _second_ part shall contain street_name, street_number (optional)
            second_list = [s.strip() for s in second.split(',')]
            self.street_name = second_list[0]
            del second_list[0]  # The street name is assigned and can be removed

            street_nbr = second_list[0]
            if str(street_nbr).isnumeric():
                self.street_number = street_nbr
                del second_list[0]  # The street number is assigned and can be removed

            if self.case_and_level == "AA":
                # This is an automatic alarm. Expect [object-info, alarmnetnbr] in the message
                alarmnet_index = 0
                alarmnet_found = False

                # Search for the alarmnet number in the list
                for alarmnet_index in range(0, len(second_list)):
                    stripped_string = str(second_list[alarmnet_index])
                    if re.match(r"(\d{3}\s\d{3})", stripped_string, re.UNICODE):
                        self.alarmnet_number = stripped_string
                        alarmnet_found = True
                        break

                if alarmnet_found:
                    # If a alarmnet number was found, the element in front shall contain the object-info
                    self.object_info = " ".join(second_list[:alarmnet_index])
                    # Check if additional information's are sent
                    if alarmnet_index < len(second_list):
                        self.details = " ".join(second_list[alarmnet_index+1:])
                else:
                    # If no alarmnet number is found, take everything as details
                    self.details = " ".join(second_list)

            else:
                # No automatic alarm. Take everything after the address as additional info (street-nbr is already cutted)
                self.details = ",".join(second_list[1:])

            parsed = True

        return parsed


# ---- SURFACES ---------------------------
class HeaderSurface(pygame.Surface):
    def __init__(self, size, logger=None, color_bg=BLACK, color_fg=WHITE, show_time=True, show_second=True,
                 show_date=True, show_weekday=True, show_logo=True, company_path_logo="", company_name=""):
        super(HeaderSurface, self).__init__(size)
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\HeaderSurface.log")

        self._font = get_font_obj(font_name=DEFAULT_FONT_BOLD, font_size=self.get_height()-4)

        self.bg_color = color_bg
        self.fg_color = color_fg

        self.show_time    = show_time
        self.show_second  = show_second
        self.show_date    = show_date
        self.show_weekday = show_weekday
        self.weekday_list = ['Montag',      # Weekday 0
                             'Dienstag',    # Weekday 1
                             'Mittwoch',    # Weekday 2
                             'Donnerstag',  # Weekday 3
                             'Freitag',     # Weekday 4
                             'Samstag',     # Weekday 5
                             'Sonntag']     # Weekday 6

        # configs for miscellaneous
        self.show_logo         = show_logo
        self.company_path_logo = company_path_logo
        self.company_name      = company_name

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
        if os.path.isfile(self.company_path_logo):
            # Load image
            image = pygame.image.load(self.company_path_logo)

            # The image shall be 4 pixel smaller than the available space
            image = scale_image(image_obj=image, max_height=self.get_height() - 4)

        return image

    def configure(self, **kw):
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
            elif key == 'company_path_logo':
                self.company_path_logo = value
                self.logger.info("Set 'company_path_logo' to {}".format(value))
                self.image = self._get_logo_surface()
            elif key == 'show_logo':
                self.show_logo = value
                self.logger.info("Set 'show_logo' to {}".format(value))
            elif key == 'company_name':
                self.company_name = value
                self.logger.info("Set 'company_name' to {}".format(value))

    def update(self):

        self.fill(self.bg_color)

        # Render text for date and time
        time_date_string = self._get_date_time_str()
        text_date_time = self._font.render(time_date_string, True, self.fg_color, self.bg_color)

        # blit text on the right position of the header
        text_rect = text_date_time.get_rect()
        text_rect.right = self.get_width() - 10
        text_rect.centery = self.get_height() // 2
        self.blit(text_date_time, text_rect)

        if self.show_logo and self.image is not None:
            # Blit the image on the left position of the header
            image_rect = self.image.get_rect()
            image_rect.left = 10
            image_rect.centery = self.get_height() // 2
            self.blit(self.image, image_rect)

        if self.company_name:
            image_width = 0
            if self.image is not None:
                image_rect = self.image.get_rect()
                image_width = image_rect.right + 10

            # blit text on the right position of the company logo
            text_company = self._font.render(self.company_name, True, self.fg_color, self.bg_color)
            text_rect = text_company.get_rect()
            text_rect.left = image_width + 10
            text_rect.centery = self.get_height() // 2
            self.blit(text_company, text_rect)


class AnalogClockSurface(pygame.Surface):
    def __init__(self, size, logger=None, **kwargs):
        super(AnalogClockSurface, self).__init__(size)
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\AnalogClockSurface.log")

        # Size of the analog clock
        self.size = size
        self.center = (size[0] // 2, size[1] // 2)
        self.radius = int(min(size) * 0.45)  # If the size is not equal, take smaller width / height as reference

        # Coloring clock
        self.color_bg          = kwargs.get("color_bg", BLACK)
        self.color_boarder     = WHITE
        self.color_second_hand = RED
        self.color_minute_hand = WHITE
        self.color_hour_hand   = WHITE
        self.color_face        = RED

        # Define length of the hands, depend on the size if the overall clock
        self.second_hand_length = self.radius * 1
        self.minute_hand_length = self.radius * 0.85
        self.hour_hand_length   = self.radius * 0.7
        self.second_hand_width  = self.radius * 0.02
        self.minute_hand_width  = self.radius * 0.03
        self.hour_hand_width    = self.radius * 0.04
        self.circle_size        = self.radius * 0.04
        self.clock_boarder      = 5

        # Define which hands shall be shown
        self.show_second_hand = kwargs.get("show_second_hand", True)
        self.show_minute_hand = kwargs.get("show_minute_hand", True)
        self.show_hour_hand   = kwargs.get("show_hour_hand", True)

    def draw_clock_face(self):
        for i in range(12):
            angle = 2 * math.pi * i / 12 - math.pi / 2
            x = self.center[0] + self.radius * math.cos(angle)
            y = self.center[1] + self.radius * math.sin(angle)
            pygame.draw.circle(self, self.color_face, (int(x), int(y)), self.circle_size, 0)

        # Draw center point where all hands come together
        pygame.draw.circle(self, self.color_face, self.center, self.circle_size, 0)

        # Show a circle clock boarder if size greater than 0
        if self.clock_boarder > 0:
            pygame.draw.circle(self, self.color_boarder, self.center, self.radius + self.circle_size*2, self.clock_boarder)

    def draw_hour_hand(self, current_time):
        width = int(self.hour_hand_width)
        hour, minute = current_time.hour % 12, current_time.minute

        angle = 2 * math.pi * (hour / 12 + minute / (60 * 12)) - math.pi / 2
        x = self.center[0] + self.hour_hand_length * math.cos(angle)
        y = self.center[1] + self.hour_hand_length * math.sin(angle)
        pygame.draw.line(self, self.color_hour_hand, self.center, (x, y), width)

    def draw_minute_hand(self, current_time):
        width = int(self.minute_hand_width)
        angle = 2 * math.pi * (current_time.minute / 60 + current_time.second / (60 * 60)) - math.pi / 2

        x = self.center[0] + self.minute_hand_length * math.cos(angle)
        y = self.center[1] + self.minute_hand_length * math.sin(angle)
        pygame.draw.line(self, self.color_minute_hand, self.center, (x, y), width)

    def draw_second_hand(self, ticks):
        width = int(self.second_hand_width)
        seconds = ticks / 1000 % 60
        angle = math.radians((seconds / 60) * 360 - 90)

        x = self.center[0] + self.second_hand_length * math.cos(angle)
        y = self.center[1] + self.second_hand_length * math.sin(angle)
        pygame.draw.line(self, self.color_second_hand, self.center, (x, y), width)

        pygame.draw.circle(self, self.color_second_hand, (x, y), self.circle_size/2, 0)

    def update(self):
        # Clear the surface
        self.fill(self.color_bg)

        # Get current time and ticks
        current_time = datetime.now()
        ticks = pygame.time.get_ticks()

        if self.show_hour_hand:
            self.draw_hour_hand(current_time=current_time)

        if self.show_minute_hand:
            self.draw_minute_hand(current_time=current_time)

        if self.show_second_hand:
            self.draw_second_hand(ticks=ticks)

        self.draw_clock_face()

    def configure(self, **kw):

        if len(kw) == 0:  # return a dict of the current configuration
            cfg = {'show_second_hand': self.show_second_hand, 'show_minute_hand': self.show_minute_hand,
                   'show_hour_hand': self.show_hour_hand}
            return cfg

        else:  # do a configure
            for key, value in list(kw.items()):
                if key == 'show_second_hand':
                    self.show_second_hand = value
                    self.logger.info("Set 'show_second_hand' to {}".format(value))
                elif key == 'show_minute_hand':
                    self.show_minute_hand = value
                    self.logger.info("Set 'show_minute_hand' to {}".format(value))
                elif key == 'show_hour_hand':
                    self.show_hour_hand = value
                    self.logger.info("Set 'show_hour_hand' to {}".format(value))


class DigitalClockSurface(pygame.Surface):
    def __init__(self, size, logger=None, **kwargs):
        super(DigitalClockSurface, self).__init__(size)
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\DigitalClockSurface.log")

        # Size of the analog clock
        self.size = size

        # Coloring clock
        self.color_bg = kwargs.get("color_bg", BLACK)
        self.color_fg = kwargs.get("color_fg", WHITE)

        # Define which hands shall be shown
        self.show_time   = kwargs.get("show_time", False)
        self.show_date   = kwargs.get("show_date", True)
        self.show_second = kwargs.get("show_second", False)  # show_time must be True

        font_size = int(self.get_height() * 0.6)
        self._font = get_font_obj(font_name=DEFAULT_FONT_BOLD, font_size=font_size)
        self.weekday_string = ['Montag',      # Weekday 0
                               'Dienstag',    # Weekday 1
                               'Mittwoch',    # Weekday 2
                               'Donnerstag',  # Weekday 3
                               'Freitag',     # Weekday 4
                               'Samstag',     # Weekday 5
                               'Sonntag']     # Weekday 6

    def update(self):
        self.fill(self.color_bg)

        current_time = datetime.now()
        time_str = "{:02d}:{:02d}".format(current_time.hour, current_time.minute)
        if self.show_second:
            time_str = "{}:{:02d}".format(time_str, current_time.second)

        date_str = "{:02d}.{:02d}.{:04d}".format(current_time.day, current_time.month, current_time.year)
        if not self.show_time:
            date_str = "{}, {}".format(self.weekday_string[current_time.weekday()], date_str)

        time_txt = self._font.render(time_str, True, self.color_fg, self.color_bg)
        date_txt = self._font.render(date_str, True, self.color_fg, self.color_bg)
        if self.show_time and self.show_date:
            text_rect = time_txt.get_rect()
            text_rect.left    = 10
            text_rect.centery = self.get_height() // 2
            self.blit(time_txt, text_rect)

            text_rect = date_txt.get_rect()
            text_rect.right   = self.get_width() - 10
            text_rect.centery = self.get_height() // 2
            self.blit(date_txt, text_rect)

        elif self.show_time:
            text_rect = time_txt.get_rect()
            text_rect.centerx = self.get_width() // 2
            text_rect.centery = self.get_height() // 2
            self.blit(time_txt, text_rect)

        elif self.show_date:
            text_rect = date_txt.get_rect()
            text_rect.centerx = self.get_width() // 2
            text_rect.centery = self.get_height() // 2
            self.blit(date_txt, text_rect)

    def configure(self, **kw):

        if len(kw) == 0:  # return a dict of the current configuration
            cfg = {'show_time': self.show_time, 'show_date': self.show_date,
                   'show_second': self.show_second}
            return cfg

        else:  # do a configure
            for key, value in list(kw.items()):
                if key == 'show_time':
                    self.show_time = value
                    self.logger.info("Set 'show_time' to {}".format(value))
                elif key == 'show_date':
                    self.show_date = value
                    self.logger.info("Set 'show_date' to {}".format(value))
                elif key == 'show_second':
                    self.show_second = value
                    self.logger.info("Set 'show_second' to {}".format(value))


class ScrollingTextX(object):
    def __init__(self, text, font_size, font_color, font=None):
        super(ScrollingTextX, self).__init__()

        self.font_color = font_color
        self._text = text  # Use update_text to change text during runtime

        self.scroll_speed_base = 9
        self.scroll_speed = self.scroll_speed_base

        self.image = None
        self.rect = None
        self.font = None
        self.font_size = font_size

        # Use update_font to change font during runtime
        self._fontname = DEFAULT_FONT_BOLD if font is None else font
        self.update_font(self._fontname, self.font_size)

    def render(self):
        self.image = self.font.render(self._text, True, self.font_color)
        self.rect = self.image.get_rect()
        self.rect.left = 0

    def update_text(self, text):
        if self._text != text:
            self._text = text
            self.render()

    def update_font(self, fontname, size):
        self._fontname = fontname
        self.font_size = size

        self.font = get_font_obj(font_name=fontname, font_size=size)
        self.render()

    def update_color(self, color):
        self.font_color = color
        self.render()

    def get_rect(self):
        return self.image.get_rect()

    def draw(self, surface: pygame.Surface, x, y):

        rect = self.rect.move(x, y)
        surface.blit(self.image, rect)

        # Check if the text fit to the screen. If not shift slightly to left for next drawing
        if self.rect.width > surface.get_width():
            self.rect.move_ip(-self.scroll_speed, 0)

            # Increase speed if right text side is in the middle and reduse speed if left side reaches again the middle
            if self.rect.right <= surface.get_width() * 0.5:
                self.scroll_speed = self.scroll_speed_base * 8
            elif self.rect.left <= surface.get_width() * 0.5:
                self.scroll_speed = self.scroll_speed_base
            if self.rect.right <= 0:
                self.rect.left = surface.get_width()


class ScrollingTextY(object):
    def __init__(self, text, font_size, font_color, screen_size, font=None):
        super(ScrollingTextY, self).__init__()

        self.font_color = font_color
        self._text = text  # Use update_text to change text

        self.screen_size = screen_size
        self.max_width = screen_size[0]
        self.max_height = screen_size[1]
        self.overall_height = None  # will be calculated by the render method

        self.scroll_speed_base = 2
        self.scroll_speed = self.scroll_speed_base

        self.image_list = []
        self.rect_list = []
        self.font = None
        self.font_size = font_size

        # Use update_font to change the font name
        self._fontname = DEFAULT_FONT_BOLD if font is None else font
        self.update_font(self._fontname, self.font_size)

    def render(self):
        font_height = self.font.get_linesize()

        # Split text into words and combine them to lines where each line shall not width than the surface
        line = ""
        lines = []
        words = self._text.split()
        for word in words:
            if self.font.size(line + word)[0] > self.max_width:
                lines.append(line)
                line = ""
            line += word + " "
        lines.append(line)

        # Create a text surface for every line
        self.image_list = []
        self.rect_list = []
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.font_color)
            text_rect = text_surface.get_rect()
            text_rect.topleft = (0, i * font_height)
            self.image_list.append(text_surface)
            self.rect_list.append(text_rect)

        self.overall_height = font_height * len(lines)

    def _restart_rect(self):
        font_height = self.font.get_linesize()

        # Re-arrange images to start from the bottom
        for i, rect in enumerate(self.rect_list):
            rect.topleft = (0, i * font_height + self.max_height)
            self.rect_list[i] = rect

    def draw(self, surface: pygame.Surface, x, y):

        # Only scroll if text is not fitting into surface, otherwise show text middle centered
        if self.overall_height > self.max_height:
            for i, (image, rect) in enumerate(zip(self.image_list, self.rect_list)):
                current_rect = rect.move(x, y)
                surface.blit(image, current_rect)

                # Change Y-axis for next drawing. This simulates a moving text upwards
                rect.move_ip(0, -self.scroll_speed)
                self.rect_list[i] = rect

            # Check if last line reached the middle of the screen
            first_rect = self.rect_list[0]
            last_rect = self.rect_list[-1]
            if last_rect.bottom <= (self.max_height // 2) + y:
                self.scroll_speed = self.scroll_speed_base * 8
            elif first_rect.top <= (self.max_height // 2) + y:
                self.scroll_speed = self.scroll_speed_base

            if last_rect.bottom <= y:
                self._restart_rect()

        else:
            upper_space = (self.max_height - self.overall_height) // 2
            for i, (image, rect) in enumerate(zip(self.image_list, self.rect_list)):
                rect.move_ip(x, y + upper_space)
                surface.blit(image, rect)

    def update_font(self, fontname, size):
        self._fontname = fontname
        self.font_size = size

        self.font = get_font_obj(font_name=fontname, font_size=size)
        self.render()

    def update_text(self, text):
        self._text = text
        self.render()


class ProgressBarSurface(pygame.Surface):
    def __init__(self, size, duration_sec, color_bg=GREY, font=None):
        super(ProgressBarSurface, self).__init__(size)

        # Store size and color
        self.size = size
        self.width = size[0]
        self.height = size[1]
        self.color_bg = color_bg
        self.color_text = WHITE
        self.borderwidth = 2

        # Create instance for scrolling text (if progressbar is smaller than text to display)
        self._text_surface = ScrollingTextX("", self.height * 0.9, self.color_text, font)

        # Store timing variables for doing progress
        self._duration_sec = duration_sec
        self.max_value = 100
        self._start_time = 0

        self.color_scheme = [(0, 'red'),
                             (90, 'orange'),
                             (100, 'green')
                             ]
        self.text_scheme = [(0, "Warte auf Atemschutz-Geräteträger"),
                            (90, "Bereitmachen zum Ausrücken"),
                            (100, "Losfahren, auch bei zuwenig Atemschutz-Geräteträger")
                            ]

    def update(self):
        if self._start_time == 0:
            self.start_timer(self._duration_sec)

        time_elapsed_ms = pygame.time.get_ticks() - self._start_time
        time_duration_ms = self._duration_sec * 1000
        value = min(time_elapsed_ms / time_duration_ms * 100, self.max_value)

        progress = int((value / self.max_value) * self.width)

        # Select foreground color and text depend on the current progres
        index_color = 0
        index_text = 0
        for i in range(len(self.color_scheme)):
            if int(value) >= self.color_scheme[i][0]:
                index_color = i
        for i in range(len(self.text_scheme)):
            if int(value) >= self.text_scheme[i][0]:
                index_text = i

        # Draw background
        bg_rect = pygame.Rect(0, 0, self.width, self.height)
        pygame.draw.rect(self, self.color_bg, bg_rect)

        # Draw foreground
        fg_rect = pygame.Rect(0, 0, progress, self.height)
        pygame.draw.rect(self, self.color_scheme[index_color][1], fg_rect)

        # Draw text
        self._text_surface.update_text(self.text_scheme[index_text][1])
        text_rect = self._text_surface.get_rect()
        # If text is smaller than progress bar, place in the center
        x_axis = max((self.width - text_rect.width) // 2, 0)
        y_axis = max((self.height - text_rect.height) // 2, 0)
        self._text_surface.draw(surface=self, x=x_axis, y=y_axis)

        if self.borderwidth:
            pygame.draw.rect(self, BLACK, (0, 0, self.width, self.height), self.borderwidth)

    def start_timer(self, duration):
        self._duration_sec = duration
        self._start_time = pygame.time.get_ticks()

    def stop_timer(self):
        self._start_time = 0

    def update_duration(self, duration_sec):
        self.stop_timer()
        self._duration_sec = duration_sec


class ResponseOrderSurface(pygame.Surface):
    def __init__(self, size, equipment_list=None, color_bg=GREY, logger=None):
        super(ResponseOrderSurface, self).__init__(size)
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\ResponseOrderSurface.log")

        # Store size and color
        self.size = size
        self.width = size[0]
        self.height = size[1]

        self.borderwidth = 2
        self.color_bg = color_bg
        self._equipment_list = []
        self._equipment_image_list = []
        self._equipment_rect_list = []
        self._equipment_images_width = 0

        self.rect = None
        self.scroll_speed_base = 2
        self.scroll_speed = self.scroll_speed_base

        if equipment_list is not None:
            self.update_order(equipment_list=equipment_list)

    def update_order(self, equipment_list):
        if self._equipment_list != equipment_list:
            # Delete old entry, will exchange all
            self._equipment_list = []
            self._equipment_image_list = []
            self._equipment_images_width = 0

            for equipment_name in equipment_list:
                # Load image and scale to available space
                image_path = os.path.join(DEFAULT_PIC_DIR, equipment_name)
                self.logger.debug(f"calculate image '{image_path}' for screen")

                if not os.path.isfile(image_path):
                    self.logger.error(f"Could not find picture {image_path}, take 'no_image' instead")
                    image_path = DEFAULT_NO_PIC

                image_obj = pygame.image.load(image_path)
                image_obj = scale_image(image_obj=image_obj, max_width=self.width, max_height=self.height-10)
                image_rect = image_obj.get_rect()
                # image_rect.left = self._equipment_images_width
                image_rect.topleft = (self._equipment_images_width, (self.height - image_rect.height)//2)
                self._equipment_images_width += image_obj.get_width()

                self._equipment_list.append(equipment_name)
                self._equipment_image_list.append(image_obj)
                self._equipment_rect_list.append(image_rect)

            # If at least one image is in list, take the first as reference for location
            if self._equipment_image_list:
                self.rect = self._equipment_image_list[0].get_rect()

    def _restart_rect(self):
        # Re-arrange images to start from the right side
        x_axis_offset = 0
        for i, rect in enumerate(self._equipment_rect_list):
            rect.topleft = (self.width + x_axis_offset, 0)
            x_axis_offset += rect.width
            self._equipment_rect_list[i] = rect

    def update(self):
        self.fill(self.color_bg)

        left_padding = self.borderwidth + 1  # Offset of 5 pixels as the boarder already takes 4 pixel

        # Only update if equipment is listed
        if self._equipment_image_list:
            # Only scroll if all images are wither than space available
            if self._equipment_images_width > self.width:
                for i, (image, rect) in enumerate(zip(self._equipment_image_list, self._equipment_rect_list)):
                    current_rect = rect.move(left_padding, 0)
                    self.blit(image, current_rect)

                    # Change x-axis for next drawing. This simulates a moving text upwards
                    rect.move_ip(-self.scroll_speed, 0)
                    self._equipment_rect_list[i] = rect

                # Check if last image reached the middle of the screen
                first_rect = self._equipment_rect_list[0]
                last_rect = self._equipment_rect_list[-1]
                if last_rect.right <= (self.width // 2) + left_padding:
                    self.scroll_speed = self.scroll_speed_base * 8
                elif first_rect.left <= (self.width // 2) + left_padding:
                    self.scroll_speed = self.scroll_speed_base

                if last_rect.right <= left_padding:
                    self._restart_rect()

            else:
                next_image_left = self.rect.left + left_padding
                for image_obj in self._equipment_image_list:
                    rect = image_obj.get_rect()
                    rect.move_ip(next_image_left, 0)
                    next_image_left += rect.width
                    self.blit(image_obj, rect)

        if self.borderwidth:
            pygame.draw.rect(self, BLACK, (0, 0, self.width, self.height), self.borderwidth)


class MessageSurface(pygame.Surface):
    def __init__(self, size, message="", logger=None):
        super(MessageSurface, self).__init__(size)
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\MessageSurface.log")

        message = message
        self.event_obj = None

        self.case_text = None
        self.address_text = None
        self.details_text = None
        self.message_text = None

        self.case_height = self.get_height() * 0.1
        self.address_height = self.get_height() * 0.35
        self.details_height = self.get_height() * 0.35
        self.space_height = self.get_height() * 0.05
        self.message_height = self.get_height() * 0.4  # This should show 2 lines and scroll if more

        self.background_surface = None
        self.render_background(WHITE, RED)
        self.update_text(message)

    def update(self):
        self.fill((0, 0, 0))
        self.blit(self.background_surface, (0, 0))
        if self.case_text:
            self.case_text.draw(self,    10, self.space_height)
            self.address_text.draw(self,  0, self.space_height * 2 + self.case_height)
            self.details_text.draw(self,  0, self.space_height * 3 + self.case_height + self.address_height)
        else:
            self.message_text.draw(self, 0, 0)

    def render_background(self, top_color_bg, bottom_color_bg):
        self.background_surface = pygame.Surface(self.get_size())
        self.background_surface.fill(pygame.Color(top_color_bg))

        width = self.get_width()
        height = int(self.get_height())
        top_color = pygame.Color(top_color_bg)
        bottom_color = pygame.Color(bottom_color_bg)

        # Calculate color for each vertical pixel and draw it to the background
        for y in range(height):

            # Calculate the color for this row
            t = y / (height - 1)
            row_color = top_color.lerp(bottom_color, t)

            # Fill the row with the color
            rect = pygame.Rect(0, y, width, 1)
            # rect = pygame.Rect(0, y + height, width, 1)
            pygame.draw.rect(self.background_surface, row_color, rect)

    def update_text(self, message):

        self.event_obj = EventInfo(event_msg=message)

        if self.event_obj.parsed:
            case_str = CASE_LEVEL_DICT.get(self.event_obj.case_and_level, f"Gruppe: {self.event_obj.case_and_level}")
            self.case_text = ScrollingTextX(case_str, self.case_height, BLACK)

            if self.event_obj.street_number:
                address_str = "{} {} - {}".format(self.event_obj.street_name, self.event_obj.street_number, self.event_obj.city.upper())
            else:
                address_str = "{} - {}".format(self.event_obj.street_name, self.event_obj.city.upper())
            self.address_text = ScrollingTextX(address_str, self.address_height, BLACK)

            if self.event_obj.details:
                details_str = self.event_obj.details
            else:
                details_str = self.event_obj.object_info
            self.details_text = ScrollingTextX(details_str, self.details_height, BLACK)
            color_bg = CASE_COLOR_DICT.get(self.event_obj.case_and_level, pygame.Color('grey'))
            self.render_background(WHITE, color_bg)
            self.message_text = None

        else:
            message_text = self.event_obj.message
            self.message_text = ScrollingTextY(message_text, self.message_height, BLACK, self.get_size())

            self.render_background(WHITE, pygame.Color('gold'))

            self.case_text = None
            self.address_text = None
            self.details_text = None


# ---- SCREENS ----------------------------
class BaseScreen(pygame.Surface):
    def __init__(self, size):
        super(BaseScreen, self).__init__(size)
        self.size = size

    def configure(self):
        raise NotImplementedError("'configure' method not implemented for this screen class")

    def update(self):
        raise NotImplementedError("'update' method not implemented for this screen class")


class SplashScreen(BaseScreen):
    def __init__(self, size, company_path_logo="", color_bg=BLACK, color_fg=WHITE, logger=None):
        super(SplashScreen, self).__init__(size)
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\SplashScreen.log")

        self.company_path_logo = company_path_logo
        self.color_bg          = color_bg
        self.color_fg          = color_fg

        # Do not show logo in the header, it's already present in main surface
        self.header_height = 30
        self._header_surface_obj = HeaderSurface(size=(self.get_width(), self.header_height),
                                                 logger      = logger,
                                                 show_logo   = False,
                                                 show_time   = True,
                                                 show_second = True,
                                                 show_date   = True,
                                                 show_weekday= True)
        self._main_surface = pygame.Surface((self.get_width(), self.get_height()-self.header_height))
        self._set_logo()

    def _set_logo(self):
        surface_width = self._main_surface.get_width()
        surface_height = self._main_surface.get_height()
        max_image_width = surface_width - 50
        max_image_height = surface_height - 50

        self._main_surface.fill(self.color_bg)

        if os.path.isfile(self.company_path_logo):
            # Load image
            image = pygame.image.load(self.company_path_logo)
            image = scale_image(image_obj=image, max_width=max_image_width, max_height=max_image_height)

            # Center image in the middle of the surface
            x = (surface_width - image.get_width()) // 2
            y = (surface_height - image.get_height()) // 2
            self._main_surface.blit(image, (x, y))
        else:
            pygame.draw.line(self._main_surface, RED, (0, 0), (surface_width, surface_height), 5)
            pygame.draw.line(self._main_surface, RED, (surface_width, 0), (0, surface_height), 5)

    def update(self):
        self.fill(self.color_bg)

        self._header_surface_obj.update()
        self.blit(self._header_surface_obj, (0, 0))
        self.blit(self._main_surface, (0, self.header_height + 1))

    def configure(self, **kw):
        update_image = False
        for key, value in list(kw.items()):
            if key == 'company_path_logo':
                self.company_path_logo = value
                update_image = True
            elif key == 'color_bg':
                self.color_bg = value
                update_image = True
            elif key == 'color_fg':
                self.color_fg = value
                update_image = True
            else:
                self.logger.error(f"Unknown configuration set: '{key}': '{value}'")

        if update_image is True:
            self._set_logo()


class EventScreen(BaseScreen):
    def __init__(self, size, show_message_bar=True, alarm_message="", show_progress_bar=False, progress_bar_duration=7 * 60,
                 show_response_order=False, equipment_list=None, image_path_left="", image_path_right="", logger=None,
                 path_sound_folder=DEFAULT_SOUND_DIR, force_sound_file="", force_sound_repetition=1):
        """
        +---------MessageBar----------+
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

        :param size:                  Tuple for screen size in format (x, y)
        :param show_message_bar:      If true the MessageBar at the top of the screen is shown.
        :param alarm_message:         Message string from the police, will shown in the MessageBar
        :param show_progress_bar:     If true a progress bar is shown at the bottom of the screen
        :param progress_bar_duration: Time in second for the progress bar to reach 100%
        :param show_response_order:   If true a response bar is shown at the bottom the the screen with equipment images
        :param equipment_list:        List of pictures to display in the response bar.
        :param image_path_left:       Image which is shown on the left side. If image_path_rigth is empty, this image
                                      will shown over the whole width
        :param image_path_right:      Image which is shown on the right side
        :param logger:                Logger instance
        """
        super(EventScreen, self).__init__(size)
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\EventScreen.log")

        # Store the height of the several places
        self.message_bar_height = 220  # Pixel
        self.progress_bar_height = 100  # Pixel
        self.response_order_height = 150  # Pixel
        self.images_height = 0  # Is calculated and set in update_images --> it depends on the given show_... bar's

        # Configure the alarm message bar
        message_size = (self.get_width(), self.message_bar_height)
        self.show_message_bar = show_message_bar
        self.message_obj = MessageSurface(size=message_size, message=alarm_message, logger=self.logger)

        # Configure the progress bar
        progress_size = (self.get_width(), self.progress_bar_height)
        self.show_progress_bar = show_progress_bar
        self.progress_bar_obj = ProgressBarSurface(size=progress_size, duration_sec=progress_bar_duration)

        # Configure the response order bar
        response_size = (self.get_width(), self.response_order_height)
        self.show_response_order = show_response_order
        self.response_order_obj = ResponseOrderSurface(size=response_size,
                                                       equipment_list=equipment_list,
                                                       logger=self.logger)

        # Configure images
        self.image_path_left = image_path_left
        self.image_obj_left = None
        self.image_rect_left = None
        self.image_path_right = image_path_right
        self.image_obj_right = None
        self.image_rect_right = None
        self.update_images()

        # Sound
        self.sound_file = ""
        self.sound_file_force = force_sound_file
        self.sound_repeat = 1
        self.sound_repeat_force = force_sound_repetition
        self.sound_obj = AlarmSound(path=path_sound_folder, logger=self.logger)

    def __del__(self):
        self.sound_obj.stop()

    def configure(self, **kw):
        update_image = False
        update_sound = False
        for key, value in list(kw.items()):
            if key == 'alarm_message':
                self.message_obj.update_text(value)
            elif key == 'image_left':
                update_image = True
                self.image_path_left = value
            elif key == 'image_right':
                update_image = True
                self.image_path_right = value
            elif key == 'equipment_list':
                self.response_order_obj.update_order(equipment_list=value)
            elif key == 'progress_bar_duration':
                self.progress_bar_obj.update_duration(duration_sec=value)
            elif key == 'show_alarm_message':
                update_image = True
                self.show_message_bar = value
            elif key == 'show_progress_bar':
                update_image = True
                self.show_progress_bar = value
            elif key == 'show_response_order':
                update_image = True
                self.show_response_order = value
            elif key == 'sound_file':
                self.sound_file = value
                update_sound = True
            elif key == 'sound_repeat':
                self.sound_repeat = value
                update_sound = True
            elif key == 'sound_repeat_force':
                self.sound_repeat_force = value
                update_sound = True
            elif key == 'sound_file_force':
                self.sound_file_force = value
                update_sound = True
            elif key == 'path_sound_folder':
                if pathlib.Path(value).is_dir():
                    self.sound_obj.sound_folder_path = value
                    self.logger.info(f"Set default sound path to '{value}'")
                else:
                    self.sound_obj.sound_folder_path = DEFAULT_SOUND_DIR
                    self.logger.info(f"Could not find sound path '{value}', set therefore to default '{DEFAULT_SOUND_DIR}'")
            else:
                self.logger.error(f"Unknown configuration set: '{key}': '{value}'")

        if update_image:
            self.update_images()
        if update_sound:
            self.update_sound()

    def update_images(self):
        # Calculate size of Images
        progress_height = int(self.show_progress_bar)   * self.progress_bar_height
        response_height = int(self.show_response_order) * self.response_order_height
        message_height = int(self.show_message_bar) * int(self.message_bar_height)

        # calculate height and width and resize the canvas afterwards
        self.images_height = int(self.get_height() - message_height - progress_height - response_height)
        images_width = int(self.get_width())

        # if right picture is empty, show left picture as full screen and clear right picture object
        if not self.image_path_right:
            # Only single picture available, delete second if it was defined prior
            self.image_obj_right = None
        else:
            # Two picture shall be shown --> divide available space for each image
            images_width = images_width // 2

        if self.image_path_left:
            image_path = self.image_path_left
            if not os.path.isfile(image_path):
                self.logger.error(f"Could not find picture {image_path}, take 'no_image' instead")
                image_path = DEFAULT_NO_PIC

            image_obj = pygame.image.load(image_path)
            image_obj = scale_image(image_obj=image_obj, max_width=images_width, max_height=self.images_height)
            image_rect = image_obj.get_rect()
            image_rect.center = (images_width // 2, message_height + self.images_height // 2)
            self.image_obj_left = image_obj
            self.image_rect_left = image_rect

        if self.image_path_right:
            image_path = self.image_path_right
            if not os.path.isfile(image_path):
                self.logger.error(f"Could not find picture {image_path}, take 'no_image' instead")
                image_path = DEFAULT_NO_PIC

            image_obj = pygame.image.load(image_path)
            image_obj = scale_image(image_obj=image_obj, max_width=images_width, max_height=self.images_height)
            image_rect = image_obj.get_rect()
            image_rect.center = (images_width + images_width // 2, message_height + self.images_height // 2)
            self.image_obj_right = image_obj
            self.image_rect_right = image_rect

    def update_sound(self):
        if self.sound_file and self.sound_obj.is_file(self.sound_file):
            self.sound_obj.load_music(file=self.sound_file)
            self.sound_obj.start(loops=self.sound_repeat, offset=0, delay=2, pause=15)
            self.logger.info("Play sound")
        elif self.sound_file_force and self.sound_obj.is_file(self.sound_file_force):
            self.sound_obj.load_music(file=self.sound_file_force)
            self.sound_obj.start(loops=self.sound_repeat_force, offset=0, delay=2, pause=15)
            self.logger.info("Play sound forced")
        else:
            self.logger.warning("Could not start sound, no file defined")

    def update(self):
        self.fill(BLACK)

        # Update and blit the message bar if available
        if self.show_message_bar:
            self.message_obj.update()
            self.blit(self.message_obj, (0, 0))

        # blit images if available
        if self.image_obj_left:
            self.blit(self.image_obj_left, self.image_rect_left)
        if self.image_obj_right:
            self.blit(self.image_obj_right, self.image_rect_right)

        # Update and blit progress bar if available
        if self.show_progress_bar:
            progress_offset = self.images_height
            progress_offset += int(self.show_message_bar) * int(self.message_bar_height)
            self.progress_bar_obj.update()
            self.blit(self.progress_bar_obj, (0, progress_offset))

        # Update and blit response order bar if available
        if self.show_response_order:
            response_offset = self.images_height
            response_offset += int(self.show_message_bar) * int(self.message_bar_height)
            response_offset += int(self.show_progress_bar) * int(self.progress_bar_height)
            self.response_order_obj.update()
            self.blit(self.response_order_obj, (0, response_offset))


class ClockScreen(BaseScreen):
    def __init__(self, size, logger=None):
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

        :param size:   Tuple for screen size in format (x, y)
        :param logger: Logger instance
        """
        super(ClockScreen, self).__init__(size)
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\ClockScreen.log")

        self.color_bg = BLACK
        self.color_fg = WHITE

        self._analog_clk = AnalogClockSurface(size             = (self.size[0], self.size[1]*0.8),
                                              color_bg         = self.color_bg,
                                              show_second_hand = True,
                                              show_minute_hand = True,
                                              show_hour_hand   = True,
                                              logger           = self.logger)

        self._digital_clk = DigitalClockSurface(size      = (self.size[0], self.size[1]*0.2),
                                                color_bg  = self.color_bg,
                                                color_fg  = self.color_fg,
                                                show_time = False,
                                                show_date = True,
                                                logger    = self.logger)

    def update(self):
        self.fill(self.color_bg)
        self._analog_clk.update()
        self.blit(self._analog_clk, (0, 0))
        self._digital_clk.update()
        self.blit(self._digital_clk, (0, self._analog_clk.get_height()))

    def configure(self, **kw):
        for key, value in list(kw.items()):
            if key == 'show_second_hand':
                self._analog_clk.configure(show_second_hand=value)
            elif key == 'show_minute_hand':
                self._analog_clk.configure(show_minute_hand=value)
            elif key == 'show_hour_hand':
                self._analog_clk.configure(show_hour_hand=value)
            elif key == 'show_digital_time':
                self._digital_clk.configure(show_time=value)
            elif key == 'show_digital_date':
                self._digital_clk.configure(show_date=value)
            elif key == 'show_digital_seconds':
                self._digital_clk.configure(show_second=value)
            else:
                self.logger.error(f"Unknown configuration set: '{key}': '{value}'")


class SlideshowScreen(BaseScreen):
    def __init__(self, size, logger=None, **kwargs):
        super(SlideshowScreen, self).__init__(size)
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\SlideshowScreen.log")

        # store path where the pictures for the slideshow are stored
        self.slideshow_path      = kwargs.get("slideshow_path", "")
        self.sort_alphabetically = kwargs.get("short_alphabetically", False)
        self.display_duration    = kwargs.get("seconds_between_images", 4)

        self.last_image_time     = None
        self.image_list          = []
        self.new_image           = None
        self.current_image       = None
        self.current_image_index = 0
        self.fade_alpha          = 0  # can be -1 ... 1 where -1 is the old image and 1 the new
        self.fade_over_bg        = kwargs.get("fade_over_background", False)
        if self.slideshow_path:
            self.load_images()

        # Store settings for header-bar
        self.show_header_bar   = kwargs.get("show_header", True)
        self.company_path_logo = kwargs.get("company_path_logo", "")
        self.company_name      = kwargs.get("company_name", "")
        self.header_height     = 40
        self._header_surface_obj = HeaderSurface(size              = (self.size[0], self.header_height),
                                                 logger            = logger,
                                                 show_time         = False,
                                                 color_bg          = GREY,
                                                 company_path_logo = self.company_path_logo,
                                                 company_name      = self.company_name)

        self._font = get_font_obj(font_name=DEFAULT_FONT_BOLD, font_size=50)

        self.bg_color = BLACK
        self.fg_color = RED

    def load_images(self):
        images = []
        successful = True

        # Check if path to images is defined
        if self.slideshow_path == '':
            self.logger.error("ERROR: Path to slideshow folder not set yet")
            successful = False

        # check if slideshow folder already exists and create it if necessary
        if os.path.exists(self.slideshow_path):
            for filename in os.listdir(self.slideshow_path):
                if filename.lower().endswith(('.jpg', '.jpeg', '.bmp', '.png', '.gif', '.eps', '.tif', '.tiff')):
                    images.append(filename)
        else:
            try:
                os.makedirs(self.slideshow_path)
            except FileNotFoundError as e:
                self.logger.critical(f"Could not create temporary folder, probably root drive "
                                     f"in path '{self.slideshow_path}' is not existing", exception=e.args)

        self.current_image_index = 0
        self.image_list = images
        self.sort_images()
        return successful

    def sort_images(self):
        if self.sort_alphabetically:
            self.image_list = sorted(self.image_list)
        else:
            self.image_list = random.sample(self.image_list, len(self.image_list))

    def get_next_image_obj(self):
        if self.image_list:

            if self.current_image_index >= len(self.image_list):
                self.current_image_index = 0

            max_height = self.size[1]
            if self.show_header_bar:
                max_height -= self.header_height

            path = os.path.join(self.slideshow_path, self.image_list[self.current_image_index])
            image = pygame.image.load(path)
            image = scale_image(image_obj  = image,
                                max_height = max_height,
                                max_width  = self.size[0])

            self.current_image_index += 1
        else:
            image = self._font.render("Keine Bilder zum Anzeigen :(", True, self.fg_color, self.bg_color)

        return image

    def update(self):

        self.fill(self.bg_color)

        # If this is the first call, the current image is empty
        if self.current_image is None:
            self.current_image = self.get_next_image_obj()
            self.last_image_time = time.time()
            self.fade_alpha = 1  # Completely faded

        # Check if picture shall be updated
        if self.fade_alpha >= 1 and time.time() - self.last_image_time >= self.display_duration:
            self.new_image = self.get_next_image_obj()
            self.fade_alpha = -1 if self.fade_over_bg else 0
            self.last_image_time = None

        # If fading is in progress, the alpha channel is less than 1
        if self.fade_alpha < 1:
            header_height = self.header_height if self.show_header_bar else 0
            fade_surface = pygame.Surface((self.size[0], self.size[1]-header_height))
            fade_surface.fill(BLACK)

            # The fade range is -1 ... 1 where -1 is the complete old image while 1 is the complete new image
            if self.fade_alpha < 0:
                # Fade out old picture
                fade_surface.set_alpha(255 - int(abs(self.fade_alpha) * 255))
                x = (self.size[0] - self.current_image.get_width()) // 2
                y = (self.size[1] - self.current_image.get_height()) // 2
                if self.show_header_bar:
                    y += self.header_height
                self.blit(self.current_image, (x, y))
                self.blit(fade_surface, (x, y))
            else:
                if self.fade_over_bg:
                    # Fade in new picture
                    fade_surface.set_alpha(255 - int(self.fade_alpha * 255))
                    x = (self.size[0] - self.new_image.get_width()) // 2
                    y = (self.size[1] - self.new_image.get_height()) // 2
                    if self.show_header_bar:
                        y += self.header_height
                    self.blit(self.new_image, (x, y))
                    self.blit(fade_surface, (x, y))
                else:
                    # Do not fade over background color, so directly fade out old picture and fade in new
                    self.current_image.set_alpha(255 - int(self.fade_alpha * 255))
                    self.new_image.set_alpha(int(self.fade_alpha * 255))

                    x_old = (self.size[0] - self.current_image.get_width()) // 2
                    y_old = (self.size[1] - self.current_image.get_height()) // 2
                    x_new = (self.size[0] - self.new_image.get_width()) // 2
                    y_new = (self.size[1] - self.new_image.get_height()) // 2
                    if self.show_header_bar:
                        y_old += self.header_height
                        y_new += self.header_height
                    self.blit(self.current_image, (x_old, y_old))
                    self.blit(self.new_image, (x_new, y_new))

            # Increment fade step and check if fading is finished
            self.fade_alpha += 1/FPS
            if self.fade_alpha >= 1:
                self.last_image_time = time.time()
                self.current_image = self.new_image
                self.new_image = None
        else:
            # No fade, just show picture
            x = (self.size[0] - self.current_image.get_width()) // 2
            y = (self.size[1] - self.current_image.get_height()) // 2
            if self.show_header_bar:
                y += self.header_height
            self.blit(self.current_image, (x, y))

        # Update header
        if self.show_header_bar:
            self._header_surface_obj.update()
            self.blit(self._header_surface_obj, (0, 0))

    def configure(self, **kw):
        for key, value in list(kw.items()):
            if key == 'seconds_between_images':
                self.display_duration = int(value)
                self.logger.info("Set 'seconds_between_images' to {}".format(value))
            elif key == 'fade_over_background':
                self.fade_over_bg = value
                self.logger.info("Set 'fade_over_background' to {}".format(value))
            elif key == 'sort_alphabetically':
                self.sort_alphabetically = value
                self.logger.info("Set 'sort_alphabetically' to {}".format(value))
                self.sort_images()
            elif key == 'slideshow_path':
                self.slideshow_path = value
                self.logger.info("Set 'slideshow_path' to {}".format(value))
                self.load_images()
            elif key == 'company_path_logo':
                self.company_path_logo = value
                self.logger.info("Set 'company_path_logo' to {}".format(value))
                self._header_surface_obj.configure(company_path_logo=self.company_path_logo)
                self.load_images()
            elif key == 'company_name':
                self.company_name = value
                self._header_surface_obj.configure(company_name=self.company_name)
            elif key == 'show_header_bar':
                self.show_header_bar = value
                self.logger.info("Set 'show_header_bar' to {}".format(value))
            else:
                self.logger.error(f"Unknown configuration set: '{key}': '{value}'")


class OffScreen(BaseScreen):
    def __init__(self, size, logger=None, **kwargs):
        super(OffScreen, self).__init__(size)
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\OffScreen.log")

        self.bg_color = BLACK
        self.fill(self.bg_color)

    def configure(self):
        # This screen cannot be configured
        pass

    def update(self):
        # Noting to update
        pass


# ---- SCREEN THREAD / HANDLER ------------
class Screen(Enum):
    """
    This enumeration holds all available screens for display.
    ORDER: To define the classes within the enumeration, they must already be defined beforehand
    """
    off   = OffScreen
    event = EventScreen
    clock = ClockScreen
    splash = SplashScreen
    slideshow = SlideshowScreen


class GuiThread(threading.Thread):
    def __init__(self, size, full_screen, switch_delay_after_event=0, switch_to_screen_after_event='off', cec_enable=False, hdmi_port_nbr=1,
                 standby_enable=False, logger=None):
        threading.Thread.__init__(self, daemon=True, name="GuiThread")
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\GuiHandler.log")

        # catch exceptions in this thread
        threading.excepthook = self.logger.thread_except_hook

        self.size                         = size
        self.full_screen                  = full_screen
        self.switch_delay_after_event     = switch_delay_after_event
        self.switch_to_screen_after_event = switch_to_screen_after_event

        self._timer_obj: Union[threading.Timer, None] = None

        self.tv_remote_obj = GraphicOutputDriver(logger=self.logger, cec_enable=cec_enable, hdmi_port_nbr=hdmi_port_nbr, standby_enable=standby_enable)

        self._running    = False
        self._queue      = queue.Queue()

        self._fps = FPS

    def change_screen(self, data):
        self._queue.put(data)

    def run(self):

        if self.full_screen:
            window = pygame.display.set_mode(self.size, pygame.FULLSCREEN)
        else:
            window = pygame.display.set_mode(self.size)

        clock      = pygame.time.Clock()
        screen_obj = None

        self._running = True
        while self._running:

            # Check user interaction
            for event in pygame.event.get():
                # Did the user click the window close button?
                if event.type == pygame.QUIT:
                    self._running = False

                # Did the user press ESC-button?
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._running = False

            # Check queue for data (new screen oder configuration for current screen)
            try:
                screen_name   = None
                screen_config = None
                data          = self._queue.get_nowait()

                if isinstance(data, tuple):
                    screen_name = data[0]
                    screen_config = data[1]
                    self.logger.info(f"switch to screen {screen_name}", screen_config=screen_config)
                elif isinstance(data, Screen):
                    screen_name = data
                    self.logger.info(f"switch to screen {screen_name}")
                elif isinstance(data, dict):
                    screen_config = data
                    self.logger.info("received new configuration for current screen", screen_config=screen_config)
                else:
                    self.logger.error(f"Unknown data type '{type(data)}' received from queue")

                if screen_name is not None:
                    screen_obj = screen_name.value(size=window.get_size(), logger=self.logger)

                    # On a screen change always check if status of the television shall be changed
                    if screen_name == Screen.off:
                        self.tv_remote_obj.set_visual(state=OutputState.off)
                    else:
                        self.tv_remote_obj.set_visual(state=OutputState.on)

                    # On screen change to event, trigger timer if self.switch_delay_after_event is != 0
                    if screen_name == Screen.event and self.switch_delay_after_event != 0:
                        log = f"This is a event, switch automatically to '{self.switch_to_screen_after_event}' after {self.switch_delay_after_event} seconds"
                        self.logger.info(log)
                        switch_to_screen_obj = get_screen_obj_from_string(screen_name=self.switch_to_screen_after_event)
                        self.start_timer(timer_time=self.switch_delay_after_event, screen_name=switch_to_screen_obj)
                    else:
                        self.stop_timer()

                if screen_config is not None:
                    if hasattr(screen_obj, "configure"):
                        screen_obj.configure(**screen_config)
                    else:
                        self.logger.error(f"Failed to configer {screen_obj.__class__.__name__}, this object dies not have a 'configure' attribute")
            except queue.Empty:
                pass

            # Fill the background with white
            window.fill((255, 255, 255))
            if screen_obj is not None:
                screen_obj.update()
                window.blit(screen_obj, (0, 0))
            pygame.display.flip()

            # Control the FPS
            clock.tick(self._fps)

    def stop(self):
        self._running = False
        pygame.quit()

    def start_timer(self, timer_time: int, screen_name: Screen):
        """
        This method starts a timer to switch the screen to off-screen after
        """

        self.stop_timer()

        self.logger.info(f"Create new timer. Switch to '{screen_name}' after {timer_time} seconds")
        self._timer_obj = threading.Timer(interval=timer_time, function=self.change_screen, args=[(screen_name, {})])
        self._timer_obj.daemon = True  # Kill timer if application is stopped
        self._timer_obj.start()

    def stop_timer(self):
        if self._timer_obj is not None:
            self.logger.info("Timer not 'None', cancel it first")
            self._timer_obj.cancel()
            self._timer_obj = None


class GuiHandler(object):
    def __init__(self, logger=None, gui_settings=None, splash_settings=None, clock_settings=None,
                 event_settings=None, slideshow_settings=None):
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\GuiHandler.log")

        self.gui_settings       = gui_settings if gui_settings is not None else dict()
        self.splash_settings    = splash_settings if splash_settings is not None else dict()
        self.clock_settings     = clock_settings if clock_settings is not None else dict()
        self.event_settings     = event_settings if event_settings is not None else dict()
        self.slideshow_settings = slideshow_settings if slideshow_settings is not None else dict()

        self._thread = None
        self._current_screen = None

        screen_info = pygame.display.Info()
        if self.gui_settings.get("full_screen_enable", False):
            self.size = (screen_info.current_w, screen_info.current_h)
        else:
            self.size = (screen_info.current_w * 0.9, screen_info.current_h * 0.9)

    def set_screen_and_config(self, screen_name: Screen, screen_config: dict):
        screen_config = self._merge_config(screen_name, screen_config)
        self._current_screen = screen_name
        self._thread.change_screen((screen_name, screen_config))

    def set_screen(self, screen_name: Screen):
        """
        Do not load screen without configuration. If user does not apply any config, send at least
        the available default configuration

        :param screen_name:
        :return:
        """
        default_config = self._merge_config(screen_name=screen_name, screen_config=dict())
        self.set_screen_and_config(screen_name=screen_name, screen_config=default_config)

    def set_configuration(self, screen_config: dict):
        screen_config = self._merge_config(self._current_screen, screen_config)
        self._thread.change_screen(screen_config)

    def _merge_config(self, screen_name, screen_config):
        config = dict()
        if screen_name == Screen.splash:
            config = dict(self.splash_settings)
        elif screen_name == Screen.event:
            config = dict(self.event_settings)
        elif screen_name == Screen.clock:
            config = dict(self.clock_settings)
        elif screen_name == Screen.slideshow:
            config = dict(self.slideshow_settings)

        # Remove undefined key's
        for key, value in dict(config).items():
            if value is None or value == "":
                del config[key]

        config.update(screen_config)
        return config

    def start(self):
        self._thread = GuiThread(size                         = self.size,
                                 full_screen                  = self.gui_settings.get("full_screen_enable", False),
                                 switch_delay_after_event     = self.gui_settings.get("switch_screen_delay_after_event", 0),
                                 switch_to_screen_after_event = self.gui_settings.get("switch_to_screen_after_event", 'off'),
                                 cec_enable                   = self.gui_settings.get("cec_enable", False),
                                 hdmi_port_nbr                = self.gui_settings.get("hdmi_port_number", 1),
                                 standby_enable               = self.gui_settings.get("standby_enable", False),
                                 logger                       = self.logger)

        # Deactivate mouse over GUI and set the SplashScreen as default start screen
        pygame.mouse.set_visible(False)
        self.set_screen_and_config(screen_name=Screen.splash,
                                   screen_config={"company_path_logo": self.slideshow_settings.get("company_path_logo", "")})

        self._thread.start()

        # Check if the screen shall automatically change after application has been started
        switch_delay_after_start     = self.gui_settings.get("switch_screen_delay_after_start", 0)
        switch_to_screen_after_start = self.gui_settings.get("switch_to_screen_after_start", 'off')
        if switch_delay_after_start != 0:
            time.sleep(1)
            screen_obj = get_screen_obj_from_string(screen_name=switch_to_screen_after_start)
            self.logger.info(f"Starting GuiHandler, switch automatic to screen '{screen_obj}' after {switch_delay_after_start} seconds")
            self._thread.start_timer(timer_time=switch_delay_after_start, screen_name=screen_obj)

    def stop(self):
        self._thread.stop()
        self._thread.join()

    def is_running(self):
        return self._thread.is_alive()


def test_screen_top(screen_obj):
    def update_screen():
        header_obj.update()
        screen_obj.blit(header_obj, (0, 0))
        pygame.display.flip()

    header_obj = HeaderSurface(screen_obj.get_size())

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
        slideshow_obj.update()
        screen_obj.blit(slideshow_obj, (0, 0))
        pygame.display.flip()

    clock = pygame.time.Clock()
    slideshow_obj = SlideshowScreen(screen_obj.get_size())

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
    this_screen = pygame.display.Info()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((this_screen.current_w, this_screen.current_h))
    # screen = pygame.display.set_mode((this_screen.current_w, 500))
    # screen = pygame.display.set_mode((500, 500))
    splash_screen = SplashScreen((this_screen.current_w, this_screen.current_h), company_path_logo="C:\\Firefinder\\logo.png")
    # slideshow_obj = SlideshowScreen((this_screen.current_w, this_screen.current_h), path_to_images="D:\\Firefinder\\Slideshow")
    # analog_clock_surface = AnalogClockSurface((this_screen.current_w, 1200))
    # digital_clock_surface = DigitalClockSurface((this_screen.current_w, 300))
    clock_surface = ClockScreen((this_screen.current_w, this_screen.current_h))
    # scrolling = ScrollingTextY(text="Das ist ein sehr sehr sehr langer Text welcher wohl nicht platz hat und daher in Laufschrift angezeigt werden muss", font_size=100, font_color=BLACK, screen_size=(500, 500))
    # scrolling = ScrollingTextY(text="Das ist ein kurzer text", font_size=100, font_color=BLACK, screen_size=(500, 500))
    # event_screen = MessageSurface((this_screen.current_w, 400), message="AA, AA Sprinkler, Ittigen;Ey,19, Geschäftshaus Bermuda Ittigen, 223 326 (Geschäftshaus Bermuda Ittigen)")
    # event_screen = MessageSurface((this_screen.current_w, 400), message="H2, Öl, Benzin, Ittigen;Allmitstrasse, Flüssigkeiten aufnehmen nach Pw-Pw, 1 Fahrzeug auf der Seite, POL vor Ort, Ittigen Schönbühl Kreuzung")
    # progress_bar = ProgressBarSurface((500, 100), 30)
    # response_order = ResponseOrderSurface((800, 100), ["Fz_1.png", "Fz_2.png", "Fz_3.png"])
    # response_order = ResponseOrderSurface((500, 100), ["Fz_1.png", "Fz_2.png", "Fz_3.png", "Fz_4.png", "Fz_5.png", "Fz_6.png", "Fz_7.png", "Fz_8.png", "Fz_9.png", ])
    event_screen = EventScreen(size=(this_screen.current_w, this_screen.current_h),
                               show_message_bar=True,
                               alarm_message="AA, AA Sprinkler, Ittigen;Ey,19, Geschäftshaus Bermuda Ittigen, 223 326 (Geschäftshaus Bermuda Ittigen)",
                               show_progress_bar=True,
                               progress_bar_duration= 60,
                               show_response_order=True,
                               equipment_list=["Fz_1.png", "Fz_2.png", "Fz_3.png", "Fz_4.png", "Fz_5.png", "Fz_6.png", "Fz_7.png", "Fz_8.png", "Fz_9.png", ],
                               image_path_left="C:\\FireFinder\\direction_1.jpg",
                               image_path_right="C:\\FireFinder\\direction_detail_1.jpg",
                               )
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
        # test_slideshow(screen_obj=screen)
        # pygame.quit()
        # break

        # splash_screen.update()
        # screen.blit(splash_screen, (0, 0))
        # slideshow_obj.update()
        # screen.blit(slideshow_obj, (0, 0))
        # analog_clock_surface.update()
        # screen.blit(analog_clock_surface, (0, 0))
        # digital_clock_surface.update()
        # screen.blit(digital_clock_surface, (0, 0))
        clock_surface.update()
        screen.blit(clock_surface, (0, 0))
        # clock_surface.update()
        # screen.blit(clock_surface, (0, 0))
        # scrolling.draw(surface=screen, x=0, y=0)
        # event_screen.update()
        # screen.blit(event_screen, (0, 0))
        # progress_bar.update()
        # screen.blit(progress_bar, (0, 0))
        # response_order.update()
        # screen.blit(response_order, (0, progress_bar.get_height()))
        # event_screen.update()
        # screen.blit(event_screen, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

