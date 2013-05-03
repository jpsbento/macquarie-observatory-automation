 # This will do EVERYTHING
# will make a way to give it a script

import os
import client_socket
import time, math
import pyfits

class UberServer:
	
	# A list of the telescopes we have, comment out all but the telescope you wish to connect with:
	telescope_type = 'bisquemount'
	#telescope_type = 'meademount'

	# We set clients, one for each device we are talking to
	labjack_client = client_socket.ClientSocket("labjack",telescope_type) #23456 <- port number
	telescope_client = client_socket.ClientSocket("telescope",telescope_type)  #23458 <- port number
	weatherstation_client = client_socket.ClientSocket("weatherstation",telescope_type) #23457 <- port number
	sidecam_client = client_socket.ClientSocket("sidecamera",telescope_type) #23459 <- port number
	camera_client = client_socket.ClientSocket("sbig",telescope_type) #23460 <- port number 
	fiberfeed_client = client_socket.ClientSocket("fiberfeed",telescope_type) #23459 <- port number
        labjacku6_client = client_socket.ClientSocket("labjacku6",telescope_type) #23462 <- port number

	dome_tracking = True
	override_wx = False
	
	weather_counts = 1 #integer that gets incremented if the slits are open, the override_wx is false and the weather station returns an unsafe status. If this gets above 3, close slits (see function where this is used)
	dome_last_sync=time.time()
	dome_frequency = 30 #This parameters sets how often the SkyX virtual dome is told to align with the telescope pointing.
	guiding_bool=False
	guiding_camera='fiberfeed'
	guiding_failures=0

	#this parameter corresponds to an approximate ratio between the exposure times of the sidecamera and the fiberfeed camera for a given star (or all stars). Should be 20 for accurate value. If it is any less is just to make sure that there are enough photons if the telescope is out of focus.
	side_fiber_exp_ratio=5.
	
	exposing=False   #Boolean to determine when the camera should be exposing
	exptime=0        #Default exposure time
	shutter_position='closed'  #Default shutter position
	filename='None'
	old_filename='None'

	#Parameters to do with the focus adjustment
	move_focus_amount = 200
	sharp_value = 0
	sharp_count =0
	initial_focus_position=0
	
