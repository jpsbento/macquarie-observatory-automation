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
import time

#***********************************************************************#
#2) Set up the labjack. As the LJ and LJPROBE are declared in the global
#   module scope, lets give them capitals. These are initialized, but
#   not written to within our module. Two instances of the LabjackServer
#   would then write to the *same* labjack hardware, but could e.g. 
#   do different parts of the job. You's almost certainly *not* want to do 
#   this.
LJ=u3.U3()
LJPROBE=ei1050.EI1050(LJ, enablePinNum=0, dataPinNum=1, clockPinNum=2) #Sets up the humidity probe
LJ.configIO(NumberOfTimersEnabled = 2, EnableCounter0 = 1, TimerCounterPinOffset=8)
LJ.getFeedback(u3.Timer0Config(8), u3.Timer1Config(8)) #Sets up the dome tracking wheel
#DAC0_REGISTER = 5000  # clockwise movement
#DAC1_REGISTER = 5002  # anticlockwise movement
#LJ.writeRegister(DAC0_REGISTER, 2) # command to stop movement
#LJ.writeRegister(DAC1_REGISTER, 2)
LJ.setFIOState(u3.FIO7, state=0) #command to close slits. A good starting point.
LJ.setFIOState(u3.FIO4, state=1) #command to stop movement
LJ.setFIOState(u3.FIO5, state=1) #command to stop movement

# ^ This is required to make sure the dome does not start moving when we start the code.
# With the current set up, absoultely no voltage does not move the relays, but the labjack is not
# sensitive enough to give out no voltage at all, there is always a small amount and this is enough
# for the dome to start moving. If we give it too much ie 2 volts, the dome will stop moving.
# So for now, setting the DAC reigster to zero is to activate movement, and setting them to 2 
# halts movement


#***********************************************************************#
#2) Now define our main class, the LabjackServer.
class LabjackServer:

#Some properties relating to the relative encoder:

	dome_moving = False     	    	# A variable to keep track of whether the dome is moving due to a remote user command
	slits_open = False

	counts_per_degree = 11.83 	   	# how many counts from the wheel encoder there is to a degree
	slitoffset = int(53.83*counts_per_degree)    # The position, in degrees, of the slits when the home switch is activated


	total_counts = 0		     	# The total number of counts since we started the program, raw output from wheel
	total_count_at_last_home = 0	     	# The total counts we had last time we passed through home
	current_position = 0 		    	# The position of the dome right now in counts (counts reset at home position)
	counts_at_start = 0		     	# Record the counts from the wheel before the dome starts to move		  	
	counts_to_move = 0		    	# Number of counts the wheel needs to move to get to destination
	home_sensor_count = 0		     	# Whenever the homing sensor is activated the Counter0 labjack output changes 
					    	# by a positive amount, so every time the number changes, we know we've hit home.
					     	# home_sensor_count keeps track of this change


	dome_correction_enabled = 0  	      	# This sets whether we want the azimuth of the dome to be corrected for the telescope.
				              	# In general with will be set to 1, for basic testing it's easiest if it's set to 0

	domeRadius = 1 		 	     	# Specify the radius of the dome in meters
	domeTelescopeDistance = 0 	      	# The distance in meters between the center of the dome and the telescope
	domeAngleOffset = 0 	 	      	# This is the angle between the line joining the center of the telescope and the center 
					      	# of the dome, and the line joining the telescope to the point on the dome the telescopes 
						# is pointing, when the dome is pointing North. Not actually 0, it needs to be measured.

	homing = False
	watchdog_last_time = time.time()        # The watchdog timer.
	watchdog_max_delta = 1000                # more than this time between communications means there is a problem

#********************** a wee diagram to clear up the dome variables: **********************#
#
# (This is a birds eye view of the dome.)
#
#
#           North         /  < --- slit position for given azimuth
#              \         /  / <--- telescope line of sight for given azimuth
#               \       /  /
#                \     /  /
#                 \   /  /
#                i \ /  /
#    zero ----------x  o                  x = center of the dome
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
# x and o are not parallel to keep the code general. It is mathematically easiest to calculate 
# the dome correction angle with respect to the line joining x and o labled 'zero' on the diagram and then add on the
# angle between North and zero, (labled i in the diagram) after the calculation. Angle i is named the domeAngleOffset in the code.


