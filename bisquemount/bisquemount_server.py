#*************************************************************************#
#                    Code to control the Bisque mount                     #
#*************************************************************************#

import sys
import string
import select
import socket
from datetime import datetime
import time

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("10.72.26.145",3040))
#client_socket.settimeout(10)

class BisqueMountServer:

	def cmd_find(self,the_command):
		'''Will find an object in TheSky's Star chart and return data.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			obj = commands[1]
			linestoreplace = ['sky6StarChart.Find("object");\r\n']
			newlines = ['sky6StarChart.Find("'+obj+'");\r\n']
			if self.editscript('Find.template', 'Find.js', linestoreplace,newlines) == 0:
				script = self.readscript('Find.js')
				client_socket.send(script)
				return self.messages()
			else: return 'ERROR with files'
		else: return 'ERROR, invalid input.'

	def cmd_getTargetRaDec(self,the_command): #***************************
		'''Returns the RA and dec of the target.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			obj = commands[1]
			linestoreplace = ['var Target = "object";/*Parameterize*/\r\n']
			newlines = ['var Target = "'+obj+'";/*Parameterize*/\r\n']
			if self.editscript('GetTargetRaDec.template', 'GetTargetRaDec.js', linestoreplace,newlines) == 0:
				script = self.readscript('GetTargetRaDec.js')
				client_socket.send(script)
				return self.messages()
			else: return 'ERROR reading files'
		else: return 'ERROR, invalid input length'

	def cmd_mountGetRaDec(self,the_command):
		'''Gets the current RA and Dec of the mount.'''
		TheSkyXCommand = self.readscript('MountGetRaDec.js')
		client_socket.send(TheSkyXCommand)
		return self.messages()


	def cmd_moveTelescope(self, the_command):
		'''Will move the telescope by a specified amount. To move north, south, east, or west
		type ie 'moveTelescope north'. To move a specific Ra and Dec coordinate type:
		'moveTelescope 21 20' for example, where 21 is the  Ra and 20 is the Dec'''
		commands = str.split(the_command)
		if len(commands) == 3:
			dRa = commands[1]
			dDec = commands[2]
			linestoreplace = ['var TargetRA = RAtemp;\r\n','var TargetDec = Dectemp;\r\n']
			newlines = ['var TargetRA = "'+dRa+'";\r\n','var TargetDec = "'+dDec+'";\r\n']
			if self.is_float_try(dRa) and self.is_float_try(dDec):
				if self.editscript('MountGoto.template', 'MountGoto.js', linestoreplace,newlines) == 0:
					script = self.readscript('MountGoto.js')
					client_socket.send(script)
					return self.messages()
				else: return 'ERROR writing script'
			else: return 'ERROR invalid input'
		elif len(commands) == 2:
			script = ''
			if commands[1] == 'north': script = self.readscript('moveNorth.js')
			elif commands[1] == 'south': script = self.readscript('moveSouth.js')
			elif commands[1] == 'west': script = self.readscript('moveWest.js')
			elif commands[1] == 'east': script = self.readscript('moveEast.js')
			else: return 'ERROR invalid input'
			client_socket.send(script)
			return self.messages()
		else: return 'ERROR, invalid input'

	def cmd_findHome(self,the_command):
		script = self.readscript('FindHome.js')
		client_socket.send(script)
		return self.messages()

	def cmd_park(self,the_command):
		script = self.readscript('Park.js')
		client_socket.send(script)
		return self.messages()

	def cmd_s(self,the_command):
		'''Stops all telescope motion.'''
		script = self.readscript('moveStop.js')
		client_socket.send(script)
		return self.messages()

	def cmd_slewToRaDec(self,the_command):
		'''Will slew the telescope to the Ra and Dec put in.'''
		commands = str.split(the_command)
		if len(commands) == 3:
			dRa = commands[1]
			dDec = commands[2]
			linestoreplace = ['var TargetRa = Ratemp;\r\n','var TargetDec = Dectemp;\r\n']
			newlines = ['var TargetRa = "'+dRa+'";\r\n','var TargetDec = "'+dDec+'";\r\n']
			if self.is_float_try(dRa) and self.is_float_try(dDec):
				if self.editscript('SlewToRaDec.template', 'SlewToRaDec.js', linestoreplace,newlines) == 0:
					script = self.readscript('SlewToRaDec.js')
					client_socket.send(script)
					return self.messages()
				else: return "ERROR with files"
			else: return 'ERROR invalid input'
		else: return 'ERROR invalid input'

	def cmd_slewToAzAlt(self,the_command):
		'''Will slew the telescope to the Az and Alt put in.'''
		commands = str.split(the_command)
		if len(commands) == 3:
			dAz = commands[1]
			dAlt = commands[2]
			linestoreplace = ['var TargetAz = Aztemp;\r\n','var TargetAlt = Alttemp;\r\n']
			newlines = ['var TargetAz = "'+dAz+'";\r\n','var TargetAlt = "'+dAlt+'";\r\n']
			if self.is_float_try(dAz) and self.is_float_try(dAlt):
				if self.editscript('SlewToAzAlt.template', 'SlewToAzAlt.js', linestoreplace,newlines) == 0:
					script = self.readscript('SlewToAzAlt.js')
					client_socket.send(script)
					return self.messages()
				else: return "ERROR with files"
			else: return 'ERROR invalid input'
		else: return 'ERROR invalid input'



	def cmd_tracking(self,the_command):
		'''Turns tracking on or off and determines whether to use the sidereal time to set the tracking
		rate, or use a user input, input in form: 'tracking:on/off usesidereal:yes/no RaRate DecRate' ie if you
		wanted to turn tracking on and use sidereal rate input: 'on yes 0 0' to turn tracking on but set the rate
		to your own input put: 'on no 1.5 1.2'.'''
		commands = str.split(the_command)
		tracking = 0 #initially set tracking off
		usesidereal = 1 #intially set to use the sidereal time for tracking rates
		dRaRate = 0.0 #initally set ra tracking rate to 0
		dDecRate = 0.0 #initally set dec tracking rate to 0
		if len(commands) == 5:
			if commands[1] == 'on' or 'On': tracking = 1 #turn tracking on
			if commands[2] == 'no' or 'No': currentrates = 0 #use the current rates input by user
			if self.is_float_try(commands[3]) and self.is_float_try(commands[4]):
				dRaRate = commands[3]
				dDecRate = commands[4]
			else: return 'ERROR, invalid input'
			linestoreplace = ['\tsky6RASCOMTele.SetTracking(0,1,0,0);\r\n']
			newlines = ['\tsky6RASCOMTele.SetTracking('+str(tracking)+','+str(usesidereal)+','+str(dRaRate)+','+str(dDecRate)+');\r\n']
			if self.editscript('MountTracking.template', 'MountTracking.js', linestoreplace,newlines) == 0:
				script = self.readscript('MountTracking.js')
				client_socket.send(script)
				return self.messages()
			else: return 'ERROR writing script'
		else: return 'ERROR, invalid input'
				

	def cmd_sendSomething(self, the_command):
		commands = str.split(the_command)
		if len(commands) > 1:
			info = ''
			del commands[0]
			for i in range(len(commands)):
				info += commands[i]+' '
			TheSkyXCommand = info
			client_socket.send(TheSkyXCommand)
			return self.messages()
		else: return 'ERROR, invalid input'


	def cmd_telescopeConnect(self,the_command):
		'''Connect with the telescope.'''
		TheSkyXCommand = self.readscript('telescopeConnect.js')
		client_socket.send(TheSkyXCommand)
		return self.messages()


	def is_float_try(self,stringtry):
		'''Check to see if input is a float.'''
		try:
			float(stringtry)
			return True
		except ValueError:
			return False

	def readscript(self,script):
		'''Will read a file and return the text.'''
		try:
			f = open(script,'r')
			temp = f.read()
			f.close()
			return temp
		except ValueError:
			return -1

	def editscript(self,script, newscript, linestoreplace, newlines):
		'''This will make a script based on the template script to send to TheSky.'''
		try:
			f = open(script,'r') #open the template file
			newf = open(newscript,'w') #write the actual file we want to send to TheSkyX
			temp = []
			temp = f.readlines()
			j = 0
			for s in linestoreplace:
				for i in range(len(temp)):
					if temp[i] == s:
						temp[i] = newlines[j]
				j += 1
			for line in temp:	
				newf.write(line)
			newf.close()
			f.close()
			return 0
		except ValueError:
			print 'This is screwed'
			return -1
			
		


	def messages(self):
		'''I'm trying to make this so if you don't get a response within 10 seconds instead
		of hanging indefinitely or completely quitting, the user is simply told, and can 
		try again.'''
		data = ''
		success = 0
		for i in range(10):
			try:
				time.sleep(1)
				data = str(client_socket.recv(50000))
				success = 1
			except ValueError:
				data = 'ERROR, TheSkyX not responding'
			if success: break
		return data

			

	
