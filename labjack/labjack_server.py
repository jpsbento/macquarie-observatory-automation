#*********************************************************************#
#                 Code for the labjack server                         #
#*********************************************************************#

#*********************************************************************#
#Code the runs on module import starts here.
#1) Import all modules that we need. NB ei1050 isn't installed by default,
#   but is in the "examples" directory of the labjack code.
import string
import u3
import ei1050
import math

#***********************************************************************#
#2) Set up the labjack. As the LJ and LJPROBE are declared in the global
#   module scope, lets give them capitals. These are initialized, but
#   not written to within our module. Two instances of the LabjackServer
#   would then write to the *same* labjack hardware, but could e.g. 
#   do different parts of the job. You's almost certainly *not* want to do 
#   this.
LJ=u3.U3()
LJPROBE=ei1050.EI1050(LJ, enablePinNum=0, dataPinNum=1, clockPinNum=2) #Sets up the humidity probe
LJ.configIO(NumberOfTimersEnabled = 2, EnableCounter0 = 1)
LJ.getFeedback(u3.Timer0Config(8), u3.Timer1Config(8)) #Sets up the dome tracking wheel


#***********************************************************************#
#2) Now define our main class, the LabjackServer.
class LabjackServer:

#Some properties relating to the relative encoder.
	dome_command = 0 		      #this is the distance the user wants the dome to move to be in position
	dome_moving = False     	      #a variable to keep track of whether the dome is moving due to a remote user command
	current_position = 0 		      #The position that the dome is at right now
	last_position_count = 0
	counts_per_degree = 11.83 	      #how many counts from the wheel encoder there is to a degree
	slitoffset = 53.83*counts_per_degree  #position, in counts, of the slits when home switch is activated
	counts_at_start = 0.0		      #This will record the counts from the labjack before the dome starts to move to a new position
				  	      #We need this to keep track of how far we have traveled.


	dome_correction_enabled = 1   #This sets whether we want to correct the azimuth for the dome so '20' actually
				      #points to '20' in the reference frame of the telescope and NOT the dome
				      #Initially set as enabled.
	domeAngleOffset = 90 	 #This is the angle between the line joining the center of the telescope and the center of the dome,
				 #and the line joining the telescope to the point on the dome the telescopes is pointing, when the dome
			 	 #is pointing North. Not actually 90, it needs to be measured.
	
	dome_direction_rotate = "stopped"


	domeRadius = 1 		  # Specify the radius in meters
	domeTelescopeDistance = 0 #The distance in meters between the center of the dome an the telescope

	home_sensor_count = 0 # whenever the homing sensor is activated the number changes positively by a random amount
			      # so every time the number changes, we know we've hit home.


#********************** a wee diagram to clear up the dome variables: *************
#
# (This is a birds eye view of the dome.)
#
#
#           North   P     /  < --- slit position for given azimuth
#              \    |    /  / <--- telescope line of sight for given azimuth
#               \   |   /  /
#                \  |  /  /
#                 \i| /  /
#                  \|/  /
#                   x  o                  x = center of the dome
#                                         o = position of telescope
#                                         distance between o to x = domeTelescopeDistance <-- code variable above
#                                         angle i = domeAngleOffset <-- code variable above
#					  The dome radius has not been shown in the diagram as it's difficult to draw
#					  circles in ascii
#                                         
# It is clear from the above diagram that if the telescope is not in the center of the dome
# when the telescope and the dome are sent to the same azimuth, their line of sights will not intersect
# and so the telescope could end up looking at the dome wall instead of out of the slits.
# For this reason we need to calculate the angle difference between the telescope line of sight
# and the dome slits 'line of sight' for every point on the dome circumference. This angle is what
# is refered to in the code as the 'dome correction'. The diargram is drawn so that the north vector and the line joining
# x and o are not perpendicular to keep the code general. It is mathematically easiest to calculate 
# the dome correction angle with respect to this perpendicular line labled P on the diagram and then add on the
# angle between North and P, (labled i in the diagram) after the calculation. Angle i is named the domeAngleOffset in the code.


# domeTelescopeDistance = the distance between x and o in the diagram
# domeAngleOffset = angle i (in degrees)

# In our labjack/dome set up we have a homing sensor a point on the circumference of the dome. Once every revolution
# this homing sensor will be activated and this allows us to keep the tracking of the dome position precise as errors 
# can accumulate after many revolutions. This homing sensor is at an arbitrary point on the domes circumference, so when
# it is activated, it does not necessarily mean that the dome is at 0 degrees, so we need to know what azimuth the dome
# is at when the homing sensor is activated and be sure to reset the dome position to this azimuth. In the code this angle
# is called the 'slitoffset' and is recorded in labjack counts.