# domeTelescopeDistance = the distance between x and o in the diagram
# domeAngleOffset = angle i (in degrees)

# In our labjack/dome set up we have a homing sensor a point on the circumference of the dome. Once every revolution
# this homing sensor will be activated and this allows us to keep the tracking of the dome position precise as errors 
# can accumulate after many revolutions. This homing sensor is at an arbitrary point on the domes circumference, so when
# it is activated, it does not necessarily mean that the dome is at 0 degrees, so we need to know what azimuth the dome
# is at when the homing sensor is activated and be sure to reset the dome position to this azimuth. In the code this angle
# is called the 'slitoffset' and is recorded in counts.

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
 		return(str(self.current_position/self.counts_per_degree))

	def cmd_numHomes(self,the_command):
		'''Return the number of times the dome home sensor has been pressed.'''
 		#home_output = str( (LJ.getFeedback( u3.Counter0() ))[0] )
		return str(self.home_sensor_count)
	
	def cmd_domeCorrection(self,the_command):
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

		if len(commands) == 2 and commands[1] == 'location':
			if not self.dome_correction_enabled:
				return str(self.current_position/self.counts_per_degree)+' total counts: '+str(self.total_counts)+' num homes: '+str(self.home_sensor_count)
			else:
				return self.azimuth_dome_to_telescope(str(self.current_position/self.counts_per_degree))+' total counts: '+str(self.total_counts)+' num homes: '+str(self.home_sensor_count)
		elif len(commands) == 2 and commands[1] == 'stop':
			self.dome_relays("stop")
			self.dome_moving = False
			self.homing = False
			return 'Dome motion stopped'
		elif self.dome_moving == True:
			return "Dome moving, input only available when the dome is stationary."
		elif len(commands) == 2 and commands[1] == 'home':
			self.dome_relays("clockwise")
#			self.temp_home = self.home_sensor_count
			self.homing = True
#			while self.homing:
#				print 'home sensor count: '+str(self.home_sensor_count)
#				print 'temp count: '+str(self.temp_home)
#				print 'raw output: '+str( (LJ.getFeedback( u3.Counter0() ))[0] )
#				if self.temp_home != self.home_sensor_count:
#					self.homing = False
#					self.dome_relays("stop")
#					return 'Dome is homed'
			return 'Dome Homing'
		elif len(commands) == 2:
			user_command = commands[1]
			counts_to_move_temp = self.analyse_dome_command(user_command)
			print str(counts_to_move_temp)
			try: counts_to_move_temp = int(counts_to_move_temp)
			except Exception: return 'ERROR'

			self.counts_at_start = self.total_counts
			self.dome_moving = True #This will tell background task 'dome_location' to call task 'dome_moving'
			self.counts_to_move = counts_to_move_temp
			if self.counts_to_move == 0: 
				self.dome_moving = False
				return 'Dome already at given azimuth'
			elif self.counts_to_move > 0: 
				self.dome_relays("clockwise")
			elif self.counts_to_move < 0: 
				self.dome_relays("anticlockwise")
			else: return 'ERROR'
			
			return "Dome's current position: "+str(self.current_position/self.counts_per_degree)+" degrees. Dome moving."
		else: return 'ERROR invalid input not a number'


	def cmd_slits(self, the_command):
		'''Command to open and close the slits.'''
		commands = str.split(the_command)
		if len(commands) != 2: return 'ERROR'
		self.watchdog_last_time = time.time()
		if commands[1] == 'open':
			LJ.setFIOState(u3.FIO7, state=1)
			self.slits_open = True
			return 'slits open'
		elif commands[1] == 'close':
			LJ.setFIOState(u3.FIO7, state=0)			
			self.slits_open=False
			return 'slits closed'
		else: return 'ERROR'

	def cmd_ok(self, the_command):
		"Let the labjack know that all is OK and the slits can stay open"
		self.watchdog_last_time = time.time()
		return 'Watchdog timer reset.'

 	def cmd_BackLED(self, the_command):
		'''Command to control IR LED backfeed.'''
		commands = str.split(the_command)
		if len(commands) != 2: return 'ERROR'
		if commands[1] == 'on':
		#	LJ.setFIOState(u3.FIO7, state=1) waiting to install to define port			
			return 'LED on'
		elif commands[1] == 'off':
			# LJ.setFIOState(u3.FIO7, state=0) waiting to install to define port			
			return 'LED off'
		else: return 'ERROR'               
		
