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
	slitoffset = int(68.83*counts_per_degree)    # The position, in degrees, of the slits when the home switch is activated


	total_counts = 0		     	# The total number of counts since we started the program, raw output from wheel
	total_count_at_last_home = 0	     	# The total counts we had last time we passed through home
	current_position = 0 		    	# The position of the dome right now in counts (counts reset at home position)
	counts_at_start = 0		     	# Record the counts from the wheel before the dome starts to move		  	
	counts_to_move = 0		    	# Number of counts the wheel needs to move to get to destination
	home_sensor_count = 0		     	# Whenever the homing sensor is activated the Counter0 labjack output changes 
					    	# by a positive amount, so every time the number changes, we know we've hit home.
					     	# home_sensor_count keeps track of this change

	homing = False
	watchdog_last_time = time.time()        # The watchdog timer.
	watchdog_max_delta = 10000                # more than this time between communications means there is a problem


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

		if len(commands) == 2 and commands[1]== 'moving':
			return str(self.dome_moving)
		if len(commands) == 2 and commands[1] == 'location':
			return str(self.current_position/self.counts_per_degree)+' total counts: '+str(self.total_counts)+' num homes: '+str(self.home_sensor_count)
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
		if len(commands) > 2: return 'ERROR'
		if len(commands) == 1: return str(self.slits_open)
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
		'''Let the labjack know that all is OK and the slits can stay open'''
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
		if current_position_temp > int(360*self.counts_per_degree): current_position_temp = current_position_temp - int(360*self.counts_per_degree)
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
#		if self.slits_open:
#			print math.fabs(time.time() - self.watchdog_last_time)
		if (math.fabs(time.time() - self.watchdog_last_time) > self.watchdog_max_delta) and (self.slits_open==True):
			    self.cmd_slits('slits close')
			    self.watchdog_last_time = time.time()
		            print 'ERROR: No active communications. Slits closing.'
