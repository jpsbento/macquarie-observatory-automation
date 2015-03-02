#*********************************************************************#
#                 Code for the labjack u6 (RHEA2) server       #
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
import sys
import array
import copy
#***********************************************************************#
#2) Set up the labjack. As the LJ and LJPROBE are declared in the global
#   module scope, lets give them capitals. These are initialized, but
#   not written to within our module. Two instances of the LabjackServer
#   would then write to the *same* labjack hardware, but could e.g. 
#   do different parts of the job. You's almost certainly *not* want to do 
#   this.
LJ=u6.U6(serial=360009388)
#Need to set up fancy DAC here for the temperature control
#LJ.configIO(NumberOfTimersEnabled = 2, EnableCounter0 = 1, TimerCounterPinOffset=8)
#LJ.getFeedback(u3.Timer0Config(8), u3.Timer1Config(8)) #Sets up the dome tracking wheel

#Start off with no current: 
LJ.getFeedback(u6.BitStateWrite(1,0)) #H-Bridge bit 1
LJ.getFeedback(u6.BitStateWrite(2,0)) #H-Bridge bit 2



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
class LabjackU6Server:    # global variables that can be rewritten
        loop_count=0
        loop_fibre=0      #counter for the fibre loop activation
        loop_maxval=0
        log_loop = 0
        
        feedback_freq=2   #how often to update the feedback loop parameters
        pcm_time=0.5     #total heating cycle time. probably in seconds
	heater_frac=0.0     #fraction of the pcm_time that the heater is on
        delT_int = 0.0
        T_targ = 28.0
        heater_gain=5
        integral_gain=0.1
        T1=0
        T2=0
        T3=0
        T4=0
        T5=0
        T6=0
        T7=0
        T8=0
        P=0
        RH=0
        

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
                if (self.heater_frac==0): LJ.getFeedback(u6.DAC0_8(0))
                else: LJ.getFeedback(u6.DAC0_8(255))

              #Wait
                time.sleep(self.pcm_time*self.heater_frac)
              #Switch the heater off...
                if (self.heater_frac==1): LJ.getFeedback(u6.DAC0_8(255))
                else: LJ.getFeedback(u6.DAC0_8(0))
              #Wait
                time.sleep(self.pcm_time*(1.0 - self.heater_frac))
                 
             
                
             
#********************************** Feedback loops ***********************************#                
	def feedbackLoop(self):
                '''Execute the feedback loop every feedback_freq times'''

                if self.feedback_freq==0: return
                fileName='TLog' #'TLog_'+localtime+'.log'
                self.f = open(fileName,'a')
                self.loop_count = self.loop_count + 1
                self.log_loop = self.log_loop + 1 

                
   
                if (self.loop_count == 2):
                #Firstly, compute temperatures.
                #ResolutionIndex: 0=default, 1-8 for high-speed ADC, 9-13 for high-res ADC on U6-Pro.
                #GainIndex: 0=x1, 1=x10, 2=x100, 3=x1000, 15=autorange.
                #SettlingFactor: 0=Auto, 1=20us, 2=50us, 3=100us, 4=200us, 5=500us, 6=1ms, 7=2ms, 8=5ms, 9=10ms.
                        a0 = LJ.getAIN(0,resolutionIndex=8,gainIndex=1,settlingFactor=9,differential=1)
			a1 = LJ.getAIN(1,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #T1: optical bench
			#--> Differential measurement is made between a0 and a1!
			
			a2 = LJ.getAIN(2,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #chamber
			a3 = LJ.getAIN(3,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #F/N-system    
			a4 = LJ.getAIN(4,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #icebox_1
			a5 = LJ.getAIN(5,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #icebox_2
                        a6 = LJ.getAIN(6,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #wooden_box
                        a7 = LJ.getAIN(7,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #external
                        a8 = LJ.getAIN(8,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #CCD heat sink
                        a9 = LJ.getAIN(9,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #humidity
                        a10 = LJ.getAIN(10,resolutionIndex=8,gainIndex=0,settlingFactor=0)      #pressure
                        Vref = LJ.getAIN(11,resolutionIndex=8,gainIndex=0,settlingFactor=0)     #Reference voltage (5V)
			
                        R0 = 10 #10KOhm at 25deg!

                        dR_B1 = 2*R0*a0/(Vref-a0)     #differential change
			R1 = R0 + dR_B1                #value of R2 in bridge

                        VB = a4-a5
                        dR_B2 = 2*R0*VB/(Vref-VB)     #differential change
			R4 = R0 + dR_B2                #value of R2 in bridge

			R2 = R0 * (Vref-a2)/a2         
                        R3 = R0 * (Vref-a3)/a3        
                        R6 = R0 * (Vref-a6)/a6
			R7 = R0 * (Vref-a7)/a7 
			R8 = R0 * (Vref-a8)/a8
			
			T0 = 298
			B = 3920


			#NTC resistors (see Wikipedia Steinhart-Hart equation)

                        #Spectrograph bench:
			T1 = 1.0/T0 + math.log(R1/R0)/B   
			self.T1 = 1/T1 - 273

                        #Chamber:
                        T2  = 1.0/T0 + math.log(R2/R0)/B
			self.T2 = 1/T2 - 273

			#F/N system:
			T3  = 1.0/T0 + math.log(R3/R0)/B
			self.T3 = 1/T3 - 273

                        #Icebox:
                        T4  = 1.0/T0 + math.log(R4/R0)/B
			self.T4 = 1/T4 - 273

                        #Wooden box:
                        T6  = 1.0/T0 + math.log(R6/R0)/B
			self.T6 = 1/T6 - 273

                        #External:
		        T7  = 1.0/T0 + math.log(R7/R0)/B
			self.T7 = 1/T7 - 273

                        #CCD heat sink:
		        T8  = 1.0/T0 + math.log(R8/R0)/B
			self.T8 = 1/T8 - 273
		
			self.RH = a9/(Vref*0.00636)-(0.1515/0.00636)

                        self.P = (a10+0.095*Vref)/(Vref*0.009)*10

                        if (self.log_loop == 20):
			
                                lineOut = " %.3f %.3f %.3f %.3f %.3f %.3f %.3f %.3f %.2f %.2f " % (self.T1,self.T2,self.T3,self.T4,self.T6,self.T7,self.T8,self.RH,self.P,Vref)#  self.heater_frac,self.delT_int)
                                print lineOut
                                localtime = time.asctime( time.localtime(time.time()) )
                                self.f.write(lineOut+' '+localtime+'\n')
                                self.f.close()
                                self.log_loop = 0
                        
			  #Spectrograph temperature servo:

			delT = self.T1 - self.T_targ            #delta_T = average of both sensors - T_set    
			self.delT_int += delT              #start: deltT_int = 0 --> add delT to deltT_int per cycle
			if (self.delT_int > 0.5/self.integral_gain): self.delT_int = 0.5/self.integral_gain      # = +5
			elif (self.delT_int < -0.5/self.integral_gain): self.delT_int = -0.5/self.integral_gain  # = -5
			
			integral_term = self.integral_gain*self.delT_int #integral term (int_gain * delta_T)
			  #Full range is 0.7 mK/s. So a gain of 10 will set
			  #0.7 mK/s for a 100mK temperature difference.
			self.heater_frac =  0.5 - self.heater_gain*delT - integral_term   #see equation in notebook
			
			self.loop_count=0
                 

        
                 
