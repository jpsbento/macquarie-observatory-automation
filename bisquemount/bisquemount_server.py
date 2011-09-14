#*************************************************************************#
#                    Code to control the Bisque mount                     #
#*************************************************************************#

import sys
import string
import select
import socket
from datetime import datetime

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("10.72.26.145",3040))

class BisqueMountServer:

	def cmd_LookNorth(self,the_command):
		'''Tell the telescope to look north.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookNorth); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(512)

	def cmd_LookSouth(self,the_command):
		'''Tell the telescope to look south.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookSouth); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(512)

	def cmd_LookEast(self,the_command):
		'''Tell the telescope to look east.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookEast); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(512)

	def cmd_LookWest(self,the_command):
		'''Tell the telescope to look west.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.LookWest); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(512)

	def cmd_MoveLeft(self,the_command):
		'''Tell the telescope to move left.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveLeft); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(512)

	def cmd_MoveRight(self,the_command):
		'''Tell the telescope to move right.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveRight); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(512)

	def cmd_MoveUp(self,the_command):
		'''Tell the telescope to move up.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveUp); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(512)

	def cmd_MoveDown(self,the_command):
		'''Tell the telescope to move down.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.MoveDown); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(512)

	def cmd_ZoomIn(self,the_command):
		'''Tell the telescope to zoom in.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.ZoomIn); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(512)

	def cmd_ZoomOut(self,the_command):
		'''Tell the telescope to zoom out.'''
		command = '/* Java Script */TheSkyXAction.execute(TheSkyXAction.ZoomOut); var Out; Out = "OK"'
		client_socket.send(command)
		return client_socket.recv(512)

	def cmd_close(self,the_command):
		'''Close connection with the sky.'''
		client_socket.close();
		return "Goodbye! Connection with TheSkyX closed."
		
