import time
import threading
import os
import glob
import commands
import re
import struct
import ctypes
import socket
import SocketServer
import BaseHTTPServer

the_report_period = 10
timezone = 7200
http_port = 8100

PAGE_CHARGERS = \
"""
<!DOCTYPE html>
<html>
<body>
    <h1> Haifa local time: {} </h1>
    <h1> Nearby chargers: </h1>
    <h3> - Name: {} Charge level: {} (Vout: {} V)</h3>
</body>
</html>
"""

globals()["g_window_voltage"] = 0.0
globals()["g_count _of_power_meters"] = 0.0
globals()["g_window_voltage"] = 0.0
globals()["g_ac_voltage"] = 0.0
globals()["g_ac_current"] = 0.0

class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def requestline(self):
        return 1

    def request_version(self):
        return 'HTTP/5.0'

    def handle(self):

        print("handle request request")
        the_page = PAGE_CHARGERS.format(time.ctime(int(time.time()+timezone)),
                    "bedroom north", "[||||||||||||  ]", globals()["g_window_voltage"])

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(the_page)))
        self.send_header("refresh", str(the_report_period))
        self.request.send(the_page)
        self.end_headers()



class NETTYPE:
    LAN = 1
    WLAN = 2
    CELL = 3

class DataServerHTTP :
    _stop_server = False
    _main_thread = None
    _nettype = NETTYPE.LAN

    def _HTTPThread(self):
        IP = "1.2.2.201"
        print("http server started at " + IP + ":" + str(http_port))
        while (self._stop_server == False):
            self._http_srv = BaseHTTPServer.HTTPServer((IP, http_port),HTTPHandler)
            self._http_srv.rbufsize = -1
            self._http_srv.wbufsize = 100000000
            try:
                self._http_srv.handle_request()
            except Exception as e:
                pass
            self._http_srv.socket.close()
        print("http server finished")

    def start(self):
        self._main_thread = threading.Thread(target=self._HTTPThread)
        self._main_thread.start()

    def stop(self):
        self._stop_server=True
        self._http_srv.socket.close()


class energy_server():
    _thread = None
    _stop_requested = False

    _CtrlPort = 8200

    def __init__(self, report_period = the_report_period):
        self._IPAddr = "1.2.2.201"
	self._CtrlPort = 8200
	self._clients = {}
	self._srv_soc = None
	self._lock = threading.Lock()

    def start(self):
        self._stop_requested = False
        self._listen_thread = threading.Thread(target=self._listen_thread)
	self._listen_thread.start()
        self._read_thread = threading.Thread(target=self._read_thread)
        self._read_thread.start()

    def _listen_thread(self):
        self._srv_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv_soc.bind((self._IPAddr, self._CtrlPort))
        self._srv_soc.listen(1)

        print("energy_server thread started at {}:{}".format(self._IPAddr,str(self._CtrlPort)))
        
	while(self._stop_requested != True):
		chan = None
        	addr = None
		try:
                	chan, addr = self._srv_soc.accept()
			chan.settimeout(1.0)
        	except Exception as e:
                	pass

		if chan != None :
        	        print("client connected: {}".format(addr))
			self._lock.acquire()
                	self._clients[addr] = chan
			self._lock.release()
        	globals()["g_count_of_chargers"] = len(self._clients)


    def _read_thread(self):
	while(self._stop_requested != True):
	    self._lock.acquire()
	    for addr, client in self._clients.iteritems():
		try:
			data = client.recv(1024)
			if(len(data) >0):
				print("{}: {}".format(addr, data))
			ds = data.split(":")

			globals()["g_window_voltage"] = ds[1]
		except Exception as e:
			pass
	    self._lock.release()	
            time.sleep(0.01)
        print("energy_server thread finished")

    def stop(self):
        if(self._thread == None):
            return
        self._stop_requested = True
        if(self._listen_thread.isAlive()):
            self._listen_thread.join();
        self._listen_thread = None

sm = energy_server()
sm.start()

srv = DataServerHTTP()
srv.start()
#.                       