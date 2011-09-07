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
#import binascii

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
		alert = [1,1,1,1,1,1,1,1]
		self.data = str.split(ser.readline(),',')
		self.sequence = self.data[2]
		self.tempair = float(self.data[3])/100
		self.tempsky = float(self.data[4])/100
		self.clarity = float(self.data[5])/100
		self.light = self.data[6]
		self.rain = self.data[7]
		self.rainsensortemp = self.data[8]  #hexadecimal, maybe..
		self.rainsensortemp = int(self.rainsensortemp, 16)
		self.heaterPWM = self.data[9]       #hexadecimal, maybe..
		self.heaterPWM = int(self.heaterPWM, 16)
		self.alertstate = self.data[10]
		print self.alertstate	
		temp = int(self.alertstate, 16)
		print temp
		temp = bin(temp)
		print temp
		alert = list(temp)
		del alert[0]
		del alert[0]
		while len(alert) < 8:
			alert.insert(0, '0')
		#alert.reverse()
		print alert
		#alert = [0,0,0,0,0,0,0,0]
		#temp = list(self.alertstate)
		#first = int(temp[0], 16)
		#second = int(temp[1], 16)
		#first = bin(first)
		#second = bin(second)
		#first = list(first)
		#del first[0]
		#del first[0]
		#print first
		#while len(first) < 4:
		#	first.insert(0, '0')
		#print first
		#second = list(second)
		#del second[0]
		#del second[0]
		#print second
		#while len(second) < 4:
		#	second.insert(0, '0')
		#print second
		#alert = first + second

		#print alert	

		if int(alert[0]) == 0 and int(alert[1]) == 0:
			print 'clear, ',
		if int(alert[0]) == 1 and int(alert[1]) == 0:
			print 'unused, ',
		if int(alert[0]) == 0 and int(alert[1]) == 1:
			print 'cloudy, ',
		if int(alert[0]) == 1 and int(alert[1]) == 1:
			print 'very cloudy, ',
		if int(alert[2]) == 0 and int(alert[3]) == 0:
			print 'dry, ',
		if int(alert[2]) == 1 and int(alert[3]) == 0:
			print 'unused, ',
		if int(alert[2]) == 0 and int(alert[3]) == 1:
			print 'wet, ',
		if int(alert[2]) == 1 and int(alert[3]) == 1:
			print 'very wet, ',
		if int(alert[4]) == 0 and int(alert[5]) == 0:
			print 'dark, ',
		if int(alert[4]) == 1 and int(alert[5]) == 0:
			print 'unused, ',
		if int(alert[4]) == 0 and int(alert[5]) == 1:
			print 'light, ',
		if int(alert[4]) == 1 and int(alert[5]) == 1:
			print 'very light, ',
		if int(alert[7]) == 0:
			print 'relay safe'
		if int(alert[7]) == 1:
			print 'relay unsafe'












			
		#print alert
		#self.alertstate = binascii.a2b_hex(self.alertstate)
		message = str(self.sequence)+" "+str(self.tempair)+" "+str(self.tempsky)+" "+str(self.clarity)+" "+str(self.light)+" "+str(self.rain)+" "+str(self.rainsensortemp)+" "+str(self.heaterPWM)+" "+str(self.alertstate)
		self.log(message)
		#print self.alertstate
		return

	#definition to log the output, stores all data in a file
	def log(self,message):
		f.write(str(datetime.now())+" "+str(message)+'\n'),

	#def a2bits(self,chars):
	#	"Convert a string to its bits representation as a string of 0's and 1's"
	#	return bin(reduce(lambda x, y : (x<<8)+y, (ord(c) for c in chars), 1))[3:]

	#def Denary2Binary(self,n):
	#	'''convert denary integer n to binary string bStr'''
	#	bStr = ''
	#	if n < 0: raise ValueError, "must be a positive integer"
	#	if n == 0: return '0'
	#	while n > 0:
	#		bStr = str(n % 2) + bStr
	#		n = n >> 1
	#	return bStr


