# This will do EVERYTHING
# will make a way to give it a script

import os
import client_socket
import time

class UberServer:
	
	# A list of the telescopes we have, comment out all but the telescope you wish to connect with:
	telescope_type = 'bisquemount'
	#telescope_type = 'meademount'

	# We set clients, one for each device we are talking to
	labjack_client = client_socket.ClientSocket("labjack",telescope_type) #23456 <- port number
	telescope_client = client_socket.ClientSocket("telescope",telescope_type)  #23458 <- port number
	weatherstation_client = client_socket.ClientSocket("weatherstation",telescope_type) #23457 <- port number
	acqcamera_client = client_socket.ClientSocket("imagingsourcecamera",telescope_type) #23459 <- port number
	camera_client = client_socket.ClientSocket("sbig",telescope_type) #23460 <- port number

	dome_tracking = False

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

	def cmd_telescope(self,the_command):
		'''A user can still access the low level commands from the telescope using this command. ie
		type 'telescope help' to get all the available commands for the telescope server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_telescope = ' '.join(commands)
			response = self.telescope_client.send_command(command_for_telescope)
			return str(response)
		else: return 'To get a list of commands for the telescope type "telescope help".'

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

	def cmd_camera(self,the_command):
		'''A user can still access the low level commands from the imaging source camera using this command. ie
		type 'camera help' to get all the available commands for the imaging source camera server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_camera = ' '.join(commands)
			response = self.camera_client.send_command(command_for_camera)
			return str(response)
		else: return 'To get a list of commands for the camera type "camera help".'

	def cmd_acqcamera(self,the_command):
		'''A user can still access the low level commands from the imaging source camera using this command. ie
		type 'acqcamera help' to get all the available commands for the imaging source camera server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_acqcamera = ' '.join(commands)
			response = self.acqcamera_client.send_command(command_for_acqcamera)
			return str(response)
		else: return 'To get a list of commands for the acqcamera type "acqcamera help".'

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
		self.acqcamera_client.send_command('orientationCapture base')
		jog_response = self.telescope_client.send_command('jog N 1')  # jogs the telescope 1 arcsec (or arcmin??) north
		if jog_response == 'ERROR': return 'ERROR in telescope movement.'
		self.acqcamera_client.send_command('orientationCapture north 1')
		jog_response = self.telescope_client.send_command('jog E 1')
		if jog_response == 'ERROR': return 'ERROR in telescope movement'
		self.acqcamera_client.send_command('orientationCapture east 1') # Should add some responses here to keep track
		response = self.acqcamera_client.send_command('calculateCameraOrientation')
		return response

	def cmd_centerStar(self, the_command):
		'''This pulls together commands from the camera server and the telescope server so we can
		center and focus a bright star with just one call to this command. It is recommended that you 
		focus the star before attemping to center it for more accurate results'''
		acqcamera_client.send_command('captureImages centering_image 1')
		response = acqcamera_client.send_command('starDistanceFromCenter centering_image')
		try: dNorth, dEast = response
		except Exception: "Error with star centering"

		if dNorth >= 0: 
			jog_response = self.telescope_client.send_command('jog N '+str(dNorth))
			if jog_response == 'ERROR': return 'ERROR'
		else: 
			jog_response = self.telescope_client.send_command('jog S '+str(float(dNorth)*-1)) # Always send a postive jog distance
			if jog_response == 'ERROR': return 'ERROR'
		if aAz >= 0: 
			jog_response = self.telescope_client.send_command('jog E '+str(dEast))
			if jog_response == 'ERROR': return 'ERROR'
		else: 
			jog_response = self.telescope_client.send_command('jog W '+str(float(dEast)*-1))
			if jog_response == 'ERROR': return 'ERROR'

		return 'Successful centering of star'

	def cmd_focusStar(self, the_command):
		'''This pulls together commands from the telescope servers and the camera server to focus a bright star.'''
		move_focus_amount = 100
		sharp_value = 0
		focusing = True
		camera_client.send_command("focusCapture")
		old_sharp_value = self.telescope_client.send_command("focusGoToPosition "+str(int(position)+move_focus_amount))
		while move_focus_amount != 0:
			focusposition = self.telescope_client.send_command("focusReadPosition")
			try: focusposition = int(focusposition)
			except Exception: return 'ERROR'
			# need to get the sharpness
			self.telescope_client.send_command("focusGoToPosition "+str(int(position)+move_focus_amount))
			sharp_value = camera_client.send_command("focusCapture")
			# as the star becomes more in focus, the sharp_value decreases, so if it increases
			# we are moving the focuser the wrong way
			if sharp_value >= old_sharp_value: move_focus_amount = (move_focus_amount*-1)/2
		return str(focusposition) # return the best focus position
				
	def cmd_focusIRAF(self, the_command):
		'''This pulls together commands from the telescope servers and the camera server to focus a bright star using IRAF.'''
		move_focus_amount = 100
		#It is really complex if we start at a position less than 200...
		focusposition = self.telescope_client.send_command("focusReadPosition")
		focusposition = str.split(focusposition)
		focusposition = focusposition[0]
		try: focusposition = int(focusposition)
		except Exception: return 'ERROR 1 parsing focus value'
		if focusposition < 2*move_focus_amount:
			return 'ERROR 2 parsing focus value'
		for fnum in range(1,6):
			self.telescope_client.send_command("focusGoToPosition " + str(focusposition + (fnum-3)*move_focus_amount))
			self.camera_client.send_command("exposeAndWait 0.5 open focus" + str(fnum) + ".fits")
		bestimage = self.camera_client.send_command("focusCalculate")
		bestimage = str.split(bestimage)
		bestimage = bestimage[0]
		print "Best Interpolated Image from images 1-5 is: " + bestimage
		try: bestimage = float(bestimage)
		except Exception: return 'ERROR parsing best focus'
		focusposition = int(focusposition + (bestimage-3)*move_focus_amount)
	        self.telescope_client.send_command("focusGoToPosition " + str(focusposition))
		return str(focusposition) # return the best focus position
				

#***************************** End of User Commands *****************************#

	def dome_tracking(self,command):
		'''This will slew the dome to the azimuth of the telescope automatically if dome
		tracking is turned on.'''
		#set this as a background task when setting up uber_main
		if self.dome_tracking:
			telescopeAzimuth = self.telescope_client.send_command('getAzimuth')
			domeAzimuth = self.labjack_client.send_command('dome location')
			labjack_split = str.split(labjack_response)
			dome_current_azimuth = labjack_split[3]
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

	def waiting_messages(self): # I don't think this will work...
		self.labjack_client.waiting_messages()

	def monitor_slits(self):
		'''This will be a background task that monitors the output from the weatherstation and will decide whether
		it is safe to keep the slits open or not'''
		weather = weatherstation_client.send_command('safe')
		if not weather:
			response = labjack_client.send_command('slits close')
			print response  # Need to find a way to send this over sockets so the user knows



