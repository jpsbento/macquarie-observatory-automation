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

#IP = '' #set up a server so the telescope can talk to the labjack to update dome position.
#PORT = 23469
#ADS = (IP, PORT)

#!!! Think about this !!!
#server = socket(AF_INET, SOCK_STREAM)
#server.bind(ADS)
#server.setblocking(0)
#server.listen(1) #will allow 1 client to connect with server, can only have one telescope in charge at once

#server.setsockopt(1, 2, 1)

#***********************************************************************#
#2) Now define our main class, the LabjackServer.
class LabjackServer:

#Some properties relating to the relative encoder.
	dome_command = 0 		      #this is the distance the user wants the dome to move to be in position
	dome_moving = False     	      #a variable to keep track of whether the dome is moving due to a remote user command
	current_pos = 0 		      #The position that the dome is at right now
	counts_per_degree = 11.83 	      #how many counts from the wheel encoder there is to a degree
	slitoffset=53.83*counts_per_degree    #position, in counts, of the slits when home switch is activated
	counts_at_start = 0.0		      #This will record the counts from the labjack before the dome starts to move to a new position
				  	      #We need this to keep track of how far we have traveled.
#	counts_per_degree = 11.89 #at the moment is set to counts per turns, we need to measure counts per degree
#	slitoffse=53.83*counts_per_degree #position of the slits when home switch is activated in counts
	countsatstart = 0.0
	CLIENTS = []
#	input = [server]

	dome_correction_enabled = 1   #This sets whether we want to correct the azimuth for the dome so '20' actually
				      #points to '20' in the reference frame of the telescope and NOT the dome
				      #Initially set as enabled.
	domeoffset = 90  #This is the angle between the line joining the center of the telescope and the center of the dome,
			 #and the line joining the telescope to the point on the dome the telescopes is pointing, when the dome
			 #is pointing North. Not actually 90, it needs to be measured.


	domeRadius = 1
	domeTelescopeDistance = 0 #The distance between the center of the dome an the telescope
#*************************************************************************#
#All the definitions used are listed here

#definition for weather checking
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
 		return(str(self.current_pos/self.counts_per_degree)+" degrees.")

	def cmd_numHomes(self,the_command):
		'''Return the number of times the dome home sensor has been pressed.'''
 		return str( (LJ.getFeedback( u3.Counter0() ))[0] )
	
	def cmd_domeCorrection(self,the_command):
		'''Used to turn the dome correction on or off (automatically set to on). When dome correction is on,
		the dome will move to the azimuth given to it, but that azimuith in the reference frame of the dome.
		This way if the telescope is at 20, a command to the dome will move to 20 with dome correction enabled
		will ensure the telescope and dome line up.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == 'on': dome_correction_enabled = 1
			elif commands[1] == 'off': dome_correction_enabled = 0
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
		relative changes'''
		commands=str.split(the_command)
		if self.dome_moving == True:
			return "Dome moving, input only available when the dome is stationary."
		elif len(commands) == 1:
			return "Dome's current position: "+str(self.current_pos/self.counts_per_degree)+" degrees from the domes frame of reference. Dome NOT moving."
		elif len(commands) == 2:
			self.counts_at_start=self.current_pos
			self.dome_command = commands[1] #Grabs the number the user input
			temp = list(self.dome_command)  #we use the array 'temp' to make sure we have a correct input
			degree_move = 0.0
			newdegree_move = 0.0
			distance = 0
			correction = 0
			if temp[0] == '+' or temp[0] == '-': #user has asked to move a certain amount from where we are now
				if temp[0] == '+': sign = 1 #Keep track of the direction the user input
				else: sign = -1     #must have input a nedomeTelescopeDistancegative number
				del temp[0]
				temp2 = ''
				for i in len(temp): #put back together to get a number back out
					if temp[i].isdigit():
						temp2 += temp[i]
					else: 
						return 'ERROR invalid input'
					if int(temp2) > 180 or int(temp2) < -180: return 
						#break
				degree_move = float(temp2)*sign
				#put in some from of thing to stop billions of rotations.	
			#if above statement is false, user has asked to go to a specific degree location
			elif self.dome_command.isdigit():
				if dome_correction_enabled:
					correction = asin((self.domeTelescopeDistance/self.domeRadius)*math.sin(math.radians(self.dome_command + domeoffset)))		
					#Above we have also changed coordinate systems.
					correctionDegrees = math.degrees(correction)
					#whether you add or minus the correction depends on the telescopeAzimuth size
					if self.dome_command <= (180- self.domeoffset) and self.dome_command >= (360-self.domeoffset): self.dome_command = correctionDegrees + self.dome_comand
					elif self.dome_command > (180 - self.domeoffset) and self.dome_command < (360-self.domeoffset): self.dome_command = self.dome_command - correctionDegrees
					else: return 'ERROR invalid number input.'
				degree_move = float(self.dome_command) - float(self.dome_pos) #where you want to go - where you are now to convert into
			else: return "ERROR, invalid input"

			while float(degree_move) > 180:
				degree_move = (float(degree_move) - 360) #This will minimise the motion of the dome rotation
			while float(degree_move) < -180:
				degree_move = (float(degree_move) + 360) #The same as above but for the other direction
			self.dome_command = str(float(degree_move))  #setting the variable to be sent to 'dome_rotate'
			#else: return "ERROR, although I shouldn't be able to get here."
			self.dome_moving = True #This will tell background task 'dome_location' to call task 'dome_moving'
			return "Dome's current position: "+str(self.current_pos/self.counts_per_degree)+" degrees. Dome moving."
		else: return 'ERROR invalid input'

