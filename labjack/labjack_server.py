#*********************************************************************#
#                 Code for the labjack server                         #
#*********************************************************************#

#*********************************************************************#
#Code the runs on module import starts here.
#1) Import all modules that we need. NB ei1050 isn't installed by default,
#   but is in the "examples" directory of the labjack code.
import sys
sys.path.append('../common/')
import client_socket
import string
import u3
import u6
import ei1050
import math
import time, os
import numpy as np
import parameterfile

labjack_model=parameterfile.labjack_model
#***********************************************************************#
#2) Set up the labjack. As the LJ and LJPROBE are declared in the global
#   module scope, lets give them capitals. These are initialized, but
#   not written to within our module. Two instances of the LabjackServer
#   would then write to the *same* labjack hardware, but could e.g.
#   do different parts of the job. You's almost certainly *not* want to do
#   this.
if labjack_model.upper()=='U3':
    LJclass=u3
    LJ=u3.U3()
    LJ.setFIOState(u3.FIO7, state=0) #command to close slits. A good starting point.
    LJ.setFIOState(u3.FIO4, state=1) #command to stop movement
    LJ.setFIOState(u3.FIO5, state=1) #command to stop movement
    LJPROBE=ei1050.EI1050(LJ, enablePinNum=0, dataPinNum=1, clockPinNum=2) #Sets up the humidity probe
    LJ.configIO(NumberOfTimersEnabled = 2, EnableCounter0 = 1, TimerCounterPinOffset=8)
    LJ.getFeedback(LJclass.Timer0Config(8), LJclass.Timer1Config(8)) #Sets up the dome tracking wheel

elif labjack_model.upper()=='U6':
    #Attempt to connect to Mike's rhea_tt server running the connection to the actual labjack
    try: rheatt_client = client_socket.ClientSocket("rhea_tt",parameterfile.telescope_id)  #3001 <- port number
    except Exception: print 'Unable to connect to rhea_tt server'
    try:
        dummy=rheatt_client.send_command('eio 5 0')
        dummy=rheatt_client.send_command('eio 6 0')
        dummy=rheatt_client.send_command('eio 7 0')
    except Exception: print 'Could not send a command to the rhea_tt server'
# OLD CODE TO RUN LABJACK DIRECTLY
#       LJclass=u6
#        LJ=u6.U6()
#        LJ.setDIOState(1,0) #Command to power down the RF transmitter and stop slit movement.
#        LJPROBE=ei1050.EI1050(LJ, enablePinNum=0, dataPinNum=1, clockPinNum=2) #Sets up the humidity probe
#       LJ.configIO(NumberTimersEnabled = 2, EnableCounter0 = 1, TimerCounterPinOffset=8)

#LJ.getFeedback(LJclass.Timer0Config(8), LJclass.Timer1Config(8)) #Sets up the dome tracking wheel

#DAC0_REGISTER = 5000  # clockwise movement
#DAC1_REGISTER = 5002  # anticlockwise movement
#LJ.writeRegister(DAC0_REGISTER, 2) # command to stop movement

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

    dome_moving = False                     # A variable to keep track of whether the dome is moving due to a remote user command
    slits_open = False

    counts_per_degree = parameterfile.counts_per_degree             # how many counts from the wheel encoder there is to a degree. 11.83 for 16" dome. 10.9 for 12" dome.
    slitoffset = int(parameterfile.slitoffset*counts_per_degree)    # The position, in degrees, of the slits when the home switch is activated. 68.83 for 16" dome. 92.93 for 12" dome.


    total_counts = 0                        # The total number of counts since we started the program, raw output from wheel
    total_count_at_last_home = 0            # The total counts we had last time we passed through home
    current_position = 0                    # The position of the dome right now in counts (counts reset at home position)
    counts_at_start = 0                     # Record the counts from the wheel before the dome starts to move
    counts_to_move = 0                      # Number of counts the wheel needs to move to get to destination
    home_sensor_count = 0                   # Whenever the homing sensor is activated the Counter0 labjack output changes
                                            # by a positive amount, so every time the number changes, we know we've hit home.
                                            # home_sensor_count keeps track of this change
    homing = False
    watchdog_last_time = time.time()        # The watchdog timer.
    watchdog_max_delta = 10000                # more than this time between communications means there is a problem
    time_since_last_slits_command=time.time()   #time stamp since last slits command. Useful to determine how long it's been since the last instruction to open or close the slits at Mt Stromlo has been.
    slits_moving=False                      #boolean that stores whether the slits are moving. Similar to dome_moving
    slits_opening_duration=parameterfile.slits_opening_duration #time it takes for the slits to open
    dome_park_position=parameterfile.dome_park_position      #Position that the dome should be left in at the end of the night
    if not os.path.isfile('dome_status.txt'):
        np.savetxt('dome_status.txt',[0,0,False])
    #Recover information since last labjack crash
    try:
        total_counts_offset,since_last_offset,slits_state=np.loadtxt('dome_status.txt')
    except Exception:
        np.savetxt('dome_status.txt',[0,0,False])
        total_counts_offset,since_last_offset,slits_state=np.loadtxt('dome_status.txt')
    #if slits_state: cmd_slits('slits open')



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
        #home_output = str( (LJ.getFeedback( LJclass.Counter0() ))[0] )
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
#                       self.temp_home = self.home_sensor_count
            self.homing = True
