#*************************************************************************#
#                    Code to control the Bisque mount                     #
#*************************************************************************#

import sys
import string
import select
import socket
from datetime import datetime

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("10.126.56.202",3040))

class BisqueMountServer:

	def cmd_LookNorth(self,the_command):
		'''Tell the telescope to look north.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookNorth); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_LookSouth(self,the_command):
		'''Tell the telescope to look south.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookSouth); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_LookEast(self,the_command):
		'''Tell the telescope to look east.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookEast); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_LookWest(self,the_command):
		'''Tell the telescope to look west.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookWest); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_LookUp(self,the_command):
		'''Tell the telescope to look up.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookUp); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_MoveLeft(self,the_command):
		'''Tell the telescope to move left.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveLeft); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_MoveRight(self,the_command):
		'''Tell the telescope to move right.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveRight); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_MoveUp(self,the_command):
		'''Tell the telescope to move up.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveUp); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_MoveDown(self,the_command):
		'''Tell the telescope to move down.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveDown); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_ZoomIn(self,the_command):
		'''Tell the telescope to zoom in.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.ZoomIn); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_ZoomOut(self,the_command):
		'''Tell the telescope to zoom out.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.ZoomOut); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_GrabScreen(self,the_command):   #Will need to change var Folder to "c:/" when this is installed on windows
		'''Grab the current screen TheSkyX is displaying.'''
		command = '/* Java Script *//* Save TheSkyXs current star chart as a JPG image*/ var Folder; var Width = 1000; var Height = 800; var USETHESKYS = -999.0; var cmd = 14; var uid = 100; var Out; if (Application.operatingSystem == 1) {Folder = "c:/";} else{Folder = "/";} sky6Web.CurAz = USETHESKYS; sky6Web.CurAlt = USETHESKYS; sky6Web.CurRotation = USETHESKYS; sky6Web.CurFOV = USETHESKYS; sky6Web.CurRa = sky6StarChart.RightAscension; sky6Web.CurDec = sky6StarChart.Declination; sky6Web.LASTCOMERROR = 0; sky6Web.CreateStarChart(USETHESKYS, cmd, uid, USETHESKYS, USETHESKYS, USETHESKYS, Width, Height, Folder); if (sky6Web.LASTCOMERROR == 0) { Out = sky6Web.outputChartFileName;} else {Out = "Error  + sky6Web.LASTCOMERROR";}'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_GetTargetRADec(self,the_command):
		'''Returns the RA and dec of the target.'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			command = '/* Java Script */var Target = "'+commands[1]+'";/*Parameterize*/var TargetRA=0; var TargetDec=0; var Out=""; var err; sky6StarChart.LASTCOMERROR=0; sky6StarChart.Find(Target); err = sky6StarChart.LASTCOMERROR; if (err != 0){Out =Target + " not found."}else{sky6ObjectInformation.Property(54);/*RA_NOW*/TargetRA = sky6ObjectInformation.ObjInfoPropOut; sky6ObjectInformation.Property(55);/*DEC_NOW*/ TargetDec = sky6ObjectInformation.ObjInfoPropOut; Out = "RA: "+String(TargetRA) + "|"+"Dec: "+ String(TargetDec);}'
			client_socket.send(command)
			return client_socket.recv(1024)
		else: return 'ERROR, invalid input length'

	def cmd_MountGoTo(self,the_command):
		'''Moves the mount to a given RA and Dec position. Input RA then Dec'''
		if len(the_command) == 3:
			commands = str.split(the_command)
			RA = commands[1]
			Dec = commands[2]
			command = '/* Java Script */var TargetRA = "'+RA+'";var TargetDec = "'+Dec+'";var Out;sky6RASCOMTele.Connect();if (sky6RASCOMTele.IsConnected==0)/*Connect failed for some reason*/{Out = "Not connected"}else{sky6RASCOMTele.Asynchronous = true;sky6RASCOMTele.SlewToRaDec(TargetRA, TargetDec,"");Out  = "OK";}'
			client_socket.send(command)
			return client_socket.recv(1024)
		else: return 'ERROR, invalid input length'

	def cmd_MountGetRADec(self,the_command):
		'''Gets the current RA and Dec of the mount.'''
		command = '/* Java Script */var Out;sky6RASCOMTele.Connect();if (sky6RASCOMTele.IsConnected==0)/*Connect failed for some reason*/{Out = "Not connected"}else{sky6RASCOMTele.GetRaDec();Out  = String(sky6RASCOMTele.dRa) +"| " + String(sky6RASCOMTele.dDec);}'
		client_socket.send(command)
		return client_socket.recv(1024)

	def cmd_Find(self,the_command):
		'''Will find an object.'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			obj = commands[1]
			command = '/* Java Script */ var Out; Var PropCnt = 189; Out = ""; Sky6StarChart.Find("moon"); for(p=0;p<PropCnt;++p){if(sky6ObjectInformation.PropertyApplies(p)!=0){sky6ObjectInformation.Property(p); Out += sky6ObjectInformation.ObjInfoPropOut+"|"}}'
			client_socket.send(command)
			return client_socket.recv(1024)
		else: return 'ERROR, invalid input length'

		
