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
        T_targ = 30
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
                 a0 = LJ.getAIN(0,resolutionIndex=11,gainIndex=0,settlingFactor=0)
                 a1 = LJ.getAIN(1,resolutionIndex=11,gainIndex=1,settlingFactor=0)
                 a2 = LJ.getAIN(2,resolutionIndex=11,gainIndex=0,settlingFactor=0)
                 r1 = (a0 - a2)/a1
                 r2 = (a2 - a1)/a1
                 T0 = 298
                 B = 3920
                 R0 = 10
                 T1 = 1.0/T0 + math.log(r1/R0)/B
                 T1 = 1/T1 - 273
                 T2 = 1.0/T0 + math.log(r2/R0)/B
                 T2 = 1/T2 - 273
                 lineOut = "%.4f %.4f %.4f %.3f" % (T1, T2,self.heater_frac,self.delT_int)
                 print lineOut
                 localtime = time.asctime( time.localtime(time.time()) )
                 self.f.write(lineOut+' '+localtime+'\n')
                 self.f.close()
                 delT = 0.5*(T1 + T2) - self.T_targ
                 self.delT_int += delT
                 if (self.delT_int > 10):  self.delT_int=5
                 if (self.delT_int < -10): self.delT_int=-5
                 #Full range is 0.7 mK/s. So a gain of 10 will set
                 #0.7 mK/s for a 100mK temperature difference.
                 self.heater_frac = 0.5 - 10*delT - 0.1*self.delT_int
                 self.loop_count=0            
