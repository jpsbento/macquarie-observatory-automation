# This will do EVERYTHING
# will make a way to give it a script

import os
import client_socket


class UberServer:

	bisque_IP = "10.238.16.11"
	meade_IP  = "10.238.16.12"


	dome_tracking = True


	# We set clients, one for each device we are talking to

	labjack_client = client_socket.ClientSocket("labjack")
	meademount_client = client_socket.ClientSocket("meademount")
	weatherstation_client = client_socket.ClientSocket("weatherstation")
	imagingsourcecamera_client = client_socket.ClientSocket("imagingsourcecamera")

#***************************** A list of user commands *****************************#


	def cmd_finishSession(self,the_command):
		'''Close the slits, home the dome, home the telescope, put telescope in sleep mode.'''
		# actual stuffs for this to come

	# This whole thing is rather dodgy at the moment.
#	def cmd_rebootServer(self,the_command):
#		'''Can reboot any of the low level servers if they crash using this command, simply input the name of the server
#		you wish to reboot: ie labjack.'''
#		commands = str.split(the_command)
#		temp = open("device_list.txt")
#		tempread = read(temp)
#		if len(commands) = 2:
#			device_name = commands[1]
#			if device_name in tempread:
				# ssh into relevant machine maybe: os.system("ssh phy-admin@"+meade_IP)
				# result = os.system("/"+device_name+"/./"+device_name+"_main")
				# we actually have to ssh into the correct machine first
				# if result == 0: it's worked, if not it hasn't

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
		type 'meademount help' to get all the available commands for the meademount server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_meademount = ' '.join(commands)
			response = self.meademount_client.send_command(command_for_meademount)
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
		imagingsourcecamera_client.send_command('orientationCapture base')
		bisquemount_client.send_command('jog 1 N')  # jogs the telescope 1 arcsec (or arcmin??) north
		imagingsourcecamera_client.send_command('orientationCapture north 1')
		bisquemount_clinet.send_command('jog 1 E')
		imagingsourcecamera_client.send_command('orientationCapture east 1')
		response = imagingsourcecamera_client.send_comamnd('calculateCameraOrientation')
		return response


	def cmd_centerStar(self, the_command):
		'''This pulls together commands from the camera server and the telescope server so we can
		center and focus a bright star with just one call to this command. It is recommended that you 
		focus the star before attemping to center it for more accurate results'''
		imagingsourcecamera_client.send_command('captureImages centering_image 1')
		response = imagingsourcecamera_client.send_command('starDistanceFromCenter centering_image')
		try: dNorth, dEast = response
		except Exception: "Error with star centering"

		if dNorth > 0: bisquemount_client.send('jog '+dNorth+' N')
		else: bisquemount_client.send('jog 'str(float(dNorth)*-1)+' S')
		if aAz > 0: bisquemount_client.send('jog '+dEast+' E')
		else: bisquemount_client.send('jog '+str(float(dEast)*-1)+' W')

		return 'Bright star centered.'


#***************************** End of User Commands *****************************#




	def dome_tracking(self,command):
		'''This will slew the dome to the azimuth of the telescope automatically if dome
		tracking is turned on.'''
		#set this as a background task when setting up uber_main
		if self.dome_tracking:
			meademount_client.send('getAzimuth')
			telescopeAzimuth = meademount_client.recv(1024)
			domeAzimuth = labjack_client.send_command('dome location')
			ljr = str.split(labjack_response)
			dome_current_azimuth = ljr[3]
			try: 
				float(telescopeAzimuth)
				float(domeAzimuth)
			except Exception: 
				self.dome_tracking = False
				return 'Error with Azimuth output from telescope, dome tracking switched off'
			if abs(float(domeAzimuth) - float(dome_current_azimuth)) > 4:
				dome_response = dome_client.send_command('moveDome '+str(domeAzimuth))

# We have a potential mess in the above function as the labjack will output it's azimuth in it's coordinate
# system (I think..).. Think about this.








			
			