#*************************************** List of user commands ***************************************#



	def cmd_humidity(self,the_command):
		''' Get the humidity from the E1050 probe '''
		humidity = LJPROBE.getHumidity()
		return str(humidity)
        
	def cmd_temperature(self,the_command):
		''' Get the temperature from the E1050 probe '''
		temperature = LJPROBE.getTemperature()
		return str(temperature)
        
	def cmd_ljtemp(self,the_command):
		''' Get the temperature of the labjack in Kelvin'''
		temperature = LJ.getTemperature()
		return str(temperature)
        
	def cmd_status(self,the_command):
		'''Return the status of the entire system.'''
 		return(str(self.current_position))

	def cmd_numHomes(self,the_command):
		'''Return the number of times the dome home sensor has been pressed.'''
 		home_output = str( (LJ.getFeedback( u3.Counter0() ))[0] )
		return home_output
	
	def cmd_domeCorrection(self,the_command): # I don't think we need this as we will always want to correct
		'''Used to turn the dome correction on or off (automatically set to on). When dome correction is on,
		the dome will move to the azimuth given to it, but that azimuith in the reference frame of the dome.
		This way if the telescope is at 20, a command to the dome will move to 20 with dome correction enabled
		will ensure the telescope and dome line up.'''
		commands = str.split(the_command)
		if len(commands) == 1 and self.dome_correction_enabled: return 'Dome correction enabled'
		elif len(commands) == 1 and not self.dome_correction_enabled: return 'Dome correction disabled'
		elif len(commands) == 2:
			if commands[1] == 'on': 
				self.dome_correction_enabled = 1
				return 'Dome correction now enabled'
			elif commands[1] == 'off': 
				self.dome_correction_enabled = 0
				return 'Dome correction now disabled'
			else: return 'ERROR invalid input'
		else: return 'Invalid input'
		

	def cmd_dome(self,the_command):
                '''Move the dome. Put a + or - before the number you input to move a certain distance
		from the current position, or just input the postion number where you want the dome to
		be positioned. Eg '+20' means 'move 20 degrees clockwise from current position'. '-20' 
		means 'move 20 degrees anticlockwise from current positon'. '20' means, move to 20 degrees 
		from North (North being at the defined 0 degrees point). Note if you want to move'-20 with 
		resects to north' please input '340'. Please only input integers. A decimal will not be read.
		Range is 0 to 360 for positions (negative positions wont give desired result) and +/- 180 for
		relative changes. Type "dome location" to get the current location.'''
		commands=str.split(the_command)
		dome_command_temp = 0 # We use this to keep track of our dome command and only change
				      # global self.dome_command when we have finished processing our value
		if self.dome_moving == True:
			return "Dome moving, input only available when the dome is stationary."
		elif len(commands) == 2 and commands[1] == 'location':
			return str(self.current_position)
		elif len(commands) == 2:
			self.counts_at_start=self.current_position
			user_command = commands[1]
			if user_command[0] == '+' or '-': #user has asked to move a certain amount from where we are now
				try: float(user_command)
				except Exception: return 'ERROR invalid input'
				while float(user_command) > 180: user_command = float(user_command) - 360
				while float(user_command) < -180: user_command = float(user_command) + 360

				degree_move = float(user_command)
				dome_command_temp = self.current_position + degree_move
			else:
				try: dome_command_temp = float(user_input)
				except Exception: return 'ERROR invalid input'

			if self.dome_correction_enabled:
				correction = math.asin((self.domeTelescopeDistance/self.domeRadius)*math.sin(math.radians(dome_command_temp + self.domeAngleOffset)))		
				#Above we have also changed coordinate systems.
				correctionDegrees = math.degrees(correction)
				#whether you add or minus the correction depends on the telescopeAzimuth size
				if dome_command_temp <= (180- self.domeAngleOffset) and dome_command_temp >= (360-self.domeAngleOffset): 
					dome_command_temp = correctionDegrees + self.dome_comand
				elif dome_command_temp > (180 - self.domeAngleOffset) and dome_command_temp < (360-self.domeAngleOffset): 
					dome_command_temp = dome_command_temp - correctionDegrees
				else: return 'ERROR invalid number input.'

			# we only record our dome position between 0 and 360 degrees
			while dome_command_temp > 360: dome_command_temp -= 360
			while dome_command_temp < 0: dome_command_temp += 360
			self.counts_at_start = self.current_position
			self.dome_command = dome_command_temp
			self.dome_moving = True #This will tell background task 'dome_location' to call task 'dome_moving'
			degree_distance = self.dome_command - self.dome_position
			if degree_distance > 180: 
				self.dome_relays("anticlockwise")
				self.direction_dome_moving = "anticlockwise"
			elif degree_distance > 0 and degree_distance < 180: 
				self.dome_relays("clockwise")
				self.direction_dome_moving = "clockwise"
			elif degree_distance < -180: 
				self.dome_relays("clockwise")
				self.direction_dome_moving = "clockwise"
			elif degree_distance < 0 and degree_distance > -180: 
				self.dome_relays("anticlockwise")
				self.direction_dome_moving = "anticlockwise"
			else: return 'ERROR'
			
			return "Dome's current position: "+str(self.current_position)+" degrees. Dome moving."
		else: return 'ERROR invalid input'

                