#***************************** A list of user commands *****************************#

	def cmd_finishSession(self,the_command):
		'''Close the slits, home the dome, home the telescope, put telescope in sleep mode.'''
		# actual stuffs for this to come
		dummy = self.labjack_client.send_command('slits close')
		self.dome_tracking=False
		dummy = self.labjack_client.send_command('dome home')
		dummy = self.telescope_client.send_command('park')
		self.override_wx=False

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

	def cmd_sidecam(self,the_command):
		'''A user can still access the low level commands from the imaging source camera using this command. ie
		type 'sidecam help' to get all the available commands for the imaging source camera server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_sidecam = ' '.join(commands)
			response = self.sidecam_client.send_command(command_for_sidecam)
			return str(response)
		else: return 'To get a list of commands for the sidecam type "sidecam help".'

	def cmd_fiberfeed(self,the_command):
		'''A user can still access the low level commands from the fiber feed imaging source camera using this command. ie
		type 'fiberfeed help' to get all the available commands for the imaging source camera server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_fiberfeed = ' '.join(commands)
			response = self.fiberfeed_client.send_command(command_for_fiberfeed)
			return str(response)
		else: return 'To get a list of commands for the fiberfeed type "fiberfeed help".'

	def cmd_labjacku6(self,the_command):
		'''A user can still access the low level commands from the labjacku6 using this command. ie
		type 'labjacku6 help' to get all the available commands for the labjack server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_labjacku6 = ' '.join(commands)
			response = self.labjacku6_client.send_command(command_for_labjacku6)
			return str(response)
		else: return 'To get a list of commands for the labjacku6 type "labjacku6 help".'

		
	def cmd_setDomeTracking(self,the_command):
		'''Can set the dome tracking to be on or off'''
		commands = str.split(the_command)
		if len(commands) == 1:
			if self.dome_tracking: return 'Dome tracking enabled.'
			else: return 'Dome tracking disabled.' 
		elif len(commands) != 2: return 'Invalid input'
		if commands[1] == 'on': self.dome_tracking = True
		elif commands[1] == 'off': self.dome_tracking = False
		else: return 'Invalid input, on/off expected.'

	def cmd_orientateCamera(self, the_command):
		'''This will control the camera and the telescope to get the camera orientation.'''
		commands=str.split(the_command)
		if len(commands)!=2: return 'Invalid number of arguments. Please indicate which camera you want this to happen on.'
		if commands[1]=='fiberfeed':
			cam_client=self.fiberfeed_client
			jog_amount=str(0.2)
		elif commands[1]=='sidecam': 
			cam_client=self.sidecam_client
			jog_amount=str(20)
		else: return 'Invalid camera selection'
		cam_client.send_command('orientationCapture base')
		jog_response = self.telescope_client.send_command('jog North '+jog_amount)  # jogs the telescope 1 arcsec (or arcmin??) north
		if jog_response == 'ERROR': return 'ERROR in telescope movement.'
		print 'sleeping 5 seconds'
		time.sleep(5)
		cam_client.send_command('orientationCapture North '+jog_amount)
		jog_response = self.telescope_client.send_command('jog East '+jog_amount)
		print 'sleeping 5 seconds'
		time.sleep(5)
		if jog_response == 'ERROR': return 'ERROR in telescope movement'
		cam_client.send_command('orientationCapture East '+jog_amount) # Should add some responses here to keep track
		response = cam_client.send_command('calculateCameraOrientation')
		return response

	def cmd_offset(self, the_command):
		'''This pulls together commands from the camera server and the telescope server so that we can move the telescope to a given known pixel position which corresponds to the centre of the telescope field of view'''
		#These are the known coordinates of the centre of the telescope field of view. These need to be changed every time anything is put on the back of the telescope. 
		x_final=332.93
		y_final=224.39
		#The input for this function is the current coordinates of the bright star. This perhaps should take the output of brightStarCoords instead....
		commands=str.split(the_command)
		try:
			x_init= float(commands[1])
			y_init= float(commands[2])
		except Exception: print 'ERROR: Coordinates introduced are not floats.'
		#This is the pixel offsets required
		dx=x_final-x_init #in declination
		dy=y_final-y_init #in RA
		#Convert these into hours (in RA) and degrees (in Dec)
		dxd=dx*120/3600.#in degrees
		dyh=dy*120/3600./15.#in hours
		#Query the telescope for the current RA and Dec
		try:
			RA_init=float(str.split(self.telescope_client.send_command('getRA'))[0])
			Dec_init=float(str.split(self.telescope_client.send_command('getDec'))[0])
		except Exception: 'ERROR: RA and Dec query not successful'
		#Calculate the new coordinates in hours (RA) and degrees (Dec)
		RA_final=RA_init+dyh
		Dec_final=Dec_init+dxd
		#Instruct the telescope to move to new coordinates
		try: dummy = self.telescope_client.send_command('slewToRaDec '+str(RA_final)+' '+str(Dec_final))
		except Exception: print'ERROR: Telescope failed to move to new coordinates'
		return 'Telescope successfully offset to new coordinates.'
		

	def cmd_centerStar(self, the_command):
		'''This pulls together commands from the camera server and the telescope server so we can
		center and focus a bright star with just one call to this command. It is recommended that you 
		focus the star before attemping to center it for more accurate results'''
		sidecam_client.send_command('captureImages centering_image 1')
		response = sidecam_client.send_command('starDistanceFromCenter centering_image')
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
				
	def cmd_override_wx(self, the_command):
		commands=str.split(the_command)
		if len(commands) == 2 and (commands[1] == 'off' or commands[1]=='0'):
			self.override_wx=False
		else: self.override_wx=True
		return str(self.override_wx)

	def cmd_guiding(self, the_command):
		'''This function is used to activate or decativate the guiding loop. Usage is 'guiding <on/off> <camera>', where option is either 'on' or 'off' and camera is either 'sidecam' or 'fiberfeed' (default). For the 'off' option, no camera needs to be specified.'''
		commands=str.split(the_command)
		if len(commands)==2:
			if commands[1]=='off':
				self.guiding_bool=False
				return 'Guiding loop disabled'
			elif commands[1]=='on':
				self.guiding_bool=True
				self.guiding_camera='fiberfeed'
				return 'Guiding loop enabled using the '+self.guiding_camera
			else: return 'invalid argument.'
		if len(commands)==3 and commands[1]=='on':
			self.guiding_bool=True
			if commands[2]=='sidecam': 
				self.guiding_camera='sidecam'
				return 'Guiding loop enabled using the '+self.guiding_camera
			elif commands[2]=='fiberfeed':
				self.guiding_camera='fiberfeed'
				return 'Guiding loop enabled using the '+self.guiding_camera
			else: return 'invalid camera selection'
		else: return 'invalid number of arguments'
			
		#Still needs to be completed. 
		
	def cmd_spiral(self, the_command):
		'''This function is used to spiral the telescope until the fiberfeed camera finds a star close to the center of the chip. Usage is 'guiding <amount>', where amount is the offset in arcmins of each spiral motion. A default amount is set'''
		default=2.0
		commands=str.split(the_command)
		if len(commands) > 2:
			return 'Too many arguments!'
		if len(commands) == 1:
			offset=default
		else: 
			try: offset=float(commands[1])
			except Exception: return 'invalid offset value for spiralling. Type "spiral help" for more information.'
		#m=0: keep searching in large movements. m=1: search closer
		m=0
		#n=number of times the offset the current direction is meant to be moved by
		n=1
		#sign is the orientation of the motion. To move south, you can instruct the telescope to move north negatively. (see below for explanation of this procedure)
		sign=1
		#parameter that changes once a star has been found close to the middle of the chip.
		found_it=False
		#directions of motion
		directions=['North','East']
		while n<11 and found_it==False:
			for direction in directions:
				for i in range(n):
					result=self.fiberfeed_client.send_command('brightStarCoords')
					if 'no stars found' not in result:
						 starinfo=str.split(result)
						 try: 
							 xcoord=float(starinfo[1])
							 ycoord=float(starinfo[2])
						 except Exception: return 'Something went really wrong here, if we got this message...'
						 print 'star found in coordinates', xcoord, ycoord
						 if m==0:
							 m=1
							 offset/=4.
							 n=1
							 sign=1
						 if xcoord < 520 and xcoord > 120 and ycoord < 360 and ycoord > 120:
							 return 'Spiral sucessful. Star is now at coordinates '+str(xcoord)+', '+str(ycoord)
						 else: print 'Still not good enough. Continuing...'
					else: print 'Star not found, Continuing...'
					jog_response=self.telescope_client.send_command('jog '+direction+' '+str(sign*offset))
					print direction, sign*offset
					time.sleep(3)
					self.fiberfeed_client.send_command('captureImages test 1 no')
			sign*=-1
			n+=1
		if found_it==False:
			return 'Spiral unsucessful. Star is not within the search region.'

		#_______________________________________________
		#  Quick explanation of how the spiralling is coded:
		#
		#  What we want is to move 1 north, 1 east, 2 south, 2 west, 3 north, 3 east, 
		#   4 south, 4 west, etc, taking exposures at each offset of 1. (The units of the motion are defined in the input).
		#
		#  And, moving twice south is equivalent of moving twice north by a negative amount. Also, notice that the amount 
		#  of displacement in each direction is increased by one every time the direction of motion changes twice.
		#
		#  So, one loop that moves north by a given amount, and east by the same amount, can do the trick, provided that the 
		#  amount of offsets is increased every time the loop runs and the direction of motion is inverted every loop. The amount 
		#  controlled by the variable 'n' and the motion direction is inverted by multiplying the amount by 1 or -1 depending on the
		#  iteration.
		#


	def cmd_masterAlign(self, the_command):
		'''Awesome!! function that can be ran to trigger the improvement in the alignment. This is supposed to be ran once the telescope has been instructed to point at a star and the dome has finished moving to it, and it will improve the pointing using the sidecam, put the star in the fiberfeed cam and start the guiding. It is mostly a collection of existing functions. It is also highly customisable.

		This function will require more thorough checks along the way. This will be added whilst this is being tested.'''
		try: self.sidecam_client.send_command('Chop on')
		except Exception: 
			print 'ERROR: Failed to set the image chopping on the sidecam'
			return 0
		print 'image chopping activated.'
		try: self.sidecam_client.send_command('setCameraValues default')
		except Exception: 
			print 'ERROR: Failed to set the default values for the sidecam'
			return 0
		print 'default values for sidecam set.'
		try: self.sidecam_client.send_command('adjustExposure')
		except Exception: 
			print 'ERROR: Failed to adjust the exposure of the sidecam'
			return 0
		print 'exposure adjusted for sidecam.'
		try: self.cmd_orientateCamera('orientateCamera sidecam')
		except Exception: 
			print 'ERROR: Failed to set the orientation of the sidecam'
			return 0
		print 'orientation of the sidecamera set.'
		distance=1000
		while distance>1.0:
			try: self.sidecam_client.send_command('imageCube test 10')
			except Exception: 
				print 'ERROR: Failed to take images to work out where the star is at the moment'
				return 0
			print 'current location images taken for sidecam.'
			try: 
				moving=str.split(self.sidecam_client.send_command('starDistanceFromCenter test'))
				dummy=float(moving[0])
			except Exception: 
				print 'ERROR: Failed to work out what the stellar distance to the optimal coordinates is'
				return 0
			print 'Stellar distance to center found.'
			distance=math.sqrt(float(moving[0])**2+float(moving[1])**2)
			print 'Distance to be moved: ',distance
			try: 
				self.telescope_client.send_command('jog North '+moving[0])
				self.telescope_client.send_command('jog East '+moving[1])
			except Exception:
				print 'ERROR: Failed to move telescope to desired coordinates'
				return 0
		print 'successfully moved telescope to location'
		#Set the focus position back to the initial value
		if self.initial_focus_position==0:
			self.initial_focus_position=self.telescope_client.send_command("focusReadPosition").split('\n')[0]
		else: 
			self.telescope_client.send_command("focusGoToPosition "+self.initial_focus_position)
		try: 
			sidecam_exposure=self.sidecam_client.send_command('currentExposure')
			fiberfeed_exposure=str(int(float(str.split(sidecam_exposure)[0])*1E4/self.side_fiber_exp_ratio))
		except Exception:
			print 'ERROR: Failed to query current sidecam exposure time'
			return 0
		print 'Got the sidecamera exposure'
		try: self.fiberfeed_client.send_command('setCameraValues default')
		except Exception: 
			print 'ERROR: Failed to set the default values for the fiberfeed'
			return 0
		print 'Set default values for fiberfeed'
		try: self.fiberfeed_client.send_command('setCameraValues ExposureAbs '+fiberfeed_exposure)
		except Exception:
			print 'ERROR: Failed set the fiberfeed camera exposure time'
			return 0
		print 'set exposure time for fiberfeed'
		try: self.cmd_spiral('spiral')
		except Exception:
			print 'ERROR: Failed to spiral for some reason. Check the output '
			return 0
		print 'spiralling complete'
		try: self.fiberfeed_client.send_command('adjustExposure')
		except Exception:
			print 'ERROR: Failed to adjust exposure for the fiberfeed camera'
			return 0
		print 'adjusted exposure for fiberfeed'
		try: self.cmd_orientateCamera('orientateCamera fiberfeed')
		except Exception: 
			print 'ERROR: Failed to set the orientation of the fiberfeed camera'
			return 0
		print 'orientation of fiberfeed found'
		try: self.fiberfeed_client.send_command('imageCube test 10')
		except Exception: 
			print 'ERROR: Failed to take images to work out where the star is at the moment in the fiberfeed camera'
			return 0
		print 'got the images of current location of star'
		try: 
			moving=str.split(self.fiberfeed_client.send_command('starDistanceFromCenter test'))
			dummy=float(moving[0])
		except Exception: 
			print 'ERROR: Failed to work out what the stellar distance to the optimal coordinates is on the fiberfeed camera'
			return 0
		print 'worked out the stellar distance to center'
		try: 
			self.telescope_client.send_command('jog North '+moving[0])
			self.telescope_client.send_command('jog East '+moving[1])
		except Exception:
			print 'ERROR: Failed to move telescope to desired coordinates (fiberfeed)'
			return 0
		print 'sucessfully moved telescope'
		try: self.fiberfeed_client.send_command('captureImages program_images/visual 1')
		except Exception: 
			print 'Failed to capture an image to show you where the star currently lies in. Not too much of a problem...'
		self.guiding_failures=0
		return 'Finished the master alignment. You can now inspect the image and decide if this is good enough. '
		
	def cmd_Imaging(self,the_command):
		#sets the state of the boolean for the imaging_loop function COMPLETE!!!!!
		commands=str.split(the_command)
		if len(commands)==1: return 'Imaging is set to '+str(self.exposing)
		elif len(commands)==2 and commands[1]=='on': self.exposing=True
		elif len(commands)==2 and commands[1]=='off': self.exposing=False
		else: return 'Incorrect usage of function. Activate Imaging using "on" or "off".'
		return 'Imaging status set to '+str(self.exposing)

	def cmd_Imsettings(self,the_command):
		#sets the camera settings for the exposing loop
		commands=str.split(the_command)
		if len(commands)==1: 
			return 'exposure time is set to '+str(self.exptime)+'\nshutter state is set to '+str(self.shutter_position)
		elif len(commands)!=3:
			return 'please input the desired exposure time in seconds and the intended shutter state'
		else:
			self.exptime=float(commands[1])
			self.shutter_position=commands[2]
			return 'Finished updating camera settings'
	

#***************************** End of User Commands *****************************#

	def dome_track(self):
		'''This will slew the dome to the azimuth of the telescope automatically if dome
		tracking is turned on.'''
		#set this as a background task when setting up uber_main
		if self.dome_tracking:
			domeAzimuth = str.split(self.labjack_client.send_command('dome location'))[0]
#			print domeAzimuth
			VirtualDome = str.split(self.telescope_client.send_command('SkyDomeGetAz'),'|')[0]
#			print VirtualDome
			try: float(domeAzimuth)
			except Exception: 
				self.dome_tracking = False
				return 'Dome Azimuth not as expected.'
			try: float(VirtualDome)
			except Exception:
				self.dome_tracking = False
				return 'Virtual Dome not giving out what is expected'
			if abs(float(domeAzimuth) - float(VirtualDome)) > 2.5:
				print 'go to azimuth:'+str(VirtualDome)+' because of an offset. Dome azimuth is currently: '+str(domeAzimuth)
				self.labjack_client.send_command('dome '+str(VirtualDome))
			if (math.fabs(time.time() - self.dome_last_sync) > self.dome_frequency ):
				try: ForceTrack=self.telescope_client.send_command('SkyDomeForceTrack') #Forces the virtual dome to track the telescope every self.dome_frequency seconds
				except Exception: print 'Unable to force the virtual dome tracking'
				self.dome_last_sync=time.time()
				#print 'Dome Synced'


	def waiting_messages(self): # I don't think this will work...
		self.labjack_client.waiting_messages()

	def monitor_slits(self):
		'''This will be a background task that monitors the output from the weatherstation and will decide whether
		it is safe to keep the slits open or not'''
		try: slits_opened = self.labjack_client.send_command('slits').split()[0]
		except Exception: print 'Could not query the status of the slits from Labjack.'
		if (not self.override_wx) & (slits_opened=='True'):
			try: weather = self.weatherstation_client.send_command('safe')
			except Exception: 
				response = self.labjack_client.send_command('slits close')
				print 'ERROR: Communication with the WeatherStation failed. Closing Slits for safety.'
			if not "1" in weather:
				if self.weather_counts > 3:
					response = self.labjack_client.send_command('slits close')
					print 'Weather not suitable for observing. Closing Slits.'
				else:
					self.weather_counts+=1
			else:
				self.weather_counts=1
				self.labjack_client.send_command('ok')

	#This may not be necessary anymore. Anyways, looks like a pretty stupid function to have. Might as well replace any function call with the only line in it! I'm just leaving it here for now just in case something else is calling it, in case the program breaks.
	def watchdog_slits(self):
		self.labjack_client.send_command('ok')		


	def guiding_loop(self):
		'''This is the function that does the guiding loop''' 
		if self.guiding_bool and ('False' in self.fiberfeed_client.send_command('imagingStatus')):
			guidingReturn=str.split(self.fiberfeed_client.send_command('guidingReturn'))
			HFD=float(guidingReturn[0])
			moving=[float(guidingReturn[1]),float(guidingReturn[2])]
			if HFD==0.0 and moving==[0.0,0.0]:
				if self.guiding_failures>10:
					print 'guide star lost, stopping the guiding loop'
					self.guiding_bool=False
				else: self.guiding_failures+=1
			else:
				self.guiding_failures=0
				try: 
					dummy=self.telescope_client.send_command('jog North '+str(float(moving[0])/2.))
					dummy=self.telescope_client.send_command('jog East '+str(float(moving[1])/2.))
				except Exception: 
					print 'For some reason communication with the telescope is not working.'  
					self.guiding_bool=False
				print 'Guiding has offset the telescope by amounts: '+str(moving[0])+' arcmins Nrth and '+str(moving[1])+' arcmins East'
				result=self.telescope_client.send_command('focusTelescope '+str(HFD))
				if 'Focussing' not in result: print 'Something went wrong with the focussing instruction'
			result=self.fiberfeed_client.send_command('guide')
			if 'being taken' not in result: print 'Something went wrong with the image instruction'



	def imaging_loop(self):
		#Function that sets the camera going if the imaging boolean is true
		if os.path.exists('../sbig/images/'+self.old_filename+'.fits'):
			a=pyfits.getheader('../sbig/images/'+self.old_filename+'.fits')
			if not a.has_key('TELESCOP'):
				im=pyfits.open('../sbig/images/'+self.old_filename+'.fits',mode='update')
				h=im[0].header
				h.update('TELESCOP', 'Meade LX200 f/10 16 inch', 'Which telescope used')
				h.update('LAT', -33.77022, 'Telescope latitude (deg)')
				h.update('LONG', 151.111075, 'Telescope longitude (deg)')
				h.update('TEL-RA', float(self.telescope_client.send_command('getRA').split('\n')[0]), 'Telescope pointing Right Ascension')
				h.update('TEL-DEC', float(self.telescope_client.send_command('getDec').split('\n')[0]) , 'Telescope pointing Declination')
				telAlt=float(self.telescope_client.send_command('getAltitude').split('\n')[0])
				h.update('TEL-ALT', telAlt, 'Telescope pointing altitude')
				telAz=float(self.telescope_client.send_command('getAzimuth').split('\n')[0])
				h.update('TEL-AZ', float(self.telescope_client.send_command('getAzimuth').split('\n')[0]) , 'Telescope pointing Azimuth')
				h.update('DOMETEMP', float(self.labjack_client.send_command('temperature').split('\n')[0]) , 'Dome Temperature (C)')
				h.update('DOMEHUMD', float(self.labjack_client.send_command('humidity').split('\n')[0]) , 'Dome Humidity')
				zendist= 90-telAlt 
				h.update('ZENDIST', zendist , 'Zenith Distance (deg)')
				#From Rozenberg, G. V. 1966. Twilight: A Study in Atmospheric Optics. New York: Plenum Press, 160.
				airmass= 1/(math.cos(math.radians(zendist)) + 0.025*math.exp(-11*math.cos(math.radians(zendist))))
				h.update('AIRMASS',airmass , 'Airmass of observation')
				h.update('MOONPHAS', 'place_holder', 'Lunar Phase (% illumination)')
				h.update('MOONDIST', 'place_holder', 'Distance to the Moon (deg)')
				h.update('MOONALT','place_holder' , 'Moon altitude (deg)')
				h.update('NIGHT', 'place_holder', 'Night index')
				im.flush()
				self.old_filename='None'
		if self.exposing==True and ('False' in self.camera_client.send_command('imagingStatus')) and self.old_filename=='None':
			localtime=time.localtime(time.time())
			self.filename=str(localtime[0])+str(localtime[1]).zfill(2)+str(localtime[2]).zfill(2)+str(localtime[3]).zfill(2)+str(localtime[4]).zfill(2)+str(localtime[5]).zfill(2)
			result=self.camera_client.send_command('imageInstruction '+str(self.exptime)+' '+str(self.shutter_position)+' '+self.filename)
			if self.old_filename=='None': self.old_filename=self.filename
			if 'being taken' not in result: print 'Something went wrong with the image instruction'
