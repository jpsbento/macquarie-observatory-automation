#****************************************************************************#
#               Code to open and read from the weather station               #
#****************************************************************************#

import serial
import sys
#if sys.version_info[0] >= 3:
#	bin = "{0:#0b}".format
#	from functools import reduce
import select
import string
from datetime import datetime
from socket import *
#import binascii

#Open port 0 at "9600,8,N,1", timeout of 5 seconds
ser = serial.Serial(0)  #open first serial port
print ser.portstr       #check which port was really used


class WeatherstationServer:

	IP = ''
	PORT = 23460
	ADS = (IP, PORT)

	server = socket(AF_INET, SOCK_STREAM)
	server.bind(ADS)
	server.setblocking(0)
	server.listen(5) #will allow 5 clients to connect with server
	#server.setsockopt(1, 2, 1)

	CLIENTS = []
	input = [server, sys.stdin]
#Global variables

	data = []
	running = 1
	sequence = 0
	tempair = 0
	tempsky = 0
	clarity = 0
	light = 0
	rain = 0
	alertstate = 0
	slitvariable = 0 #This is the variable to send to the slits to tell them whether
			 #it's okay to be open or not. 0 to close, 1 to open.

#A list of user commands:

	def cmd_clarity(self,the_command):
		'''Returns the clarity reading from the weather station. This is the difference between 
		the air temperature and the sky temperature.'''
		return str(self.clarity)

	def cmd_light(self,the_command):
		'''Returns the light reading from the weather station. Uncalibrated value, normal range: 0 to 30.'''
		return str(self.light)

	def cmd_rain(self,the_command):
		'''Returns the rain reading from the weather station. Uncalibrated value, normal range: 0 to 30.'''
		return str(self.rain)

	def cmd_tempair(self,the_command):
		'''Returns the air temperature reading from the weather station. Units are in degrees C.'''
		return str(self.tempair)

	def cmd_tempsky(self,the_command):
		'''Returns the sky temperature reading from the weather station. Units are in degrees C.'''
		return str(self.tempsky)

	def cmd_status(self,the_command):
		'''Returns all the latest data output from the weather station.'''
		return "Clarity: "+str(self.clarity)+"\nLight: "+str(self.light)+"\nRain: "+str(self.rain)+"\nAir temperature: "+str(self.tempair)+"\nSky temperature: "+str(self.tempsky)



#************************* End of user commands ********************************#

#Background task that reads data from the weather station and records it to a file

	#definition to read from the serial port
	#I am assuming that only the rainsensortemp and heaterPWM are in hexadecimal
	#I'll know for sure when the aurora guys email me back
	def serialread(self):
		self.data = str.split(ser.readline(),',')
		self.sequence = self.data[2]
		self.tempair = float(self.data[3])/100.0 #sensor temperature
		self.tempsky = float(self.data[4])/100.0 #sky temperature
		self.clarity = float(self.data[5])/100.0 #is the difference between the air temperature and the sky temperature
		self.light = float(self.data[6])/10.0 #Non calibrated value, normal range of about 0 to 30
		self.rain = float(self.data[7])/10.0  #Non calibrated value, normal range of about 0 to 30
		self.alertstate = self.data[10]
		alertdigit = int(self.alertstate, 16)
		#print self.alertstate
		#print alertdigit

		#Initally set the alert variable to 0 (= Unsafe)
		cloudvariable = 0 #this will be set to 1 if it is clear
		rainvariable = 0  #this will be set to 1 if it is dry
		lightvariable = 0 #this will be set to 1 if it is dark
		message = ''
		if ((alertdigit >> 0) & 1) and ((alertdigit >> 1) & 1): message += 'Clear,'; cloudvariable = 1
		elif ((alertdigit >> 1) & 1): message += 'Unused,' #will never be printed
		elif ((alertdigit >> 0) & 1): message += 'Cloudy,'
		else: message += 'Very cloudy,'

		if ((alertdigit >> 2) & 1) and ((alertdigit >> 3) & 1): message += ' unused,' #will never be printed
		elif ((alertdigit >> 3) & 1): message += ' dry,'; rainvariable = 1
		elif ((alertdigit >> 2) & 1): message += ' very wet,'
		else: message += ' wet,'

		if ((alertdigit >> 4) & 1) and ((alertdigit >> 5) & 1): message += ' dark,'; lightvariable = 1
		elif ((alertdigit >> 5) & 1): message += ' unused,' #will never be printed
		elif ((alertdigit >> 4) & 1): message += ' light,'
		else: message += ' very light,'

		if ((alertdigit >> 7) & 1): message += ' energised, safe for dome to open.' #I think this relay unsafe business
		else: message += ' not energised.'				#is whether it is safe to observe
									#it's triggered by certain factors


		#When the electronics for the slits is actually in place we can send the slits this value at a regular interval
		#to tell it whether it is safe to stay open or not. If at any point the slits lose contact with the weather-station
		#they should be configured to automatically close.
		self.slitvariable = cloudvariable*rainvariable*lightvariable #if = 1, it's safe for slits to be open! Unsafe otherwise.

		print message
		print str(cloudvariable)+' '+str(rainvariable)+' '+str(lightvariable)+' '+str(self.slitvariable)
		print str(self.sequence)+" "+str(self.tempair)+" "+str(self.tempsky)+" "+str(self.clarity)+" "+str(self.light)+" "+str(self.rain)+" "+str(self.alertstate)
		self.log(message)

		return

	#definition to log the output, stores all data in a file
	def log(self,message):
		f = open('weatherlog.txt','a')
		f.write(str(datetime.now())+" "+str(message)+'\n'),
		f.close()


	def socket_funct(self):
		for s in self.input:
			if s == self.server:
				#handle server socket
				try:
					client, address = self.server.accept()
					client.setblocking(0)
					self.input.append(client)
					self.CLIENTS.append(client)
					self.input[-1].send(str(self.slitvariable))
					return 
				except IOError:
					#print 'broken'
					return 
			elif s == sys.stdin:
				#handle standard input
				junk = string.split(sys.stdin.readline())
				if junk[0] == "quit" or junk[0] == "exit" or junk[0] == "bye":
					log("Manually shut down. Goodbye.")
					running = 0 #so if we type anything into the server it will quit.
					return 
				else:
					log('Error, command not expected, type "exit" or "quit" to exit server.')
					return 
			else:
				#handle all other sockets
				data = str(s.recv(1024))
				if data:
					return data
				else:
					s.close()
					input.remove(s)
					return 