#******************************* End of user commands ********************************#
                

	def dome_location(self):
		temp = LJ.getFeedback(u3.QuadratureInputTimer()) #This will constantly update the current position of the dome
		#self.current_position = float(temp[-1])		 #This enables us to keep track even if the dome is manually moved
		position_count = float(temp[-1])

		# convert into degrees here!

		current_position_temp = self.current_position + (position_count - self.last_position_count)/self.counts_per_degree
		while current_position_temp > 360: current_position_temp = current_position_temp - 360
		while current_position_temp < 0: current_position_temp = current_position_temp + 360
		self.current_position = current_position_temp
		self.last_position_count = position_count
		
		# Perhaps here instead of using counts directly, add them on to the last known position
		# We can test to see if this leads to any great loss in accuracy 


		f = open('dome_position.dat','w')
		f.write("Dome is in position "+str(self.current_position)+" degrees.")
		f.close()
 		if self.dome_moving == True:
			if self.dome_direction_rotate == "clockwise": 
				if self.dome_command == 360: self.dome_command = 0
				if (self.current_position >= self.dome_command):
					self.dome_relays("stop")
					self.dome_moving == False
			elif self.dome_direction_rotate == "anticlockwise":
				if self.dome_command == 0: self.dome_command = 360
				if (self.current_position <= self.dome_command):
					self.dome_relays("stop")
					self.dome_moving == False



	def azimuth_telescope_to_dome(self,command):
		'''This will convert the azimuth given from the telescope to a corresponding azimuth for the dome
		so that the line of sight of the telescope is always in line with the slits.'''
		commands = str.split(command)
		if len(commands) != 1: return 'Error'
		telescopeAzimuth = commands[0]
		correction = asin((self.domeTelescopeDistance/self.domeRadius)*math.sin(math.radians(telescopeAzimuth + self.domeAngleOffset)))
		#Above we have also changed coordinate systems.
		correctionDegrees = math.degrees(correction)
		#whether you add or minus the correction depends on the telescopeAzimuth size
		if telescopeAzimuth <= (180-self.domeAngleOffset) and telescopeAzimuth >= (360-self.domeAngleOffset): correctedAzimuth = correctionDegrees + telescopeAzimuth
		if telescopeAzimuth > (180-self.domeAngleOffset) and telescopeAzimuth < (360-self.domeAngleOffset): correctedAzimuth = telescopeAzimuth - correctionDegrees
		return str(correctedAzimuth)


	def dome_relays(self, command):
		'''Move the dome clockwise, anticlockwise or stop dome motion'''
		commands = str.split(command)
		#if len(commands) != 1: return 'ERROR'
		#if commands[0] == 'clockwise': # command to move dome clockwise
		#elif commands[0] == 'anticlockwise': # command to move dome anticlockwise
		#elif commands[0] == 'stop': # command to stop dome motion
		#else: return 'ERROR'



	def home_tracker(self):
		'''Return the number of times the dome home sensor has been pressed.'''
 		home_output = int(str( (LJ.getFeedback( u3.Counter0() ))[0] ))
		if home_output != self.home_sensor_count:  # We've hit home!
			self.home_sensor_count = home_output
			if self.dome_slewing_enabled:
				self.current_position = self.azimuth_telescope_to_dome(0) # Correct value not known yet
			else: self.current_position = 0
			return 1
		return 0



