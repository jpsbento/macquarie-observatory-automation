import sys
import string
import select
import socket
from datetime import datetime

class ClientSocket:

	def __init__(self,device,telescope_type):
#Set up the class properties "server", "input", "hardware_name" and "hardware_object"
		self.device = device
		try: devicefile = open('device_list.txt')
		except Exception: return 'ERROR file "device_list.txt" not found'
		device_list = devicefile.readlines()
		IP = ''
		Port = ''
		IP_column = 1 # which IP column do we want in Device list?
		if telescope_type == 'bisquemount': IP_column = 1  # The bisquemount IP is recorded first in device_list.txt
		elif telescope_type == 'meademount': IP_column = 2 # The meademount IP is recorded second in device_list.txt
		else: 
			print 'ERROR telescope not defined in list'
			return
		for line in device_list:
			item = str.split(line)
			if item[0][0] != '#' and device == item[0]:
				try:
					IP = item[IP_column]
					Port = int(item[3])
				except Exception: print 'ERROR IN DEVICE_LIST.TXT'
				break
		ADS = (IP,Port)
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect(ADS)
		self.client.settimeout(600)
		self.client.setsockopt(1, 2, 1)
		self.client.setsockopt(6, 1, 1)



	def send_command(self, command):
#sends a command to the device server and waits for a response
		self.client.send(command)
		try: return self.client.recv(1024)
		except Exception: return