#******************************* End of user commands ********************************#              

	def dome_location(self):
		raw_wheel_output = LJ.getFeedback(u3.QuadratureInputTimer()) #This will constantly update the current position of the dome

		self.total_counts = -int(raw_wheel_output[-1])
		#print 'total counts: '+str(self.total_counts)
		#print 'counts at last home: '+str(self.total_count_at_last_home)
		current_position_temp = self.total_counts - self.total_count_at_last_home + self.slitoffset # what is our relative distance to home?
		#print 'current position temp: '+str(current_position_temp)
		if current_position_temp < 0: current_position_temp = int(360*self.counts_per_degree) + current_position_temp

		self.current_position = current_position_temp
		#print 'current position: '+str(self.current_position)
		#print '\n'
 		if self.dome_moving == True:

			if self.counts_to_move <= 0:
				if self.total_counts <= self.counts_at_start + self.counts_to_move:
					self.dome_relays("stop")
					self.dome_moving = False
			elif self.counts_to_move > 0:
				if self.total_counts >= self.counts_at_start + self.counts_to_move:
					self.dome_relays("stop")
					self.dome_moving = False
			else: 
				print 'ERROR IN DOME LOCATION'



	def azimuth_telescope_to_dome(self,command):
		'''This will convert the azimuth given from the telescope to a corresponding azimuth for the dome
		so that the line of sight of the telescope is always in line with the slits.'''
		commands = str.split(command)
		if len(commands) != 1: return 'Error'
		try: telescopeAzimuth = float(commands[0])
		except Exception: return 'ERROR'
		correction = math.asin((self.domeTelescopeDistance/self.domeRadius)*math.sin(math.radians(telescopeAzimuth + self.domeAngleOffset)))

		if (telescopeAzimuth + self.domeAngleOffset) <= 180: 
			correctedAzimuth = telescopeAzimuth + math.degrees(correction)
			return str(correctedAzimuth)

		elif (telescopeAzimuth + self.domeAngleOffset) > 180:
			correctedAzimuth = telescopeAzimuth - math.degrees(correction)
			return str(correctedAzimuth)
		else:
			print 'ERROR IN AZIMUTH TELESCOPE TO DOME'
			return telescopeAzimuth


	def azimuth_dome_to_telescope(self,command):
		'''Convert the azimuth of the dome into the telescopes coordinate system.'''
		commands = str.split(command)
		if len(commands) != 1: return 'ERROR'
		try: domeAzimuth = float(commands[0])
		except Exception: return 'ERROR'
		z = math.sqrt(self.domeRadius**2+self.domeTelescopeDistance**2-2*self.domeRadius*self.domeTelescopeDistance*math.cos(math.radians(180 - domeAzimuth)))
		correction = math.acos((self.domeTelescopeDistance**2 + self.domeRadius**2 - z**2)/(-2*z*self.domeRadius))
		if (domeAzimuth + self.domeAngleOffset) <= 180: # and (domeAzimuth + self.domeAngleOffset) >= 0:
			correctedAzimuth = domeAzimuth - math.degrees(correction)
			while correctedAzimuth > 360: correctedAzimuth = correctedAzimuth - 360
			while correctedAzimuth < 0: correctedAzimuth = correctedAzimuth + 360
			return correctedAzimuth

		elif (domeAzimuth + self.domeAngleOffset) > 180: # and (domeAzimuth + self.domeAngleOffset) <= 360:
			correctedAzimuth = domeAzimuth + math.degrees(correction)
			while correctedAzimuth > 360: correctedAzimuth = correctedAzimuth - 360
			while correctedAzimuth < 0: correctedAzimuth = correctedAzimuth + 360
			return correctedAzimuth
		else: 
			print 'ERROR IN AZIMUTH DOME TO TELESCOPE'
			return domeAzimuth

