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
LJPROBE=ei1050.EI1050(LJ, enablePinNum=0, dataPinNum=1, clockPinNum=2)
LJ.configIO(NumberOfTimersEnabled = 2)
LJ.getFeedback(u3.Timer0Config(8), u3.Timer1Config(8))

#***********************************************************************#
#2) Now define our main class, the LabjackServer.
class LabjackServer:

#Variables not used yet...
    dome_status = 'HOME'   
    slit_status = 'closed'  
    weather_status = 'NULL' #Needs to come from connection to weather server. Who is the client?
    
#Some properties relating to the relative encoder.
    wheel_pos = 0.0
    wheel_command = 0
    wheel_moving = False
    current_pos = 0 #MJI Doesn't understand the difference between WHEEL_POS, WHEEL_COMMAND and this... Needs comments

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
        return(str(self.wheel_pos))
    
    def cmd_wheel(self,the_command):
        '''Move the wheel'''
        commands=string.split(the_command)
        if self.wheel_moving == True: 
            return "Wheel already moving"
        elif len(commands) ==1:
            return "Wheel\'s current position: "+str(self.wheel_pos)+". Wheel NOT moving."
        else:
            self.wheel_command = commands[1]
            self.wheel_moving = True
            return "Wheel''s current position: "+str(self.wheel_pos)+". Moving Wheel."
        
#****** End of user commands *******
        
#This is the background job that defines if the wheel is moving.
    def dome_rotate(self,command):
        command = float(command)
        command = command*48   #turns number of turns into number of counts
        temp = LJ.getFeedback(u3.QuadratureInputTimer())
        temp2 = temp[-1]
        temp2 = temp2 - (self.wheel_pos*48)
        destination = command + self.wheel_pos
        if command >= 0:
            if temp2 < command:
                self.wheel_moving = True
                temp = LJ.getFeedback(u3.QuadratureInputTimer())
                self.current_pos = float(temp[-1])
            else: self.wheel_moving = False
        elif command < 0:
            if temp2 > command:
                self.wheel_moving = True
                temp = LJ.getFeedback(u3.QuadratureInputTimer())
                self.current_pos = float(temp[-1])
            else: self.wheel_moving = False
        else: 
            return "ERROR"
        
        if self.wheel_moving == False:
            turns = (self.current_pos/48.0) - self.wheel_pos
            pos = self.wheel_pos
            pos = pos + turns
            self.wheel_pos = pos
            return turns
        else: return
        
#This will 'move' the wheel if there has been a command which has not yet completed
#obviously at the moment the wheel is moved manually
    def wheel_move(self):
        if self.wheel_moving == True:
            self.dome_rotate(self.wheel_command)
                


