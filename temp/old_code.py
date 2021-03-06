                        if indi.get_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i)=='On':
                                frame_type=i
                return 'Image type changed to '+self.imtype+' with the indi server image type changed to '+frame_type


                        
        def cmd_exposeAndWait(self,command):
                ''' This function takes a full frame image and waits for the image to be read out prior to ending. Usage: exposeAndWait <exptime> <shutter state> <filename> <imtype (optional, if not bias, dark or light)>'''
		commands = str.split(command)
                if len(commands) < 4 : return 'error: require 3 input values (exposure time, lens (open/closed) and filename. optional argument imtype for header keyword if image type is not bias, dark or light.'
		#Tests to see if the first command is a float (exposure time) and the second command is either open or close
		try: exposureTime = float(commands[1])
		except Exception: return 'invalid input, first input must be a value in seconds'
		#if loop to determine if command[2] is open or closed or invalid
		test = 'invalid'
		if commands[2] == 'open' or commands[2] == 'closed' : test = 1
		try: checkCommand2 = float(test)
		except Exception: return 'invalid input, second input must be open or closed'
		shutter = str(commands[2])
	        fileInput = str(commands[3])  
                try:
                        if len(commands)==4:
                                self.capture(exposureTime,shutter,fileInput)	
                        else: 
                                self.capture(exposureTime,shutter,fileInput,imtype=commands[4])
                except Exception: return 'Unable to start exposure, check connection to CCD'
		return 'Exposure Initiated'

        #command that takes an image
	def capture(self,exposureTime,shutter,fileInput,imtype='Light'):
		result=self.cmd_imageType('imageType '+imtype)
                self.startTime = time.time()
                self.exposureTime=exposureTime
                #sets up file name
		self.filename= fileInput.partition('.fits')[0]
		#calls checking functions	
		self.checkFile(self.filename)
                #print 'Got this far'
                try: 
                        result=indi.set_and_send_float("SX CCD SXVR-H694","CCD_EXPOSURE","CCD_EXPOSURE_VALUE",exposureTime)
                except Exception: return 0
		self.exposure_active=True
                return 1
		
	def checkIfFinished(self):
		'''This function is constantly looking for an image named TEMPIMAGE.fits in the output directory. This is the output of the exposure and should be renamed and have the header keywords populated. This function does that. '''
                if os.path.isfile('images/TEMPIMAGE.fits'):
                        result=self.finish_exposure('Normal')
                
                
	
	def cmd_abortExposure(self,the_command):
		#Function used to stop the current exposure
	    	commands = str.split(the_command)
		if len(commands)==1:
			self.exposure_active=False
                        result=indi.set_and_send_float("SX CCD SXVR-H694","CCD_ABORT_EXPOSURE","ABORT",'On')
			return 'Aborted exposure'
		else: return 'This function takes no arguments'
	
	def finish_exposure(self,finishstatus):
                #gets end time
		self.endTime = time.time()
                im=pyfits.open('images/TEMPIMAGE.fits',mode='update')
                hdu=im[0]
		#sets up fits header. Most things are self explanatory
		#This ensures that any headers that can be populated at this time are actually done.
		#hdu.header.update('EXPTIME', self.endTime-self.startTime, comment='The frame exposure time in seconds')	
		hdu.header.update('ETINSTRU',float(self.exposureTime), 'Instructed exposure time in seconds')
		hdu.header.update('NAXIS1', indi.get_float("SX CCD SXVR-H694","CCD_FRAME","WIDTH"), comment='Width of the CCD in pixels')
		hdu.header.update('NAXIS2', indi.get_float("SX CCD SXVR-H694","CCD_FRAME","HEIGHT"), comment='Height of the CCD in pixels')
		hdu.header.update('GAIN', self.gain, comment='CCD gain in e-/ADU')
		hdu.header.update('XFACTOR', indi.get_float("SX CCD SXVR-H694","CCD_BINNING","HOR_BIN"), 'Camera x binning factor')
		hdu.header.update('YFACTOR', indi.get_float("SX CCD SXVR-H694","CCD_BINNING","VER_BIN"), 'Camera y binning factor')
		#UTC time header keywords
		start=time.gmtime(self.startTime)
		dateobs=str(start[0])+'-'+str(start[1]).zfill(2)+'-'+str(start[2]).zfill(2)
		hdu.header.update('DATE-OBS', dateobs, 'UTC YYYY-MM-DD')
		starttime=str(start[3]).zfill(2)+':'+str(start[4]).zfill(2)+':'+str(start[5]).zfill(2)
		hdu.header.update('UTSTART', starttime , 'UTC HH:MM:SS.ss Exp. Start')
		middleTime=self.startTime+(self.endTime-self.startTime)/2.
		middle=time.gmtime(middleTime)
		midtime=str(middle[3]).zfill(2)+':'+str(middle[4]).zfill(2)+':'+str(middle[5]).zfill(2)
		hdu.header.update('UTMIDDLE', midtime , 'UTC HH:MM:SS.ss Exp. Midpoint')
		end=time.gmtime(self.endTime)
		endtime=str(end[3]).zfill(2)+':'+str(end[4]).zfill(2)+':'+str(end[5]).zfill(2)
		hdu.header.update('UTEND', endtime , 'UTC HH:MM:SS.ss Exp. End')
		ut=str(middle[2]).zfill(2)+'/'+str(middle[1]).zfill(2)+'/'+str(middle[0])+':'+str(middle[3]).zfill(2)+':'+str(middle[4]).zfill(2)+':'+str(middle[5]).zfill(2)
		hdu.header.update('JD', ctx.ut2jd(ut), 'Julian date of Midpoint of exposure')
		hdu.header.update('LST', ctx.ut2lst(ut,151.112,flag=1), 'Local sidereal time of Midpoint')
		#local time header keywords
		start=time.localtime(self.startTime)
		dateobs=str(start[0])+'-'+str(start[1]).zfill(2)+'-'+str(start[2]).zfill(2)
		hdu.header.update('LDATEOBS', dateobs , 'LOCAL YYYY-MM-DD')
		starttime=str(start[3]).zfill(2)+':'+str(start[4]).zfill(2)+':'+str(start[5]).zfill(2)
		hdu.header.update('LTSTART', starttime , 'Local HH:MM:SS.ss Exp. Start')
		middleTime=self.startTime+(self.endTime-self.startTime)/2.
		middle=time.localtime(middleTime)
		midtime=str(middle[3]).zfill(2)+':'+str(middle[4]).zfill(2)+':'+str(middle[5]).zfill(2)
		hdu.header.update('LTMIDDLE', midtime , 'Local HH:MM:SS.ss Exp. Midpoint')
		end=time.localtime(self.endTime)
		endtime=str(end[3]).zfill(2)+':'+str(end[4]).zfill(2)+':'+str(end[5]).zfill(2)
		hdu.header.update('LTEND', endtime , 'Local HH:MM:SS.ss Exp. End')
		hdu.header.update('CAMTEMP', float(commands.getoutput('indi_getprop -p 7777 "SX CCD SXVR-H694.CCD_TEMPERATURE.CCD_TEMPERATURE_VALUE"').split('=')[1]), 'Camera temperature (C)')
		hdu.header.update('SETPOINT', self.ccdSetpoint, 'Camera temperature setpoint (C)')
		hdu.header.update('COOLING', indi.get_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_ON"), 'Camera cooling enabled?')
		if self.exposureTime==0:
			self.imtype='Bias'
		elif self.shutter=='closed':
			self.imtype='Dark'
		print 'Current image type just before populating header is:',self.imtype
		hdu.header.update('IMGTYPE', self.imtype, 'Image type')
		#if finishstatus=='Aborted':
		#	hdu.header.update('EXPSTAT','Aborted', 'This exposure was aborted by the user')
		'''
		hdu.header.update('FILTER', , 'NEED to query this')
		'''
		#hdu.writeto(self.fullpath)
		self.startTime=0
		self.exposureTime=0
                im.flush()
                os.system('mv images/TEMPIMAGE.fits images/'+self.filename+'.fits')
		print 'Exposure finished'
        
        #--------------------------------------LABJACK-------------------------------#
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
                 

        
                 


        #-----------------------ippower-------------------------------------#
        #ipPower options. This is a unit that is used to control power to units.
	#This dictionary contains which device is plugged into each port. If the connections change, this needs to be changed too! 
	power_order={'NUC':1,'SX':2,'XeAr':3,'WhiteLight':4}
        ippower.Options.ipaddr='192.168.2.19'
        ippower.Options.login = 'admin'
        ippower.Options.passwd = '12345678'
        ippower.Options.port = 80

       	def cmd_ippower(self,the_command):
		'''Function to control the ippower unit. The first argument is either the name of the device or the port number of the relevant device or "show" for the device list. The second argument is optional, either "on" or "off". Leave blank for power status of device.'''
		commands = str.split(the_command)
                skip_word_check=False
                if len(commands)<2:
                    return 'Useage: ippower port [on|off]'
		if commands[1]=='show': return str(self.power_order)
                try: 
                        port=int(commands[1])
                        if port > 4 or port <1: return 'Invalid port number'
                        skip_word_check=True
                except Exception: pass
                if not skip_word_check:
                        if commands[1] in self.power_order.keys():
                                for unit,number in self.power_order.iteritems():
                                        if unit == commands[1]:
                                                port=number
                        else: return 'Invalid device. type "ippower show" for a list of devices.'
		if len(commands) == 2:
			return 'The power status of the port into which the '+commands[1]+' is connected is '+str( ippower.get_power(ippower.Options,port) )
		elif len(commands) == 3:
			if commands[2]=='on': s=True
			elif commands[2]=='off': s=False
			else: return 'Invalid power status option'
			try: ippower.set_power(ippower.Options,port,s) 
			except Exception: 
				#logging.error('Unable to set power status for port')
				return 'Unable to set power status for port'
			#logging.info(commands[1]+' successfully switched '+commands[2])
			return commands[1]+' successfully switched '+commands[2]
		else: return 'Invalid ippower command'
                if len(commands)>3: return 'Too many arguments'