#    Diagram to help explain azimuth_dome_to_telescope function
#   
#                        /| <----- telescope azimuth
#                       /j|
#          dome ---->  /  |
#          azimuth    /   |
#                    /    |    	Here we want to get angle j as this is the difference between the 
#               |   /     |	dome's actual azimuth and the azimuth command sent to the telescope
#   azimuth --> |  /      |	in the dome's coordinate system.
#   sent to     |j/       |
#   telescope   |/        |
#   in domes    -----------
#   coordinate system
# 
# We are just working backwards from the azimuth_telescope_to_dome function above.
# We want to get the same angle, but we have different starting information so have
# to use a different process.
#

	def dome_relays(self, command): # 
		'''Move the dome clockwise, anticlockwise or stop dome motion'''
		commands = str.split(command)
		if len(commands) != 1: return 'ERROR'
		if commands[0] == 'clockwise': 
			LJ.setFIOState(u3.FIO4, state=0) 
			LJ.setFIOState(u3.FIO5, state=1)
#			LJ.writeRegister(DAC1_REGISTER, 2)
#			LJ.writeRegister(DAC0_REGISTER, 0) # command to move dome clockwise, possibly change to 0.5
		elif commands[0] == 'anticlockwise': 
			LJ.setFIOState(u3.FIO4, state=1) 
			LJ.setFIOState(u3.FIO5, state=0)
#			LJ.writeRegister(DAC0_REGISTER, 2)
#			LJ.writeRegister(DAC1_REGISTER, 0) # command to move dome anticlockwise
		elif commands[0] == 'stop':
			LJ.setFIOState(u3.FIO4, state=1) 
			LJ.setFIOState(u3.FIO5, state=1)
#			LJ.writeRegister(DAC0_REGISTER, 2) # command to stop movement
#			LJ.writeRegister(DAC1_REGISTER, 2)
		else: return 'ERROR'



	def home_tracker(self):
		'''Return the number of times the dome home sensor has been pressed.'''
 		#home_output = int(str( (LJ.getFeedback( u3.Counter0() ))[0] ))
		#print self.home_sensor_count
		if int(str( (LJ.getFeedback( u3.Counter0() ))[0] )) != self.home_sensor_count:  # We've hit home!
			self.home_sensor_count = int(str( (LJ.getFeedback( u3.Counter0() ))[0] ))
			self.total_count_at_last_home = self.total_counts # We have a new count as our zero reference point
			if self.homing:
				self.dome_relays("stop")
				self.homing = False



	def analyse_dome_command(self,command):
		if str(command)[0] == '+' or str(command)[0] == '-': #user has asked to move a certain amount from where we are now

			try: dome_command_temp = float(command)
			except Exception: return 'ERROR'
			while dome_command_temp > 180: dome_command_temp -= 360
			while dome_command_temp < -180: dome_command_temp += 360

			counts_to_move = int(dome_command_temp*self.counts_per_degree)
			return str(counts_to_move)
		else:
			try: dome_command_temp = float(command)
			except Exception: return 'ERROR'
			if self.dome_correction_enabled: dome_command_temp = self.azimuth_telescope_to_dome(dome_command_temp)
			while dome_command_temp > 360: dome_command_temp -= 360
			while dome_command_temp < 0: dome_command_temp += 360
			counts_to_move = int(dome_command_temp*self.counts_per_degree) - self.current_position
			#print 'current position: '+str(self.current_position)
			#print 'dome command: '+str(dome_command_temp*self.counts_per_degree)
			#print 'counts to move: '+str(counts_to_move)
			while counts_to_move > 180*self.counts_per_degree: counts_to_move = int(counts_to_move - 360*self.counts_per_degree)
			while counts_to_move < -180*self.counts_per_degree: counts_to_move = int(counts_to_move + 360*self.counts_per_degree)
			return str(counts_to_move)

	def watchdog_timer(self):
		if (math.fabs(time.time() - self.watchdog_last_time) > self.watchdog_max_delta) and (self.slits_open==True):
			    self.cmd_slits('slits close')
			    self.watchdog_last_time = time.time()
		            print 'ERROR: No active communications. Slits closing.'