#                       while self.homing:
#                               print 'home sensor count: '+str(self.home_sensor_count)
#                               print 'temp count: '+str(self.temp_home)
#                               print 'raw output: '+str( (LJ.getFeedback( LJclass.Counter0() ))[0] )
#                               if self.temp_home != self.home_sensor_count:
#                                       self.homing = False
#                                       self.dome_relays("stop")
#                                       return 'Dome is homed'
            return 'Dome Homing'
        elif len(commands) == 2:
            user_command = commands[1]
            if user_command=='park':
                counts_to_move_temp = self.analyse_dome_command(str(self.dome_park_position))
            else: counts_to_move_temp = self.analyse_dome_command(user_command)
            print str(counts_to_move_temp)
            try: counts_to_move_temp = int(float(counts_to_move_temp))
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
        #The commands here depend on which model of the labjack we are using, which determines which model of RF transmitter is in use.
        if commands[1] == 'open':
            if labjack_model.upper()=='U3':
                LJ.setFIOState(u3.FIO7, state=1)
                self.slits_open = True
                return 'slits open'
            elif labjack_model.upper()=='U6':
                #First need to power down the transmitter, change the state of the pins and power it up again.
                dummy=rheatt_client.send_command('eio 5 0')
                dummy=rheatt_client.send_command('eio 6 0')
                dummy=rheatt_client.send_command('eio 7 1')
                dummy=rheatt_client.send_command('eio 5 1')
                self.time_since_last_slits_command=time.time()
                self.slits_open = True
                self.slits_moving = True
                return 'slits open'
        elif commands[1] == 'close':
            if labjack_model.upper()=='U3':
                LJ.setFIOState(u3.FIO7, state=0)
                self.slits_open = False
                return 'slits closed'
            elif labjack_model.upper()=='U6':
                dummy=rheatt_client.send_command('eio 5 0')
                dummy=rheatt_client.send_command('eio 6 1')
                dummy=rheatt_client.send_command('eio 7 0')
                dummy=rheatt_client.send_command('eio 5 1')
                self.time_since_last_slits_command=time.time()
                self.slits_open = False
                self.slits_moving = True
                return 'slits closed'
        elif commands[1] == 'stop':
            #option used only for the Stromlo dome, for now.
            if labjack_model.upper()=='U6':
                dummy=rheatt_client.send_command('eio 5 0')
                dummy=rheatt_client.send_command('eio 6 0')
                dummy=rheatt_client.send_command('eio 7 0')
                self.slits_moving = False
                print 'Slits stopped'
            else: return 'Invalid labjack model. This command does not work on U3'
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
        #       LJ.setFIOState(LJclass.FIO7, state=1) waiting to install to define port
            return 'LED on'
        elif commands[1] == 'off':
            # LJ.setFIOState(LJclass.FIO7, state=0) waiting to install to define port
            return 'LED off'
        else: return 'ERROR'

