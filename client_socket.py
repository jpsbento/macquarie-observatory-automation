import sys
import string
import select
import socket
from datetime import datetime

class ClientSocket:

	def __init__(self,device):
#Set up the class properties "server", "input", "hardware_name" and "hardware_object"
		self.device = device
		devicefile = open('device_list.txt')
		device_list = devicefile.readlines()
		IP = ''
		Port = ''
			for item in device_list:
				if device in item:
					IP = item[1]
					Port = item[2]
		ADS = (IP,Port)
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect(ADS)
		self.client.settimeout(600)


	def command_send(self, command):
#sends a command to the device server and waits for a response
		self.client.send(command)
		return self.client.recv(1024)

