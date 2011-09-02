#****************************************************************************#
#               Code to open and read from the weather station               #
#****************************************************************************#

import serial
import sys
import select
import string
from datetime import datetime

#Open port 0 at "9600,8,N,1", no timeout
ser = serial.Serial(0)  #open first serial port
print ser.portstr       #check which port was really used

f = open('weatherdata.dat','a')

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
	rainsensortemp = 0
	heaterPWM = 0
	alertstate = 0

#A list of user commands:

	def cmd_clarity(self,the_command):
		'''Returns the clarity reading from the weather station.'''
		return str(self.clarity)

	def cmd_light(self,the_command):
		'''Returns the light reading from the weather station.'''
		return str(self.light)

	def cmd_rain(self,the_command):
		'''Returns the rain reading from the weather station.'''
		return str(self.rain)

	def cmd_tempair(self,the_command):
		'''Returns the air temperature reading from the weather station.'''
		return str(self.tempair)

	def cmd_tempsky(self,the_command):
		'''Returns the sky temperature reading from the weather station.'''
		return str(self.tempsky)

	def cmd_rainsensor(self,the_command):
		'''Returns the rain sensor temperature reading from the weather station.'''
		return str(self,rainsensortemp)

	def cmd_heaterPWM(self,the_command):
		'''Returns the heater PWM reading from the weather station.'''
		return str(self,heaterPWM)

	def cmd_status(self,the_command):
		'''Returns all the latest data output from the weather station.'''
		return "Clarity: "+str(self.clarity)+"\nLight: "+str(self.light)+"\nRain: "+str(self.rain)+"\nAir temperature: "+str(self.tempair)+"\nSky temperature: "+str(self.tempsky)+"\nRain sensor temperature: "+str(self.rainsensortemp)+"\nHeaterPWM: "+str(self.heaterPWM)



#************************* End of user commands ********************************#

#Background task that reads data from the weather station and records it to a file

	#definition to read from the serial port
	#I am assuming that only the rainsensortemp and heaterPWM are in hexadecimal
	#I'll know for sure when the aurora guys email me back
	def serialread(self):
		
		self.data = str.split(ser.readline(),',')
		self.sequence = self.data[2]
		self.tempair = self.data[3]
		self.tempsky = self.data[4]
		self.clarity = self.data[5]
		self.light = self.data[6]
		self.rain = self.data[7]
		self.rainsensortemp = self.data[8]  #hexadecimal, maybe..
		self.rainsensortemp = int(self.rainsensortemp, 16)
		self.heaterPWM = self.data[9]       #hexadecimal, maybe..
		self.heaterPWM = int(self.heaterPWM, 16)
		self.alertstate = self.data[10]
		message = str(self.sequence)+" "+str(self.tempair)+" "+str(self.tempsky)+" "+str(self.clarity)+" "+str(self.light)+" "+str(self.rain)+" "+str(self.rainsensortemp)+" "+str(self.heaterPWM)+" "+str(self.alertstate)
		self.log(message)
		return

	#definition to log the output, stores all data in a file
	def log(self,message):
		f.write(str(datetime.now())+" "+str(message)+'\n'),


