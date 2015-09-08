# This python object is designed to take as inputs a socket number, a server name
# and a hardware object, and to do all communication in the same way for all servers.

#*************************************************************************#
#Code the runs on module import starts here.
#1) Import all modules that we need. 

import sys, time
import string
import select
import socket
from datetime import datetime
#imports that we wrote
import command_list as cl

#*************************************************************************#
#2) Now define our main class, the ServerSocket
class ServerSocket:
#Some properties needed by multiple methods.
	clients=[]
	jobs=[]
	def __init__(self, port, hardware_name, hardware_object):
#Set up the class properties "server", "input", "hardware_name" and "hardware_object"
		self.hardware_object=hardware_object
		self.hardware_name=hardware_name
		IP = ''
		ADS = (IP, port)
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#See /usr/include/sus/socket.h
#SOL_SOCK and SO_REUSE_ADDR. This stops the port from blocking after a crash etc.
#		self.server.setsockopt(0xffff, 0x0004, 1)
		self.server.setsockopt(1, 2, 1)
#See /usr/include/netinet/in.h
#IPPROTO_TCP, TCP_NODELAY. This makes the packet get sent straight away (instead of waiting for extra data 
#that might arrive).
		self.server.setsockopt(6, 1, 1)
		self.server.bind(ADS)
		self.server.setblocking(0)
		self.server.listen(5) #will allow 5 clients to connect with server
		self.input = [self.server, sys.stdin]

#This method deals with the various inputs from stdin and connected clients
	def socket_funct(self, s):
		if s == self.server:
		#handle server socket
			client, address = self.server.accept()
			client.setblocking(0)
			self.input.append(client)
			self.clients.append(client)
			#self.input[-1].send("Welcome to "+self.hardware_name+"! There are "+str(len(self.clients))+" people connected\n> ")
			self.log("A client has joined, number of clients connected: "+str(len(self.clients)))
			return 0
		elif s == sys.stdin:
		#handle standard input
			data = sys.stdin.readline()
			return data
		else:
		#handle all other sockets
			try: data = str(s.recv(1024))
			except Exception: data=0
			if data:
				return data
			else:
				s.close()
				self.input.remove(s)
				self.clients.remove(s)
				self.log("A client has left, number of clients connected: "+str(len(self.clients)))
				return 0

#We will use this to log what is happening in a file with a timestamp, but for now, print to screen
#I should also add something to document which client sent which command
	def log(self, message):
		print str(datetime.now())+" "+str(message)

#This closes the connections to the cliente neatly.
	def close(self):
		self.server.close

#This medhod adds a new job to the queue.
	def add_job(self, new_job):
		self.jobs.append(new_job)

#This method runs the jobs and waits for new input
	def run(self):
		self.log("Waiting for connection, number of clients connected: "+str(len(self.clients)))
		running=True
		while running:
                        time.sleep(0.1)
			inputready,outputready,exceptready = select.select(self.input,[],[],0)
		
			for s in inputready:  #loop through our array of sockets/inputs
				data = self.socket_funct(s)
				if data == -1:
					running=False
				elif data != 0:
					response = cl.execute_command(data,self.hardware_object)
					if response == -1:
						running=False
						if s == sys.stdin:
							self.log("Manually shut down. Goodbye.")
						else:
							self.log("Shut down by remote connection. Goodbye.")
					else:
						if s==sys.stdin:
							print response
						else:
							s.send(response + '\n')
			for the_job in self.jobs:
				message=the_job()
				if message:
					for i in self.clients:
						i.send(message)

