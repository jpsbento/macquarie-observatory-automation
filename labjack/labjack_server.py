#*********************************************************************#
#                  Code for the labjack server                        #
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
#   module scope, lets give them capitals. These are initialized, byt
#   not written to within our module. Two instances of the LabjackServer
#   would then write to the *same* labjack hardware, but could e.g. 
#   do different parts of the job. You's almost certainly *not* want to do 
#   this.
LJ=u3.U3()
LJPROBE=ei1050.EI1050(LJ, enablePinNum=0, dataPinNum=1, clockPinNum=2) #Sets up the humidity probe
LJ.configIO(NumberOfTimersEnabled = 2)
LJ.getFeedback(u3.Timer0Config(8), u3.Timer1Config(8)) #Sets up the dome tracking wheel

#***********************************************************************#
#2) Now define our main class, the LabjackServer.
class LabjackServer:

#Some properties relating to the relative encoder.
    dome_command = 0 #this is the distance the user wants the dome to move to be in position
    dome_moving = False #a variable to keep track of whether the dome is moving due to a remote user command
    current_pos = 0 #The position that the dome is at right now
    counts_per_degree = 11.82 #how many counts from the wheel encoder there is to a degree
    slitoffset=53.83*counts_per_degree #position, in counts, of the slits when home switch is activated
    counts_at_start = 0.0 #This will record the counts from the labjack before the dome starts to move to a new position
			  #We need this to keep track of how far we have traveled.

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
    
    def cmd_dome(self,the_command):
        '''Move the dome. Put a + or - before the number you input to move a certain distance
	from the current position, or just input the postion number where you want the dome to
	be positioned. Eg '+20' means 'move 20 degrees clockwise from current position'. '-20' 
	means 'move 20 degrees anticlockwise from current positon'. '20' means, move to 20 degrees 
	from North (North being at the defined 0 degrees point). Note if you want to move'-20 with 
	resects to north' please input '340'. Please only input integers. A decimal will not be read.'''
        commands=str.split(the_command)
        if self.dome_moving == True:
            return "Dome moving, input only available when the dome is stationary."
        elif len(commands) == 1:
            return "Dome's current position: "+str(self.current_pos/self.counts_per_degree)+" degrees. Dome NOT moving."
        else:
            self.counts_at_start=self.current_pos
            self.dome_command = commands[1] #Grabs the number the user input
	    temp = list(self.dome_command)  #we use the array 'temp' to make sure we have a correct input
	    degree_move = 0.0
	    newdegree_move = 0.0
	    sign = 'null'   #This will keep track of whether we are moving in a clockwise or anticlockwise direction
	    extra_turns = 0 #This will keep track of any extra turns the user input.. ie if they put 500 degrees move
			    #that would be extra_turn = 1 as the dome only actually needs to move 140 degrees
	    if temp[0] == '+' or temp[0] == '-': #user has asked to move a certain amount from where we are now
		sign = temp[0]
		del temp[0]
	    else: 				#user has asked to go to a specific degree location
		if self.dome_command.isdigit():
		   distance = self.dome_command - self.dome_pos #where you want to go - where you are now to convert into
		   temp = list(distance)                        #a distance to move from the current position
		   if temp[0] == '-':  #we want to move clockwise
			sign = '-'
			del temp[0]
		   else: sign = '+'  #we want to move anticlockwise
		else: return "ERROR, invalid input"
	    for i in range(len(temp)):
		degree_move = degree_move + temp[i] #We put the array back together to make a complete number again
	    if degree_move.isdigit():               #Checking if the user input a number
		extra_turns = int(float(degree_move)/360) #Make sure we are only asking the dome to move less than one turn
		reduced_degree_move = int(degree_move) - int(extra_turns)*360 #Update the degrees to move
		if int(reduced_degree_move) > 180:
		   minimised_degree_move = 360 - reduced_degree_move #This will minimise the motion of the dome rotation
		   if temp[0] == '-': sign = '+'   		 #we need to change the direction we are moving in
		   if temp[0] == '+': sign = '-'
		if sign == '+': 
		   self.dome_command = minimised_degree_move  #setting the variable to be sent to 'dome_rotate'
		   return
		elif sign == '-': 
		   self.dome_command = str(-1*int(minimised_degree_move))
		   return
		else: return "ERROR, although I shouldn't be able to get here."
	    else: return "ERROR, invalid input"
            self.dome_moving = True #This will tell background task 'dome_location' to call task 'dome_moving'
            return "Dome's current position: "+str(self.current_pos/self.counts_per_degree)+" degrees. Dome moving."
        
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
               