#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^#
	def cmd_moveDome(self,the_command):
		commands = str.split(the_command)
		dome_command = commands[1]

		# Need current position.

		client_list[0].send(dome_command)
		if is_float_try(dome_command):

			if (dome_command - dome_current_position) > 0 and abs(dome_command - dome_current_position) <= 180: send command to dome to move clockwise
			elif (dome_command - dome_current_position) > 0: send command to dome to move anticlockwise
			elif (dome_command - dome_current_position) < 0 and abs(dome_command - dome_current_position) <= 180: send command to dome to move anticlockwise
			elif (dome_command - dome_current_position) < 0: send command to dome to move clockwise
			elif dome_command == dome_current_position: dome_moving = False # no command to be sent
			else: return 'Some form of error.'

		elif dome_command[0] == '+': send command to dome to move clockwise
		elif dome_command[1] == '-': send command to dome to move anticlockwise
		else: return 'ERROR invalid input'

		while dome_moving = 1
			labjack_output = client_list.recv(1024) #change this to just calling as a background task
			if labjack_output == 'dome at destination' # or whatever the output is when it gets to it's destination
				dome_moving == 0
				send command to the dome to stop moving
		return 'Dome in position'
                
#****** End of user commands *******
                
#This is the background job that defines if the dome is moving.
	def dome_rotate(self,command):
		distance_to_travel = float(command) #distance in degrees
		counts_to_travel = distance_to_travel*self.counts_per_degree #covert degrees to counts
		print "current_pos "+str(self.current_pos)
		if counts_to_travel >= 0:  #clockwise motion
			if self.counts_at_start+counts_to_travel > self.current_pos: #Check if we are in position yet
  				self.dome_moving = True
		#print self.current_pos
			else: self.dome_moving = False
		elif counts_to_travel < 0: #counterclockwise motion
				if self.counts_at_start+counts_to_travel < self.current_pos:
					self.dome_moving = True
				else: self.dome_moving = False
		else:
			return "ERROR"
		if self.dome_moving == False:
			#print "Dome in position: "+str(self.current_pos/self.counts_per_degree)+" degrees."
			return "Dome in position: "+str(self.current_pos/self.counts_per_degree)+" degrees."
			print "wheel done working "+turns
		else: return
       	
#This will 'move' the dome if there has been a command which has not yet completed
#obviously at the moment the dome is moved manually
	def dome_location(self):
		temp = LJ.getFeedback(u3.QuadratureInputTimer()) #This will constantly update the current position of the dome
		self.current_pos = float(temp[-1])		 #This enables us to keep track even if the dome is manually moved
		f = open('dome_position.dat','w')
		f.write("Dome is in position "+str(self.current_pos/self.counts_per_degree)+" degrees.")
		f.close()
 		if self.dome_moving == True:
			self.dome_rotate(str(self.dome_command))



	def azimuth_telescope_to_dome(self,command):
		# maybe put most of this information within the telescope class so it knows its orientation
		# however we have information for both the telescope and the dome here...
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

