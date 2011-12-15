# This will do EVERYTHING
# will make a way to give it a script

import os
import client_socket


class UberServer:

	bisque_IP = "10.238.16.11"
	meade_IP  = "10.238.16.12"
#23458 <-- bisquemount port number

	dome_tracking = False

	telescope_type = 'bisquemount'
	#telescope_type = 'meademount'


	# We set clients, one for each device we are talking to

	labjack_client = client_socket.ClientSocket("labjack",telescope_type) #23456 <- port number
	#telescope_client = client_socket.ClientSocket("telescope "+telescope_type)  #23458 <- port number
	#weatherstation_client = client_socket.ClientSocket("weatherstation "+telescope_type) #23457 <- port number
	#imagingsourcecamera_client = client_socket.ClientSocket("imagingsourcecamera "+telescope_type) #23459 <- port number


#***************************** A list of user commands *****************************#


	def cmd_finishSession(self,the_command):
		'''Close the slits, home the dome, home the telescope, put telescope in sleep mode.'''
		# actual stuffs for this to come



	def cmd_labjack(self,the_command):
		'''A user can still access the low level commands from the labjack using this command. ie
		type 'labjack help' to get all the available commands for the labjack server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_labjack = ' '.join(commands)
			response = self.labjack_client.send_command(command_for_labjack)
			return str(response)
		else: return 'To get a list of commands for the labjack type "labjack help".'


	def cmd_meademount(self,the_command):
		'''A user can still access the low level commands from the meademount using this command. ie
		type 'meademount help' to get all the available commands for the meademount server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_meademount = ' '.join(commands)
			response = self.telescope_client.send_command(command_for_meademount)
			return str(response)
		else: return 'To get a list of commands for the meademount type "meademount help".'

	def cmd_weatherstation(self,the_command):
		'''A user can still access the low level commands from the weatherstation using this command. ie
		type 'weatherstation help' to get all the available commands for the weatherstation server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_weatherstation = ' '.join(commands)
			response = self.weatherstation_client.send_command(command_for_weatherstation)
			return str(response)
		else: return 'To get a list of commands for the weatherstation type "weatherstation help".'

	def cmd_imagingsourcecamera(self, the_command):
		'''A user can still access the low level commands from the imaging source camera using this command. ie
		type 'imagingsourcecamera help' to get all the available commands for the imaging source camera server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_imagingsourcecamera = ' '.join(commands)
			response = self.imagingsourcecamera_client.send_command(command_for_imagingsourcecamera)
			return str(response)
		else: return 'To get a list of commands for the imaging source camera type "imagingsourcecamera help".'


	def cmd_setDomeTracking(self,the_command):
		'''Can set the dome tracking to be on or off'''
		commands = str.split(the_command)
		if len(command) == 1:
			if self.dome_tracking: return 'Dome tracking enabled.'
			else: return 'Dome tracking disabled.'
		elif len(commands) != 2: return 'Invalid input'
		if commands[1] == 'on': self.dome_tracking = True
		elif commands[1] == 'off': self.dome_tracking = False
		else: return 'Invalid input, on/off expected.'



	def cmd_orientateCamera(self, the_command):
		'''This will control the camera and the telescope to get the camera orientation.'''
		self.imagingsourcecamera_client.send_command('orientationCapture base')
		self.telescope_client.send_command('jog 1 N')  # jogs the telescope 1 arcsec (or arcmin??) north
		self.imagingsourcecamera_client.send_command('orientationCapture north 1')
		self.telescope_client.send_command('jog 1 E')
		self.imagingsourcecamera_client.send_command('orientationCapture east 1')
		response = self.imagingsourcecamera_client.send_comamnd('calculateCameraOrientation')
		return response


	def cmd_centerStar(self, the_command):
		'''This pulls together commands from the camera server and the telescope server so we can
		center and focus a bright star with just one call to this command. It is recommended that you 
		focus the star before attemping to center it for more accurate results'''
		imagingsourcecamera_client.send_command('captureImages centering_image 1')
		response = imagingsourcecamera_client.send_command('starDistanceFromCenter centering_image')
		try: dNorth, dEast = response
		except Exception: "Error with star centering"

		if dNorth > 0: self.telescope_client.send('jog N '+str(dNorth))
		else: self.telescope_client.send('jog S '+str(float(dNorth)*-1)) # Ensures we always send a postive jog distance to the telescope
		if aAz > 0: self.telescope_client.send('jog E '+str(dEast))
		else: self.telescope_client.send('jog W '+str(float(dEast)*-1))

		return 'Bright star centered.'


#***************************** End of User Commands *****************************#




	def dome_tracking(self,command):
		'''This will slew the dome to the azimuth of the telescope automatically if dome
		tracking is turned on.'''
		#set this as a background task when setting up uber_main
		if self.dome_tracking:
			self.telescope_client.send('getAzimuth')
			telescopeAzimuth = self.telescope_client.recv(1024)
			domeAzimuth = self.labjack_client.send_command('dome location')
			ljr = str.split(labjack_response)
			dome_current_azimuth = ljr[3]
			try: 
				float(telescopeAzimuth)
				float(domeAzimuth)
			except Exception: 
				self.dome_tracking = False
				return 'Error with Azimuth output from telescope, dome tracking switched off'
			if abs(float(domeAzimuth) - float(dome_current_azimuth)) > 4:
				dome_response = self.dome_client.send_command('moveDome '+str(domeAzimuth))

	# We have a potential confusion in the above function as the labjack will output it's azimuth in its coordinate
	# system, not the telescope's


	def waiting_messages(self):
		self.labjack_client.waiting_messages()







			
			




