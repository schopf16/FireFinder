# -*- coding: utf-8 -*-

try:
    import cec
except ImportError:
    cec = None

import os
import time
import subprocess

from enum import Enum
from celery import Task
from threading import Timer
from firefinder.util_logger import Logger


class OutputState(Enum):
    on  = True
    off = False


class PyCecClient:

    def __init__(self, logger=None):
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\MonitorOutputDriver.log")
        
        if cec:
            self.cec_config = cec.libcec_configuration()
            self.set_log_callback(self.log_callback)
            self.set_configuration()
        else:
            self.cec_config = None

        self.lib = dict()
        
    # ----------------------------------------------------------------------
    def set_configuration(self):
        if self.cec_config:
            # create a new libcec_configuration
            self.cec_config.strDeviceName = "FireFinder"
            self.cec_config.bActivateSource = 0
            self.cec_config.deviceTypes.Add(cec.CEC_DEVICE_TYPE_RECORDING_DEVICE)
            self.cec_config.clientVersion = cec.LIBCEC_VERSION_CURRENT

    # ----------------------------------------------------------------------
    def set_log_callback(self, callback):
        self.cec_config.set_log_callback(callback)

    # ----------------------------------------------------------------------
    def set_key_press_callback(self, callback):
        self.cec_config.set_key_press_callback(callback)

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
        if cec:
            # initialise libCEC
            self.lib = cec.ICECAdapter.Create(self.cec_config)
            # print libCEC version and compilation information
            print("libCEC version " + self.lib.VersionToString(
                self.cec_config.serverVersion) + " loaded: " + self.lib.GetLibInfo())

            # search for adapters
            adapter = self.detect_adapter()
            if adapter is None:
                self.logger.error("No adapters found")
            else:
                if self.lib.Open(adapter):
                    self.logger.info("cec connection opened")
                else:
                    self.logger.error("failed to open a connection to the CEC adapter")

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
        if cec:
            if level == cec.CEC_LOG_ERROR:
                self.logger.error(message)
            elif level == cec.CEC_LOG_WARNING:
                self.logger.warning(message)
            elif level == cec.CEC_LOG_NOTICE:
                self.logger.info(message)
            elif level == cec.CEC_LOG_TRAFFIC:
                self.logger.info(message)
            elif level == cec.CEC_LOG_DEBUG:
                self.logger.debug(message)
        else:
            self.logger.info(message)

        return 0

    # ----------------------------------------------------------------------
    @staticmethod
    def key_press_callback(key, duration):
        # key press callback
        print("[key pressed] " + str(key))
        return 0

    # ----------------------------------------------------------------------


class TvPower(Task):
    def __init__(self, hdmi_port_nbr=1, logger=None):
        self.logger = logger if logger is not None else Logger(verbose=True, file_path=".\\TvPower.log")

        self.hdmi_televison_port_number = hdmi_port_nbr
        
        if cec:
            self.ceclib = PyCecClient()

            # initialise libCEC and enter the main loop
            self.ceclib.init_lib_cec()
        else:
            my_dir = os.path.split(os.path.realpath(__file__))[0]
            self.path_to_cec_client = os.path.join(my_dir, "..", "library", "cec-client.exe")

    def run(self, on):
        log = "Received: {}".format(on)
        self.logger.info(log)

        if cec:
            if on:
                print("switching tv on now")
                self.ceclib.power_on_television()
                self.ceclib.process_command_active_source()
            else:
                print("switching tv off now")
                self.ceclib.process_command_standby()
        else:
            if on:
                subprocess.call(["echo", "as", "|", self.path_to_cec_client, '-s', '-p', str(self.hdmi_televison_port_number)],
                                shell=True, timeout=30)
            else:
                subprocess.call(["echo", "standby", "0", "|", self.path_to_cec_client, "-s", "-p", str(self.hdmi_televison_port_number)],
                                shell=True, timeout=30)

        return log
    

class RepeatingTimer(object):
    def __init__(self, interval, f, *args, **kwargs):
        self.interval = interval
        self.f        = f
        self.args     = args
        self.kwargs   = kwargs
        self.timer    = None

    def callback(self):
        self.f(*self.args, **self.kwargs)
        self.start()

    def cancel(self):
        # increase robustness
        if self.is_alive():
            self.timer.cancel()

    def start(self):
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()

    def is_alive(self):
        if self.timer is None:
            return False
        else:
            return self.timer.is_alive()

    def join(self, timeout):
        if self.timer is None:
            return
        else:
            return self.timer.join(timeout)
        
        
