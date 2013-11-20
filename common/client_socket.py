import sys
import string
import select
import socket
from datetime import datetime

class ClientSocket:

	def __init__(self,device,telescope_type):
		#Set up the class properties "server", "input", "hardware_name" and "hardware_object"
		self.device = device
		try: devicefile = open('../common/device_list.txt')
		except Exception: print 'ERROR: file "device_list.txt" not found'
		device_list = devicefile.readlines()
		devicefile.close()
		IP = ''
		Port = ''
		IP_column = ''
		Port_column = ''
		if device_list[0][0] == '#':
			items = str.split(device_list[0])
			for i in range(0, len(items)):
				if items[i] == telescope_type+'IP': IP_column = i
				if items[i] == 'Port': Port_column = i
				#print items[i]
		else: return 'ERROR 1'
		if IP_column == '' or Port_column == '': print 'ERROR: Device file with unknown format'
		for line in device_list:
			item = str.split(line)
			if item[0][0] != '#' and device == item[0]:
				try:
					IP = item[IP_column]
					Port = int(item[Port_column])
				except Exception: print 'ERROR: Unable to set IP and Port columns'
		ADS = (IP,Port)
		try:
			self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.client.connect(ADS)
			self.client.settimeout(600)
			#self.client.setsockopt(1, 2, 1)
			self.client.setsockopt(6, 1, 1)
		except Exception: print 'ERROR: Could not connect to server responsible for '+self.device+'. Please check that the server is running.'



	def send_command(self, command):
#sends a command to the device server and waits for a response
		try: self.client.send(command)
		except Exception: return 'Error sending command, connection likely lost.'
		try: return self.client.recv(15000)
		except Exception: return 'Error receiving response'




