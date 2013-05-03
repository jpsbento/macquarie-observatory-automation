#*********************************************************************#
#                 Code for the labjack u6 (spectrograph) server       #
#*********************************************************************#

#*********************************************************************#
#Code the runs on module import starts here.
#1) Import all modules that we need. NB ei1050 isn't installed by default,
#   but is in the "examples" directory of the labjack code.
import string
import u6
import math
import time
import numpy
import time
#***********************************************************************#
#2) Set up the labjack. As the LJ and LJPROBE are declared in the global
#   module scope, lets give them capitals. These are initialized, but
#   not written to within our module. Two instances of the LabjackServer
#   would then write to the *same* labjack hardware, but could e.g. 
#   do different parts of the job. You's almost certainly *not* want to do 
#   this.
LJ=u6.U6()
#Need to set up fancy DAC here for the temperature control
#LJ.configIO(NumberOfTimersEnabled = 2, EnableCounter0 = 1, TimerCounterPinOffset=8)
#LJ.getFeedback(u3.Timer0Config(8), u3.Timer1Config(8)) #Sets up the dome tracking wheel

LJ.getFeedback(u6.BitStateWrite(2,0)) #Start off with no current through the resistive heater.
LJ.getFeedback(u6.BitStateWrite(3,0)) #Start off with no LED.

#The Analog feedback command is LJ.AIN24, and the getAIN command does everything
#LJ.getFeedback( u6.AIN24(PositiveChannel, ResolutionIndex = 0, 
#     |                              GainIndex = 0, SettlingFactor = 0, 
#     |                              Differential = False ) )
#LJ.binaryToCalibratedAnalogVoltage(self, gainIndex, bytesVoltage, is16Bits=False)
# The u6.PortDirRead, PortDirWrite, PortStateRead and PortStateWrite commands can be used
# with getFeedback
# LJ.getFeedback( u6.BitStateWrite( IONumber, State ) )

#***********************************************************************#
#2) Now define our main class, the LabjackServer.
class LabjackU6Server:
        loop_count=0
        feedback_freq=3
        pcm_time=0.5
        heater_frac=0.0
        delT_int = 0.0
        T_targ = 23.5
        heater_gain=5
        integral_gain=0.1
#*************************************** List of user commands ***************************************#

	def cmd_ljtemp(self,the_command):
		''' Get the temperature of the labjack in Kelvin'''
		temperature = LJ.getTemperature()
		return str(temperature)
        
	def cmd_heater(self,the_command):
		'''Set the Heater PCM current'''
		commands=str.split(the_command)
		if len(commands) == 2:
 			try: heater_frac_temp = float(commands[1])
			except Exception: return 'ERROR: Requires a number between 0 and 1'
			self.heater_frac=heater_frac_temp
		else: return 'ERROR: Requires a number between 0 and 1'
        
 	def cmd_backLED(self, the_command):
		'''Command to control IR LED backfeed.'''
		commands = str.split(the_command)
		if len(commands) != 2: return 'ERROR'
		if commands[1] == 'on':
			LJ.getFeedback(u6.BitStateWrite(3,1))			
			return 'LED on'
		elif commands[1] == 'off':
			LJ.getFeedback(u6.BitStateWrite(3,0))			
			return 'LED off'
		else: return 'ERROR'               
		
#******************************* End of user commands ********************************#              

	def heaterControl(self):
                '''Pulse positive for heater_frac fraction of a pcm_time time'''
                #These lines prevents an endless sleep!
                if (self.heater_frac < 0): self.heater_frac=0
                if (self.heater_frac > 1): self.heater_frac=1
                #Switch the heater on...
                if self.heater_frac==0:
#                    LJ.getFeedback(u6.BitStateWrite(2,0))
                    LJ.getFeedback(u6.DAC0_8(0))
                else:
#                    LJ.getFeedback(u6.BitStateWrite(2,1))
                    LJ.getFeedback(u6.DAC0_8(255))
                #Wait
                time.sleep(self.pcm_time*self.heater_frac)
                #Switch the heater off...
                if self.heater_frac==1:
#                    LJ.getFeedback(u6.BitStateWrite(2,1))
                   LJ.getFeedback(u6.DAC0_8(255))
                else:
#                    LJ.getFeedback(u6.BitStateWrite(2,0))
                    LJ.getFeedback(u6.DAC0_8(0))
                #Wait
                time.sleep(self.pcm_time*(1.0 - self.heater_frac))
                
	def feedbackLoop(self):
                '''Execute the feedback loop every feedback_freq times'''

                if self.feedback_freq==0: return
                fileName='TLog.log' #'TLog_'+localtime+'.log'
                self.f = open(fileName,'a')
                self.loop_count = self.loop_count + 1
                
                
                if (self.loop_count == self.feedback_freq):  
               
                 
                 #Firstly, compute temperatures.

                 #ResolutionIndex: 0=default, 1-8 for high-speed ADC, 9-13 for high-res ADC on U6-Pro.
                 #GainIndex: 0=x1, 1=x10, 2=x100, 3=x1000, 15=autorange.
                 #SettlingFactor: 0=Auto, 1=20us, 2=50us, 3=100us, 4=200us, 5=500us, 6=1ms, 7=2ms, 8=5ms, 9=10ms.
                        
                 a0 = LJ.getAIN(0,resolutionIndex=9,gainIndex=1,settlingFactor=8,differential=1)
                 a1 = LJ.getAIN(1,resolutionIndex=9,gainIndex=0,settlingFactor=0)   #Temp_sensor_1 (bridge)
                 a2 = LJ.getAIN(2,resolutionIndex=9,gainIndex=0,settlingFactor=0)   #voltage reference (5V)
                 a3 = LJ.getAIN(3,resolutionIndex=9,gainIndex=0,settlingFactor=0)   #Temp_sensor_3
                                                   
                 r3 = 1 * (a2-a3)/a3         #ambient temperature

                 dR = 2*9.09*a0/(a2-a0)      #differential change
                 r1 = 9.09 + dR              #value of R2 in bridge
                                                          
                 T0 = 298
                 B = 3920
                 R0 = 10
                 T1 = 1.0/T0 + math.log(r1/R0)/B   #equation for PTC resistors (see Wikipedia)
                 T1 = 1/T1 - 273
               
                 T3 = 1.0/T0 + math.log(r3/R0)/B
                 T3 = 1/T3 - 273
             
                 lineOut = " %.4f %.4f %.4f %.3f " % (T1,T3,self.heater_frac,self.delT_int)
                 print lineOut
                 localtime = time.asctime( time.localtime(time.time()) )
                 self.f.write(lineOut+' '+localtime+'\n')
                 self.f.close()
                 
                 
                 #Temperature servo:
                 
                 delT = T1 - self.T_targ            #delta_T = average of both sensors - T_set    
                 self.delT_int += delT              #start: deltT_int = 0 --> add delT to deltT_int per cycle
                 if (self.delT_int > 0.5/self.integral_gain): self.delT_int = 0.5/self.integral_gain      # = +5
                 elif (self.delT_int < -0.5/self.integral_gain): self.delT_int = -0.5/self.integral_gain  # = -5
                 
                 integral_term = self.integral_gain*self.delT_int #integral term (int_gain * delta_T)
                 #Full range is 0.7 mK/s. So a gain of 10 will set
                 #0.7 mK/s for a 100mK temperature difference.
                 self.heater_frac =  self.heater_gain*delT - integral_term   #see equation in notebook

                 self.loop_count=0
                           