class GraphicOutputDriver(object):
    def __init__(self, logger=None, cec_enable=False, hdmi_port_nbr=1, standby_enable=False, bypass_tv_power_save=0):
        self.logger               = logger if logger is not None else Logger(verbose=True, file_path=".\\MonitorOutputDriver.log")
        self.cec_enable           = cec_enable
        self.hdmi_port_number     = hdmi_port_nbr
        self.standby_enable       = standby_enable
        self.bypass_tv_power_save = bypass_tv_power_save

        self._current_graphic_output = OutputState.on
        self._current_television_state = OutputState.off

        # Create television object to drive TV
        self.tv_obj = TvPower(hdmi_port_nbr=hdmi_port_nbr)
        
        # Try to disable power saving
        if os.name == 'posix':
            self.logger.debug("Try to disable power save on unix system")
            try:    
                subprocess.call(["xset", "s", "noblank"])
                subprocess.call(["xset", "s", "noblank"])
                subprocess.call(["xset", "-dpms"])
            except Exception as e: 
                self.logger.error(f"Failed disabling power savings on OS posix with '{e.args}'")

        elif os.name == 'nt':
            self.logger.debug("Try to disable power save on windows system")
            try:    
                subprocess.call(["powercfg.exe", "-change", "-monitor-timeout-ac", "0"])
                subprocess.call(["powercfg.exe", "-change", "-disk-timeout-ac", "0"])
                subprocess.call(["powercfg.exe", "-change", "-standby-timeout-ac", "0"])
                subprocess.call(["powercfg.exe", "-change", "-hibernate-timeout-ac", "0"])
            except Exception as e:
                self.logger.error(f"Failed disabling power savings on OS Windows with '{e.args}'")

        # If user enable automatic TV reboot to prevent it from power save
        # launch a separate thread to handle this asynchron from any ini-commands
        self.reboot_tv_obj = None
        if self.bypass_tv_power_save != 0:
            self.logger.debug("Load timer for reboot TV")
            self.reboot_tv_obj = RepeatingTimer(self.bypass_tv_power_save * 60, self._reboot_television_over_cec)

    def get_visual(self):
        return_value = OutputState.off

        """
        Return the status of the graphical output. If CEC is enabled, both
        (HDMI output and television on) has to be enabled, otherwise 'Off'
        will returned if at least on is disabled.
        """
        if self.cec_enable:
            if self._current_graphic_output.value and self._current_television_state.value:
                return_value = OutputState.on
        else:
            return_value = self._current_graphic_output

        return return_value

    def set_visual(self, state=OutputState.on):
        """
        Activate or deactivate the graphical output to force monitor to
        standby. If CEC is enabled, the television is triggered too,
        otherwise only the graphic output is driven.
        :param state: Can be on or off
        """
        if self.reboot_tv_obj:
            if state.value:
                # Start timer only if it's not alive, otherwise a
                # new screen would restart the timer, but the TV
                # doesn't trigger the screen, only power-changes
                if self.reboot_tv_obj.is_alive() is not True:
                    self.reboot_tv_obj.start()
            else:
                if self.reboot_tv_obj.is_alive() is True:
                    self.reboot_tv_obj.cancel()
                    self.reboot_tv_obj.join(20)  # wait to kill thread

        self._switch_graphic_output(new_state=state)

    def set_power_off(self):
        self.set_visual('Off')

    def _switch_graphic_output(self, new_state=OutputState.on):

        if new_state.value:
            '''
            ORDER:
            First enable the HDMI port and the switch the TV on if
            available. If done otherwise, the cec command can't be
            transmitted over a deactivated HDMI port.
            '''
            if self.standby_enable and (os.name == 'posix'):
                if self._current_graphic_output != new_state:
                    try:
                        subprocess.call(["/opt/vc/bin/tvservice", "-p"])
                        subprocess.call(["sudo", "/bin/chvt", "6"])
                        subprocess.call(["sudo", "/bin/chvt", "7"])
                    except Exception as e:
                        self.logger.error(f"Failed switch on display on OS posix with '{e.args}'")
                    self._current_graphic_output = new_state

            if self.cec_enable:
                # Always enable TV. The user could switch of TV manually
                self.logger.info("Switch TV on")
                self.tv_obj.run(True)
        else:
            '''
            ORDER:
            First switch off the TV with the CEC commandos if available
            and then disable the HDMI port. If done otherwise, the
            cec command can't be transmitted over a deactivate HDMI
            port.
            '''
            if self.cec_enable:
                self.logger.info("Switch TV off")
                self.tv_obj.run(False)

            if self.standby_enable and (os.name == 'posix'):
                if self._current_graphic_output != new_state:
                    try:
                        subprocess.call(["/opt/vc/bin/tvservice", "-o"])
                    except Exception as e:
                        self.logger.error(f"Failed switch off display on OS posix with '{e.args}'")
                    self._current_graphic_output = new_state

        if (self.cec_enable is False) and (self.standby_enable is False):
            self.logger.warning("CEC and Standby is disabled. Monitor can't switch on or off")

    # ----------------------------------------------------------------------
    def _reboot_television_over_cec(self):
        self.logger.debug("keep alive TV requested")

        self._switch_graphic_output('Off')
        time.sleep(10)
        self._switch_graphic_output('On')
