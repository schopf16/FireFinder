#!/usr/bin/env python

'''
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
'''

CEC_DEBUG = True

import sys
import logging
import logging.handlers

# logging
FORMAT = "%(asctime)-15s : %(message)s"
# logHandler = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=2*1024*1024, backupCount=2)
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
    class pyCecClient:
        cecconfig = cec.libcec_configuration()
        lib = {}
        # don't enable debug logging by default
        log_level = cec.CEC_LOG_TRAFFIC
        
        #----------------------------------------------------------------------
        def SetConfiguration(self):
            # create a new libcec_configuration
            self.cecconfig.strDeviceName = "FireFinder"
            self.cecconfig.bActivateSource = 0
            self.cecconfig.deviceTypes.Add(cec.CEC_DEVICE_TYPE_RECORDING_DEVICE)
            self.cecconfig.clientVersion = cec.LIBCEC_VERSION_CURRENT

        #----------------------------------------------------------------------
        def SetLogCallback(self, callback):
            self.cecconfig.SetLogCallback(callback)

        #----------------------------------------------------------------------
        def SetKeyPressCallback(self, callback):
            self.cecconfig.SetKeyPressCallback(callback)

        #----------------------------------------------------------------------       
        def DetectAdapter(self):
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

        #----------------------------------------------------------------------     
        def InitLibCec(self):
            # initialise libCEC
            self.lib = cec.ICECAdapter.Create(self.cecconfig)
            # print libCEC version and compilation information
            print("libCEC version " + self.lib.VersionToString(
                self.cecconfig.serverVersion) + " loaded: " + self.lib.GetLibInfo())

            # search for adapters
            adapter = self.DetectAdapter()
            if adapter == None:
                logger.error("No adapters found")
            else:
                if self.lib.Open(adapter):
                    logger.info("cec connection opened")
                else:
                    logger.error("failed to open a connection to the CEC adapter")

        #----------------------------------------------------------------------
        def ProcessCommandSelf(self):
            # display the addresses controlled by libCEC
            addresses = self.lib.GetLogicalAddresses()
            strOut = "Addresses controlled by libCEC: "
            x = 0
            notFirst = False
            while x < 15:
                if addresses.IsSet(x):
                    if notFirst:
                        strOut += ", "
                    strOut += self.lib.LogicalAddressToString(x)
                    if self.lib.IsActiveSource(x):
                        strOut += " (*)"
                    notFirst = True
                x += 1
            print(strOut)

        #----------------------------------------------------------------------
        def ProcessCommandActiveSource(self):
            # send an active source message
            self.lib.SetActiveSource()

        #----------------------------------------------------------------------
        def ProcessCommandStandby(self):
            # send a standby command
            self.lib.StandbyDevices(cec.CECDEVICE_BROADCAST)

        #----------------------------------------------------------------------
        def PowerOnTV(self):
            # send a standby command
            self.lib.PowerOnDevices(cec.CECDEVICE_TV)

        #----------------------------------------------------------------------
        def ProcessCommandTx(self, data):
            # send a custom command
            cmd = self.lib.CommandFromString(data)
            print("transmit " + data)
            if self.lib.Transmit(cmd):
                print("command sent")
            else:
                print("failed to send command")

        #----------------------------------------------------------------------
        def ProcessCommandScan(self):
            # scan the bus and display devices that were found
            print("requesting CEC bus information ...")
            strLog = "CEC bus information\n===================\n"
            addresses = self.lib.GetActiveDevices()
            activeSource = self.lib.GetActiveSource()
            x = 0
            while x < 15:
                if addresses.IsSet(x):
                    vendorId = self.lib.GetDeviceVendorId(x)
                    physicalAddress = self.lib.GetDevicePhysicalAddress(x)
                    active = self.lib.IsActiveSource(x)
                    cecVersion = self.lib.GetDeviceCecVersion(x)
                    power = self.lib.GetDevicePowerStatus(x)
                    osdName = self.lib.GetDeviceOSDName(x)
                    strLog += "device #" + str(x) + ": " + self.lib.LogicalAddressToString(x) + "\n"
                    strLog += "address:       " + str(physicalAddress) + "\n"
                    strLog += "active source: " + str(active) + "\n"
                    strLog += "vendor:        " + self.lib.VendorIdToString(vendorId) + "\n"
                    strLog += "CEC version:   " + self.lib.CecVersionToString(cecVersion) + "\n"
                    strLog += "OSD name:      " + osdName + "\n"
                    strLog += "power status:  " + self.lib.PowerStatusToString(power) + "\n\n\n"
                x += 1
            print(strLog)

        #----------------------------------------------------------------------
        def LogCallback(self, level, time, message):
            # logging callback
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

        #----------------------------------------------------------------------
        def KeyPressCallback(self, key, duration):
            # key press callback
            print("[key pressed] " + str(key))
            return 0

        #----------------------------------------------------------------------
        def __init__(self):
            self.SetConfiguration()

            
from celery import Task

class tv_power(Task):
    def __init__(self):
        if cec:
            self.ceclib = pyCecClient()

            # initialise libCEC and enter the main loop
            self.ceclib.InitLibCec()
#             self.ceclib.SetLogCallback(self.ceclib.LogCallback)

    #----------------------------------------------------------------------
    def run(self, on):
        log = "Received: %s" % str(on)
        logger.info(log)
        # self.last_message = time.time() # can use it for monitoring later on

        if cec:
            if on:
                self.ceclib.PowerOnTV()
                self.ceclib.ProcessCommandActiveSource()
            else:
                self.ceclib.ProcessCommandStandby()

        return log