#******************************* End of user commands ********************************#

    def dome_location(self):
        if labjack_model.upper()=='U3':
            raw_wheel_output = -float(LJ.getFeedback(LJclass.QuadratureInputTimer())[-1]) #This will constantly update the current position of the dome
        elif labjack_model.upper()=='U6':
            raw_wheel_output = str.split(rheatt_client.send_command('get_timers'))[0] #This will constantly update the current position of the dome
        self.total_counts = int(raw_wheel_output)
        #print 'total counts: '+str(self.total_counts)
        #print 'counts at last home: '+str(self.total_count_at_last_home)
        if self.home_sensor_count == 0:
            current_position_temp = self.total_counts+self.total_counts_offset - (self.total_count_at_last_home+self.since_last_offset) + self.slitoffset # what is our relative distance to home?
            np.savetxt('dome_status.txt',[self.total_counts+self.total_counts_offset,self.total_count_at_last_home+self.since_last_offset,self.slits_open])
        else:
            current_position_temp = self.total_counts - self.total_count_at_last_home + self.slitoffset # what is our relative distance to home?
            np.savetxt('dome_status.txt',[self.total_counts,self.total_count_at_last_home,self.slits_open])
        #print 'current position temp: '+str(current_position_temp)
        if current_position_temp < 0: current_position_temp = int(360*self.counts_per_degree) + current_position_temp
        if current_position_temp > int(360*self.counts_per_degree): current_position_temp = current_position_temp - int(360*self.counts_per_degree)
        self.current_position = current_position_temp
        #If we have homed, update the dome status to file, so that in a crash we know where the dome was.
        #print 'current position: '+str(self.current_position)
        #print '\n'

        #On the first run of this function, if the slits were open when the program crashed, open them again.
        if self.slits_state:
            self.cmd_slits('slits open')
            self.slits_state=False
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
            if labjack_model.upper()=='U3':
                LJ.setFIOState(u3.FIO4, state=0)
                LJ.setFIOState(u3.FIO5, state=1)
            elif labjack_model.upper()=='U6':
                #LJ.getFeedback(u6.DAC0_8(LJ.voltageToDACBits(0,0)))
                #LJ.getFeedback(u6.DAC1_8(LJ.voltageToDACBits(5,1)))
                dummy=rheatt_client.send_command('cio 0 1')
                dummy=rheatt_client.send_command('cio 1 1')
                dummy=rheatt_client.send_command('cio 2 1')
        elif commands[0] == 'anticlockwise':
            if labjack_model.upper()=='U3':
                LJ.setFIOState(u3.FIO4, state=1)
                LJ.setFIOState(u3.FIO5, state=0)
            elif labjack_model.upper()=='U6':
                #LJ.getFeedback(u6.DAC0_8(LJ.voltageToDACBits(5,0)))
                #LJ.getFeedback(u6.DAC1_8(LJ.voltageToDACBits(5,1)))
                dummy=rheatt_client.send_command('cio 0 1')
                dummy=rheatt_client.send_command('cio 1 0')
                dummy=rheatt_client.send_command('cio 2 1')
        elif commands[0] == 'stop':
            if labjack_model.upper()=='U3':
                LJ.setFIOState(u3.FIO4, state=1)
                LJ.setFIOState(u3.FIO5, state=1)
            elif labjack_model.upper()=='U6':
                #LJ.getFeedback(u6.DAC0_8(LJ.voltageToDACBits(0,0)))
                #LJ.getFeedback(u6.DAC1_8(LJ.voltageToDACBits(0,1)))
                dummy=rheatt_client.send_command('cio 2 0')
                dummy=rheatt_client.send_command('cio 0 0')
        else: return 'ERROR'



    def home_tracker(self):
        '''Return the number of times the dome home sensor has been pressed.'''
        #home_output = int(str( (LJ.getFeedback( u3.Counter0() ))[0] ))
        #print self.home_sensor_count
        if labjack_model.upper()=='U3':
            current_home_counts=int(str( (LJ.getFeedback( LJclass.Counter0() ))[0] ))
        elif labjack_model.upper()=='U6':
            current_home_counts=int(str.split(rheatt_client.send_command('get_counters'))[0])
        if current_home_counts != self.home_sensor_count:  # We've hit home!
            print 'Dome homed'
            self.home_sensor_count = current_home_counts
            self.total_count_at_last_home = self.total_counts # We have a new count as our zero reference point
            self.total_counts_offset=0
            self.since_last_offset=0
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
#               if self.slits_open:
#                       print math.fabs(time.time() - self.watchdog_last_time)
        if (math.fabs(time.time() - self.watchdog_last_time) > self.watchdog_max_delta) and (self.slits_open==True):
            self.cmd_slits('slits close')
            self.watchdog_last_time = time.time()
            print 'ERROR: No active communications. Slits closing.'
        if (math.fabs(time.time() - self.time_since_last_slits_command) > self.slits_opening_duration) and (self.slits_moving==True):
            self.cmd_slits('slits stop')
            self.slits_moving=False

    def log(self):
        #add a temperature and humidity reading to a log
        f = open('temphumlog.txt','a')
        f.write(str(time.time())+" "+time.ctime()+" "+str(self.cmd_temperature('dummy'))+" "+str(self.cmd_humidity('dummy'))+'\n'),
        f.close()
