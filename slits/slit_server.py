#**********************************************************************#
#                                                                      #
#         This is the client for the slits. It will attempt to         #
#         connect to the weatherstation server to be told whether      #
#         it is okay weather to open or not. If the client cannot      #
#         connect to the server, the slits will close automatically.   #
#                                                                      #
#**********************************************************************#


import socket
import sys
import select
import string
import time

class SlitServer:

#*********************************************************************#
#set up the socket

#input = [tcpsoc, sys.stdin]

#*********************************************************************#
#some global variables
	data = '0'
	message = ''
	openslits = 0 #This will determine if the user wants the slits open or not


#*********************************************************************#
#definition for running our client

	def cmd_slit(self,the_command):
		'''The command for the user to open/close the slits.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == 'open': 
				self.data = '1'
				self.openslits = 1
				return 'Opening slits.'
			elif commands[1] == 'close':
				self.data = '0'
				self.openslits = 0
				return 'Closing slits.'
			else: return 'ERROR, invalid input.'
		else: return 'ERROR, invalid input.'

	def slit_client(self):

		if self.openslits: #If we want the slits open, check it's safe
			IP = ''
			PORT = 23460 #23456
			ADS = (IP, PORT)
			tcpsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	
			tcpsoc.setblocking(0)
			tcpsoc.settimeout(10)
			try:
				tcpsoc.connect(ADS)
				self.data = str(tcpsoc.recv(1024))
				self.message = '' #No message to give to user
			except IOError: 
				self.data = '0' #Tells us that we need to close the slit as we are having trouble
						#connecting to the weatherstation server.
				self.message = 'Unable to connect to weather station. Closing slits.'
			tcpsoc.close()
			#print data
			#if int(self.data): #open the slits
			#	print 'Slits open'
			#else: #close the slits
			#	print 'Slits closed'
			#if self.message != '': print self.message
			time.sleep(10)
			return self.data+' '+self.message+'\n'

	#while running:

	#	client_run()

	

