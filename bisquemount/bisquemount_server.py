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
		'''Will find an object.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			obj = commands[1]
			TheSkyXCommand = '/* Java Script */var Out; var PropCnt = 189; Out = "";sky6StarChart.Find("'+obj+'"); for(p=0;p<PropCnt;++p) {if(sky6ObjectInformation.PropertyApplies(p) != 0){sky6ObjectInformation.Property(p) ;Out+=sky6ObjectInformation.ObjInfoPropOut}}'
			client_socket.send(TheSkyXCommand)
			return self.messages()

	def cmd_getTargetRADec(self,the_command):
		'''Returns the RA and dec of the target.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			TheSkyXCommand = '/* Java Script */var Target = "'+commands[1]+'";/*Parameterize*/var TargetRA=0; var TargetDec=0; var Out=""; var err; sky6StarChart.LASTCOMERROR=0; sky6StarChart.Find(Target); err = sky6StarChart.LASTCOMERROR; if (err != 0){Out =Target + " not found."}else{sky6ObjectInformation.Property(54);/*RA_NOW*/TargetRA = sky6ObjectInformation.ObjInfoPropOut; sky6ObjectInformation.Property(55);/*DEC_NOW*/ TargetDec = sky6ObjectInformation.ObjInfoPropOut; Out = "RA: "+String(TargetRA) + "|"+"Dec: "+ String(TargetDec);}'
			client_socket.send(TheSkyXCommand)
			return self.messages()
		else: return 'ERROR, invalid input length'

	def cmd_grabScreen(self,the_command):   #Will need to change var Folder to "c:/" when this is installed on windows
		'''Grab the current screen TheSkyX is displaying.'''
		TheSkyXCommand = '/* Java Script *//* Save TheSkyXs current star chart as a JPG image*/ var Folder; var Width = 1000; var Height = 800; var USETHESKYS = -999.0; var cmd = 14; var uid = 100; var Out; if (Application.operatingSystem == 1) {Folder = "c:/";} else{Folder = "/";} sky6Web.CurAz = USETHESKYS; sky6Web.CurAlt = USETHESKYS; sky6Web.CurRotation = USETHESKYS; sky6Web.CurFOV = USETHESKYS; sky6Web.CurRa = sky6StarChart.RightAscension; sky6Web.CurDec = sky6StarChart.Declination; sky6Web.LASTCOMERROR = 0; sky6Web.CreateStarChart(USETHESKYS, cmd, uid, USETHESKYS, USETHESKYS, USETHESKYS, Width, Height, Folder); if (sky6Web.LASTCOMERROR == 0) { Out = sky6Web.outputChartFileName;} else {Out = "Error  + sky6Web.LASTCOMERROR";}'
		client_socket.send(TheSkyXCommand)
		return self.messages()


	def cmd_look(self,the_command):
		'''Tell the telescope to look north, south, east, west, up or down.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == 'north' or commands[1] == 'North':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookNorth); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			elif commands[1] == 'south' or commands[1] == 'South':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookSouth); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			elif commands[1] == 'east' or commands[1] == 'East':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookEast); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			elif commands[1] == 'west' or commands[1] == 'West':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookWest); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			elif commands[1] == 'up' or commands[1] == 'Up':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookUp); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			elif commands[1] == 'down' or commands[1] == 'Down':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookDown); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			else: return 'ERROR, incorrect input.'
		else: return 'ERROR, incorrect input.'

	def cmd_mountGoTo(self,the_command): #**************************************
		'''Moves the mount to a given RA and Dec position. Input RA then Dec'''
		commands = str.split(the_command)
		if len(commands) == 3:
			RA = commands[1]
			Dec = commands[2]
			if self.is_float_try(RA) and self.is_float_try(Dec):
				TheSkyXCommand = '/* Java Script */var TargetRA = "'+RA+'";var TargetDec = "'+Dec+'";var Out;sky6RASCOMTele.Connect();if (sky6RASCOMTele.IsConnected==0)/*Connect failed for some reason*/{Out = "Not connected"}else{sky6RASCOMTele.Asynchronous = true;sky6RASCOMTele.SlewToRaDec(TargetRA, TargetDec,"");Out  = "OK";}'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'

	def cmd_mountGetRADec(self,the_command):
		'''Gets the current RA and Dec of the mount.'''
		TheSkyXCommand = '/* Java Script */var Out;sky6RASCOMTele.Connect();if (sky6RASCOMTele.IsConnected==0)/*Connect failed for some reason*/{Out = "Not connected"}else{sky6RASCOMTele.GetRaDec();Out  = String(sky6RASCOMTele.dRa) +"| " + String(sky6RASCOMTele.dDec);}'
		client_socket.send(TheSkyXCommand)
		return self.messages()


	def cmd_moveTheSky(self,the_command):
		'''Tell TheSky to move left, right, up or down.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == 'left' or commands[1] == 'Left':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveLeft); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			elif commands[1] == 'right' or commands[1] == 'Right':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveRight); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			elif commands[1] == 'up' or commands[1] == 'Up':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveUp); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			elif commands[1] == 'down' or commands[1] =='Down':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveDown); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			else: return 'ERROR, incorrect input'
		else: return 'ERROR, incorrect input.'

	def cmd_moveTelescope(self, the_command):
		'''Will move the telescope by a specified amount.if len(sys.argv) &lt; 3:
       print usage

else:
        stext = sys.argv[1]
        rtext = sys.argv[2]
        input = sys.stdin
        output = sys.stdout
        print "There are %s args " %len(sys.argv)

        if len(sys.argv) > 3:
                input = open(sys.argv[3])

        if len(sys.argv) > 4:
                output = open(sys.argv[4], 'w')

        for s in input:
                output.write(s.replace(stext, rtext))

        if len(sys.argv)> 3:
            input.close()
            if len(sys.argv) > 4:
                    output.close()
'''
		commands = str.split(the_command)
		if len(commands) == 3:
			dXArcsecs = commands[1]
			dYArcsecs = commands[2]
			if self.is_float_try(dXArcsecs) and self.is_float_try(dYArcsecs):
				TheSkyXCommand = 'var Out;'
				TheSkyXCommand += 'sky6DirectGuide.MoveTelescope('+dXArcsecs+','+dYArcsecs+')'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			else: return 'ERROR invalid input'
		else: return 'ERROR invalid input'

	def cmd_slewToRaDec(self,the_command):
		'''Will slew the telescope to the Ra and Dec put in.'''
		commands = str.split(the_command)
		if len(commands) == 4:
			dRa = commands[1]
			dDec = commands[2]
			objectName = commands[3]
			if self.is_float_try(dRa) and self.is_float_try(dDec):
				TheSkyXCommand = '/*Java Script*/'
				TheSkyXCommand = 'sky6RASCOMTele.SlewToRaDec('+str(dRa)+','+str(dDec)+',"'+objectName+'")'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			else: return 'ERROR, Invalid input'
		else: return 'ERROR, invalid input'

	def cmd_slewToAzAlt(self,the_command):
		'''Will slew the telescope to the Az and Alt put in.'''
		commands = str.split(the_command)
		if len(commands) == 4:
			dAz = commands[1]
			dAlt = commands[2]
			objectName = commands[3]
			if self.is_float_try(dAz) and self.is_float_try(aAlt):
				TheSkyXCommand = '/*Java Script*/'
				TheSkyXCommand = 'sky6RASCOMTele.SlewToAzAlt('+str(dAz)+','+str(dAlt)+',"'+objectName+'")'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input'



	def cmd_tracking(self,the_command): #Give user more control
		'''Turns tracking on or off.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == 'on' or 'On':
				TheSkyXCommand = 'var Out; sky6RASCOMTele.SetTracking(1,1,0,0);Out = "TheSkyX Build " + Application.build + cr;Out += "RA Rate = " +sky6RASCOMTele.dRaTrackingRate + cr;Out += "Dec Rate = " + sky6RASCOMTele.dDecTrackingRate + cr;'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			elif commands[1] == 'off' or 'Off':
				TheSkyXCommand = 'var Out; sky6RASCOMTele.SetTracking(0,1,0,0);Out = "TheSkyX Build " + Application.build + cr;Out += "RA Rate = " +sky6RASCOMTele.dRaTrackingRate + cr;Out += "Dec Rate = " + sky6RASCOMTele.dDecTrackingRate + cr;'
				client_socket.send(TheSkyXCommand)
				return self.messages()
		else: return 'ERROR, invalid input'

	def cmd_zoom(self,the_command):
		'''Tell TheSky to zoom in or out.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == 'in' or commands[1] == 'In':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.ZoomIn); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			elif commands[1] == 'out' or commands[1] == 'Out':
				TheSkyXCommand = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.ZoomOut); var Out; Out = "OK"'
				client_socket.send(TheSkyXCommand)
				return self.messages()
			else: return 'ERROR, incorrect input'
		else: return 'ERROR, incorrect input.'

	def cmd_sendSomething(self, the_command):
		commands = str.split(the_command)
		if len(commands) > 1:
			info = ''
			del commands[0]
			for i in range(len(commands)):
				info += commands[i]+' '
			TheSkyXCommand = info
			print TheSkyXCommand
			client_socket.send(TheSkyXCommand)
			return self.messages()
		else: return 'ERROR, invalid input'

	



	def cmd_telescopeConnect(self,the_command):
		'''Connect with the telescope.'''
		script = open('telescopeConnect.js','r')
		TheSkyXCommand = script.read()
		script.close()
		client_socket.send(TheSkyXCommand)
		return self.messages()


	def is_float_try(self,stringtry):
		try:
			float(stringtry)
			return True
		except ValueError:
			return False
		


	def messages(self):
		'''I'm trying to make this so if you don't get a response within 10 seconds instead
		of hanging indefinitely or completely quitting, the user is simply told, and can 
		try again.'''
#		inputready,outputready,exceptready = select.select(input,[],[],0)
#		for s in inputready:
#		if message == sys.stdin:
#
#			message = str(sys.stdin.readline())
#			temp = string.split(message)
#			print message
#			if temp[0] == 'exit' or temp[0] == 'quit' or temp[0] == 'bye':
#				running = 0
#			tcpsoc.send(name+" "+message)
#		else:
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

			

	
