# This will do EVERYTHING
# will make a way to give it a script

import os
import client_socket


class UberServer:

	bisque_IP = "10.238.16.11"
	meade_IP  = "10.238.16.12"

	xaxis_flip = 1.0     #all these should be in telescope server or labjack server or split between the two?
	north_vector = [0,0]
	east_vector = [0.0]
	theta = 1 
	transformation_matrix = [math.cos(theta), math.sin(theta), -1*math.sin(theta), math.cos(theta)]	


	dome_tracking = True


	# We set clients, one for each device we are talking to

	labjack_client = client_socket.ClientSocket("labjack")
	meademount_client = client_socket.ClientSocket("meademount")
	weatherstation_client = client_socket.ClientSocket("weatherstation")
	imagingsourcecamera_client = client_socket.ClientSocket("imagingsourcecamera")

	
	def cmd_rebootServer(self,the_command):
		'''Can reboot any of the low level servers if they crash using this command, simply input the name of the server
		you wish to reboot: ie labjack.'''
		commands = str.split(the_command)
		temp = open("device_list.txt")
		tempread = read(temp)
		if len(commands) = 2:
			device_name = commands[1]
			if device_name in tempread:
				os.system("/"+device_name+"/./"+device_name+"_main")

	def cmd_home(self,the_command):
		'''Home the telescope and the dome.'''
		meade_response = meademount_client.send_command('home')
		dome_response = dome_client.send_command('home')


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
		tpye 'meademount help' to get all the available commands for the meademount server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_meademount = ' '.join(commands)
			response = self.meademount_client.send_command(command_for_meademount)
			return str(response)
		else: return 'To get a list of commands for the meademount type "meademount help".'

	def cmd_weatherstation(self,the_command):
		'''A user can still access the low level commands from the weatherstation using this command. ie
		tpye 'weatherstation help' to get all the available commands for the weatherstation server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_weatherstation = ' '.join(commands)
			response = self.weatherstation_client.send_command(command_for_weatherstation)
			return str(response)
		else: return 'To get a list of commands for the weatherstation type "weatherstation help".'

	def cmd_imagingsourcecamera(self, the_command):
		'''A user can still access the low level commands from the imaging source camera using this command. ie
		tpye 'imagingsourcecamera help' to get all the available commands for the imaging source camera server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_imagingsourcecamera = ' '.join(commands)
			response = self.imagingsourcecamera_client.send_command(command_for_imagingsourcecamera)
			return str(response)
		else: return 'To get a list of commands for the imaging source camera type "imagingsourcecamera help".'

	def cmd_slits(self, the_command):
		'''A user can still access the low level commands from the slits using this command. ie
		tpye 'slits help' to get all the available commands for the slits server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_slits = ' '.join(commands)
			response = self.slits_client.send_command(command_for_slits)
			return str(response)
		else: return 'To get a list of commands for the slits type "slits help".'


	def cmd_setDomeTracking(self,the_command):
		'''Can set the dome tracking to be on or off'''
		commands = str.split(the_command)
		if len(commands) != 2: return 'Invalid input'
		if commands[1] == 'on': self.dome_tracking = True
		elif commands[1] == 'off': self.dome_tracking = False
		else: return 'Invalid input, on/off expected.'


	def dome_tracking(self):
		'''This will slew the dome to the azimuth of the telescope automatically if dome
		tracking is turned on.'''
		#set this as a background task when setting up uber_main
		if self.dome_tracking:
			meademount_client.send('getAzimuth')
			telescopeAzimuth = meademount_client.recv(1024)
			labjack_response = labjack_client.send_command('dome')
			ljr = str.split(labjack_response)
			dome_current_azimuth = ljr[3]
			try: float(telescopeAzimuth)
			except Exception: 
				self.dome_tracking = False
				return 'Error with Azimuth output from telescope, dome tracking switched off'
			domeAzimuth = self.azimuth_telescope_to_dome(str(telescopeAzimuth))
			if abs(float(domeAzimuth) - float(dome_current_azimuth)) > 4:
				dome_response = dome_client.send_command('moveDome '+str(domeAzimuth))




	def azimuth_telescope_to_dome(self,command):
		# maybe put most of this information within the telescope class so it knows its orientation
		'''This will convert the azimuth given from the telescope to a standard format so we can use the same
		process to deal with the bisquemount and meademount autoslewing.'''
		domeoffset = 0 #this is an ANGLE which accounts for the angle when we are pointing north
		domeTelescopeDistance = 0
		commands = str.split(command)
		if len(commands) != 1: return 'Error'
		telescopeAzimuth = commands[0]
		correction = asin((self.domeTelescopeDistance/self.domeRadius)*math.sin(math.radians(telescopeAzimuth + domeoffset)))
		#Above we have also changed coordinate systems.
		correctionDegrees = math.degrees(correction)
		#whether you add or minus the correction depends on the telescopeAzimuth size
		if telescopeAzimuth <= (180-domeoffset) and telescopeAzimuth >= (360-domeoffset): correctedAzimuth = correctionDegrees + telescopeAzimuth
		if telescopeAzimuth > (180-domeoffset) and telescopeAzimuth < (360-domeoffset): correctedAzimuth = telescopeAzimuth - correctionDegrees
		return str(correctedAzimuth)



	def cmd_centerStarInfo(self, the_command):
		'''This pulls together commands from the camera server and the telescope server so we can
		center and focus a bright star with just one call to this command.'''
		centering = True # We start by assuming the star is neither centered nor focused so both these are set to true
		focusing = True
		#while centering + focusing: # While we are focusing and/or centering
			data = imagingsource.star_centering_and_focusing(self) # we need to change this to give out an array of data
			# then eg:
			if data[0] == 1: centering = False
			if data[1] == 1: focusing = False
			# so have, are we focused? are we centered? direction and amount to move telescope, direction to move focuser
			dDec = data[2]
			dAz = data[3]
			focus_direction = data[4]
			if centering: 
				if dDec > 0: bisquemount_client.send('jog amount_N N')
				else: bisquemount_client.send('jog amount_s S')
				if aAz > 0: bisquemount_client.send('jog amount_E E')
				else: bisquemount_client.send('jog amount_W W')
			if focusing: 
				bisquemount_client.send('focusMove '+data[4]) 
				time.sleep(1) 
				bisquemount_client.send('fs') #something like this

		# I think Mike said we need to get the star within 4 pixels.. but can't quite remember.
		#if math.hypot(x_distance, y_distance) > 1:  # !!! <-- Need to decide a limit
			#translated_x = (self.transformation_matrix[0]*x_distance + self.transformation_matrix[1]*y_distance)*self.xaxis_flip
			#translated_y =  self.transformation_matrix[2]*x_distance + self.transformation_matrix[3]*y_distance
			#Need to convert distance into coordinates for the telescope orientation
			#
			#Tell telescope to move
			#client_socket.send(COMMAND)
			# we should have it in RA Dec
			#dDec = translated_x # with some voodoo here
			#dAz = translated_y # more voodoo
		#else: centering = 0 # Star is centered so we can stop the loop
		return 'Bright star focused and centered.'











			
			




