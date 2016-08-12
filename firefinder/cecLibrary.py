#!/usr/bin/env python

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

import sys
import logging
import logging.handlers
from celery import Task

CEC_DEBUG = True

# logging
FORMAT = "%(asctime)-15s : %(message)s"
logHandler = logging.StreamHandler(sys.stdout)
logHandler.setFormatter(logging.Formatter(FORMAT))
logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG if CEC_DEBUG else logging.INFO)
logger.addHandler(logHandler)

logger.critical("Startup")

try:
    import cec
except ImportError:
    cec = None
    logger.error("ImportError for cec lib")

if cec:
    class PyCecClient:
        cecconfig = cec.libcec_configuration()
        lib = {}
        # don't enable debug logging by default
        log_level = cec.CEC_LOG_TRAFFIC

        # ----------------------------------------------------------------------
        def set_configuration(self):
            # create a new libcec_configuration
            self.cecconfig.strDeviceName = "FireFinder"
            self.cecconfig.bActivateSource = 0
            self.cecconfig.deviceTypes.Add(cec.CEC_DEVICE_TYPE_RECORDING_DEVICE)
            self.cecconfig.clientVersion = cec.LIBCEC_VERSION_CURRENT

        # ----------------------------------------------------------------------
        def set_log_callback(self, callback):
            self.cecconfig.set_log_callback(callback)

        # ----------------------------------------------------------------------
        def set_key_press_callback(self, callback):
            self.cecconfig.set_key_press_callback(callback)

        # ----------------------------------------------------------------------
        def detect_adapter(self):
            # detect an adapter and return the com port path
            retval = None
            adapters = self.lib.DetectAdapters()
            for adapter in adapters:
                print("found a CEC adapter:")
                print("port:     " + adapter.strComName)
                print("vendor:   " + hex(adapter.iVendorId))
                print("product:  " + hex(adapter.iProductId))
                retval = adapter.strComName
            return retval

        # ----------------------------------------------------------------------
        def init_lib_cec(self):
            # initialise libCEC
            self.lib = cec.ICECAdapter.Create(self.cecconfig)
            # print libCEC version and compilation information
            print("libCEC version " + self.lib.VersionToString(
                self.cecconfig.serverVersion) + " loaded: " + self.lib.GetLibInfo())

            # search for adapters
            adapter = self.detect_adapter()
            if adapter is None:
                logger.error("No adapters found")
            else:
                if self.lib.Open(adapter):
                    logger.info("cec connection opened")
                else:
                    logger.error("failed to open a connection to the CEC adapter")

        # ----------------------------------------------------------------------
        def process_command_self(self):
            # display the addresses controlled by libCEC
            addresses = self.lib.GetLogicalAddresses()
            output_string = "Addresses controlled by libCEC: "
            x = 0
            not_first = False
            while x < 15:
                if addresses.IsSet(x):
                    if not_first:
                        output_string += ", "
                    output_string += self.lib.LogicalAddressToString(x)
                    if self.lib.IsActiveSource(x):
                        output_string += " (*)"
                    not_first = True
                x += 1
            print(output_string)

        # ----------------------------------------------------------------------
        def process_command_active_source(self):
            # send an active source message
            self.lib.SetActiveSource()

        # ----------------------------------------------------------------------
        def process_command_standby(self):
            # send a standby command
            self.lib.StandbyDevices(cec.CECDEVICE_BROADCAST)

        # ----------------------------------------------------------------------
        def power_on_television(self):
            # send a standby command
            self.lib.PowerOnDevices(cec.CECDEVICE_TV)

        # ----------------------------------------------------------------------
        def process_command_transmit(self, data):
            # send a custom command
            cmd = self.lib.CommandFromString(data)
            print("transmit " + data)
            if self.lib.Transmit(cmd):
                print("command sent")
            else:
                print("failed to send command")

        # ----------------------------------------------------------------------
        def process_command_scan(self):
            # scan the bus and display devices that were found
            print("requesting CEC bus information ...")
            str_log = "CEC bus information\n===================\n"
            addresses = self.lib.GetActiveDevices()
            # active_source = self.lib.GetActiveSource()
            x = 0
            while x < 15:
                if addresses.IsSet(x):
                    vendor_id = self.lib.GetDeviceVendorId(x)
                    physical_address = self.lib.GetDevicePhysicalAddress(x)
                    active = self.lib.IsActiveSource(x)
                    cec_version = self.lib.GetDeviceCecVersion(x)
                    power = self.lib.GetDevicePowerStatus(x)
                    osd_name = self.lib.GetDeviceOSDName(x)
                    str_log += "device #" + str(x) + ": " + self.lib.LogicalAddressToString(x) + "\n"
                    str_log += "address:       " + str(physical_address) + "\n"
                    str_log += "active source: " + str(active) + "\n"
                    str_log += "vendor:        " + self.lib.VendorIdToString(vendor_id) + "\n"
                    str_log += "CEC version:   " + self.lib.CecVersionToString(cec_version) + "\n"
                    str_log += "OSD name:      " + osd_name + "\n"
                    str_log += "power status:  " + self.lib.PowerStatusToString(power) + "\n\n\n"
                x += 1
            print(str_log)

        # ----------------------------------------------------------------------
        def log_callback(self, level, time, message):
            # logging callback
            """

            :param time: systemtime
            :param level: loglevel
            :param message: logmessage
            """
            if level > self.log_level:
                return 0

            if level == cec.CEC_LOG_ERROR:
                log = "%s" % message
                logger.error(log)
            elif level == cec.CEC_LOG_WARNING:
                log = "%s" % message
                logger.warning(log)
            elif level == cec.CEC_LOG_NOTICE:
                log = "%s" % message
                logger.info(log)
            elif level == cec.CEC_LOG_TRAFFIC:
                log = "TRAFFIC: %s" % message
                logger.info(log)

            elif level == cec.CEC_LOG_DEBUG:
                log = "%s" % message
                logger.debug(log)

            return 0

        # ----------------------------------------------------------------------
        @staticmethod
        def key_press_callback(key, duration):
            # key press callback
            print("[key pressed] " + str(key))
            return 0

        # ----------------------------------------------------------------------
        def __init__(self):
            self.set_configuration()


class TvPower(Task):
    def __init__(self):
        if cec:
            self.ceclib = PyCecClient()

            # initialise libCEC and enter the main loop
            self.ceclib.init_lib_cec()
            #             self.ceclib.set_log_callback(self.ceclib.log_callback)

    # ----------------------------------------------------------------------
    def run(self, on):
        log = "Received: {}".format(on)
        logger.info(log)
        # self.last_message = time.time() # can use it for monitoring later on

        if cec:
            if on:
                print("switching tv on now")
                self.ceclib.power_on_television()
                self.ceclib.process_command_active_source()
            else:
                print("switching tv off now")
                self.ceclib.process_command_standby()

        return log
