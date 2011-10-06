import socket
import sys
import select
import string
import time


#*********************************************************************#
#set up the socket

#input = [tcpsoc, sys.stdin]

#*********************************************************************#
#some global variables
inputready = 0
data = '0'
message = ''
running = 1

#*********************************************************************#
#definition for running our client

def client_run():
	global data
	global message
	IP = ''
	PORT = 23460 #23456
	ADS = (IP, PORT)
	tcpsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcpsoc.connect(ADS)
	
	tcpsoc.setblocking(0)
	tcpsoc.settimeout(10)
	try:
		data = str(tcpsoc.recv(1024))
		message = '' #No message to give to user
	except IOError: 
		data = '0' #Tells us that we need to close the slit as we are having trouble
			   #connecting to the weatherstation server.
		message = 'Unable to connect to weather station.'
	tcpsoc.close()
	return data

#*********************************************************************#
#Main part of code

while running:

	client_run()
	#print data
	if int(data): #open the slits
		print 'Slits open'
	else: #close the slits
		print 'Slits closed'
	if message != '': print message
	time.sleep(10)
	

