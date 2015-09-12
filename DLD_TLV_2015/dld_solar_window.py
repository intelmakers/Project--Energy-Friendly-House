from ABE_ADCPi import ADCPi
from ABE_helpers import ABEHelpers
import time
import threading
import os
import commands
import re
import struct
import ctypes
import socket

the_report_period = 5

class dld_solar_window():
    _channel = 0
    _report_period = 5

    _thread = None
    _stop_requested = False

    _srv_ip_addr = "1.2.2.201"
    _srv_port = 8200


    def __init__(self, channel = 0, report_period = the_report_period):
        self._channel = channel
        self._report_period = report_period
        self._i2c_helper = ABEHelpers()
        self._bus = self._i2c_helper.get_smbus()
        self._adc = ADCPi(self._bus, 0x68, 0x69, 12)

    def Start(self):
        self._stop_requested = False
        self._thread = threading.Thread(target=self.SamplingThread)
        self._thread.start()
        print("sampling thread initialized")
        
    def SamplingThread(self):
        print("sampling thread started")

        mc_socket = None
        
        time_last_report = time.time()
        connected = False
        while(self._stop_requested != True):
            if(connected == False):
                try:
                    #time.sleep(5)
                    mc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    mc_socket.connect((self._srv_ip_addr, self._srv_port))
                    print("connected")
                    time.sleep(1)
                except Exception as e:
                    connected = False
                    continue

            time_now = time.time()
            voltage = self._adc.read_voltage(self._channel)

            try:
                mc_socket.send("Vout:%02f\n" % (voltage))
                print("Vout:%02f\n" % (voltage))
            except Exception as e:
                connected = False
            time.sleep(5.0)

    def Stop(self):
        if(self._thread == None):
            return
        self._stop_requested = True
        if(self._thread.isAlive()):
            self._thread.join();
        self._thread = None

sm = dld_solar_window()
sm.Start()
