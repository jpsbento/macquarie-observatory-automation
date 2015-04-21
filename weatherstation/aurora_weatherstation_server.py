#****************************************************************************#
#               Code to open and read from the weather station               #
#****************************************************************************#

import serial
import sys
import select
import string, time
from datetime import datetime

#Open port 0 at "9600,8,N,1", timeout of 5 seconds
try: 
	ser = serial.Serial('/dev/ttyUSB0',9600,timeout=10)  #open first serial port
	print ser.portstr       #check which port was really used
except Exception: 
	ser = serial.Serial('/dev/ttyUSB1',9600,timeout=10)  #open first serial port
	print ser.portstr
	
class WeatherstationServer:


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

	def cmd_safe(self, the_command):
		'''Returns a 1 if it is safe to open the dome slits, and returns a zero otherwise.'''
		return str(self.slitvariable)


#************************* End of user commands ********************************#

#Background task that reads data from the weather station and records it to a file

	#definition to read from the serial port
	#I am assuming that only the rainsensortemp and heaterPWM are in hexadecimal
	#I'll know for sure when the aurora guys email me back
	def main(self):
		self.data = str.split(ser.readline(),',')
		self.sequence = self.data[2]
		self.tempair = float(self.data[3])/100.0 #sensor temperature
		self.tempsky = float(self.data[4])/100.0 #sky temperature
		self.clarity = float(self.data[5])/100.0 #is the difference between the air temperature and the sky temperature
		self.light = float(self.data[6])/10.0 #Non calibrated value, normal range of about 0 to 30
		self.rain = float(self.data[7])/10.0  #Non calibrated value, normal range of about 0 to 30
		self.alertstate = self.data[10]
		alertdigit = int(self.alertstate, 16)

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

		if ((alertdigit >> 7) & 1): message += ' energised.'
		else: message += ' not energised.'					

		self.slitvariable = cloudvariable*rainvariable*lightvariable #if = 1, it's safe for slits to be open! Unsafe otherwise.

		if self.slitvariable: message+=' Safe for dome to open.'
		else: message+=' NOT safe for dome to open.************' 
		self.log(message+' '+self.cmd_tempair('dummy'))

		return

	#definition to log the output, stores all data in a file
	def log(self,message):
		f = open('weatherlog.txt','a')
		f.write(str(time.time())+" "+str(datetime.now())+" "+str(message)+'\n')
		f.close()
                h = open('weatherlog_detailed.txt','a')
                h.write("Clarity: "+str(self.clarity)+" Light: "+str(self.light)+" Rain: "+str(self.rain)+" Air temperature: "+str(self.tempair)+" Sky temperature: "+str(self.tempsky)+"\n")
                h.close()


