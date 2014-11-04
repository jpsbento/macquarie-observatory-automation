from indiclient import *
import numpy as np
import matplotlib.pyplot as plt
import pyfits
import time
import ctypes
import os
#import the tools to do time and coordinate transforms
import ctx


#Try to connect to the camera
try: 
        indi=indiclient("localhost",7777)
        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","CONNECT","On")
        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","DISCONNECT","Off")
        #set the camera saving images locally instead of sending them onto some sort of client. This is not designed to have a client. 
        print 'successfully connected to camera'
except Exception: print 'Can not connect to camera'
time.sleep(1)
#Check connection
try: 
        result=indi.get_text("SX CCD SXVR-H694","CONNECTION","CONNECT")
        if result=='Off':
                print 'Unable to connect to SX camera'
except Exception: print 'Unable to check camera connection'

#set up some options that should not change often
dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_CLIENT","Off")
dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_BOTH","Off")
dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_LOCAL","On")
dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","CONNECT_COOLER","On")
dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","DISCONNECT_COOLER","Off")
if not os.path.exists('./images/'):
                dummy=subprocess.call('mkdir ./images', shell=True)
dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_DIR","images")
dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_PREFIX","TEMPIMAGE")



class SX:
	#Some parameters for the default stats
        frame_types=['LIGHT','BIAS','DARK','FLAT']

        #parameters related to the exposure settings and whether there is an image being taken at any given time.
	exposing=False
	exposureTime=0
	shutter_position='Closed'
	filename='None'
        imtype='none'
	gain='Unknown'
	exposure_active=False
        #FUNCTIONS: the following two functions are used in the imaging process, they relate to filenames and prevet crashes 
	#when there are typos in directories or	duplicate filenames
	
	#parameters relating to the imaging and exposure characteristics
	startTime=0
	endTime=0
	camtemp=0
        ccdSetpoint=0
	#imtype='None'
	shutter='None'

	#Checks to see if the filename given exists and prompts for overight or rename if it does
	def checkFile (self,file_to_check):
		presence = os.path.exists('./images/'+file_to_check+'.fits')
		if presence == True:
			print 'file already exists, would you like to overwrite existing file? (yes/no)'
			selection = raw_input()
			while selection != 'yes' and selection != 'no' and selection != 'n' and selection !='y':
				print 'please enter yes or no, note if you do choose to not\
					 overwrite you will be promted to enter an alternate file name'
				selection = raw_input()
			if selection == 'yes' or selection == 'y':
				os.remove('./images/'+file_to_check+'.fits')
			elif selection == 'no' or selection == 'n':
				print 'please enter a new filename, if an identical filename is entered it will overwrite the previous one'
				#offers a new name (or directory for input)
				fileInput2 = raw_input()
				self.filename= fileInput2.partition('.fits')[0]


        def cmd_checkTemperature(self,the_command):
		'''This command checks the temperature at the time it is run. No inputs for this function'''
                try: 
                        temp=indi.get_float("SX CCD SXVR-H694","CCD_TEMPERATURE","CCD_TEMPERATURE_VALUE")
                except Exception: return 'Unable to check CCD temperature for some reason'
                return 'CCD temperature is '+str(temp)+' degrees C'
        
        def cmd_setTemperature(self,the_command):
		'''this command sets the temperature of the imaging CCD, input is in degrees C.'''
		commands = str.split(the_command)
		if len(commands) < 2 : return 'error: no input value'
                if len(commands) > 2 : return 'Too many inputs. Just give us the temperature in degrees C.'
                try: 
                        dummy=indi.set_and_send_float("SX CCD SXVR-H694","CCD_TEMPERATURE","CCD_TEMPERATURE_VALUE",float(commands[1]))
                        self.ccdSetpoint=float(commands[1])
                except Exception: return 'Unable to set camera temperature'
                return 'Successfully set camera temperature'

        def cmd_establishLink(self,the_command):
                '''This command can be used to establish connection with the camera in case that link has been broken. By default, when the class is defined, connection with the camera is achieved anyway, so this should be used sparringly. No inputs to this function'''
                try: 
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","CONNECT","On")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","DISCONNECT","Off")
                        #set the camera saving images locally instead of sending them onto some sort of client. This is not designed to have a client. 
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_CLIENT","Off")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_BOTH","Off")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_LOCAL","On")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","CONNECT_COOLER","On")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","DISCONNECT_COOLER","Off")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_DIR","images")
                except Exception: return 'Unable to connect to CCD camera'
                return 'Successfully coneected to camera'

        def cmd_closeLink(self,the_command):
                '''This command can be used to break connection with the camera. No inputs to this function'''
                try: 
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","CONNECT","Off")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","DISCONNECT","On")
                except Exception: return 'Unable to disconnect CCD camera'
                return 'Successfully disconeected to camera'
        
        def cmd_getCCDParams(self,the_command):
                ''' No argument - this function gets the CCD parameters. '''
                #try to acquire all the ccd paramteres that may be useful to know
		try: 
                        name=indi.get_text("SX CCD SXVR-H694","DRIVER_INFO","NAME")
                        driver=indi.get_text("SX CCD SXVR-H694","DRIVER_INFO","EXEC")
                        version=indi.get_text("SX CCD SXVR-H694","DRIVER_INFO","VERSION")
                        image_dir=indi.get_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_DIR")
                        image_prefix=indi.get_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_PREFIX")
                        cooling=indi.get_text("SX CCD SXVR-H694","COOLER_CONNECTION","CONNECT_COOLER")
                        left=indi.get_float("SX CCD SXVR-H694","CCD_FRAME","X")
                        top=indi.get_float("SX CCD SXVR-H694","CCD_FRAME","Y")
                        width=indi.get_float("SX CCD SXVR-H694","CCD_FRAME","WIDTH")
                        height=indi.get_float("SX CCD SXVR-H694","CCD_FRAME","HEIGHT")
                        hor_bin=indi.get_float("SX CCD SXVR-H694","CCD_BINNING","HOR_BIN")
                        ver_bin=indi.get_float("SX CCD SXVR-H694","CCD_BINNING","VER_BIN")
                        temp=indi.get_float("SX CCD SXVR-H694","CCD_TEMPERATURE","CCD_TEMPERATURE_VALUE")
                        resx=indi.get_float("SX CCD SXVR-H694","CCD_INFO","CCD_MAX_X")
                        resy=indi.get_float("SX CCD SXVR-H694","CCD_INFO","CCD_MAX_Y")
                        sizex=indi.get_float("SX CCD SXVR-H694","CCD_INFO","CCD_PIXEL_SIZE_X")
                        sizey=indi.get_float("SX CCD SXVR-H694","CCD_INFO","CCD_PIXEL_SIZE_Y")
                        bitspix=indi.get_float("SX CCD SXVR-H694","CCD_INFO","CCD_BITSPERPIXEL")
                        for i in self.frame_types:
                                if indi.get_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i)=='On':
                                        frame_type=i
                except Exception: return 'Unable to query CCD camera parameters'
                return 'Name: '+name+'\n'+'Driver: '+driver+'\n'+'Version: '+version+'\n'+'Image Destination: '+image_dir+'\n'+'Image Prefix: '+image_prefix+'\n'+'Exposure Type :'+frame_type+'\n'+'Cooling Status: '+cooling+'\n'+'Temperature: '+str(temp)+' degrees C'+'\n'+'Left Pixel Coordinate: '+str(left)+'\n'+'Top Pixel Coordinate: '+str(top)+'\n'+'Frame Width: '+str(width)+' Pixels'+'\n'+'Frame Height: '+str(height)+' Pixels'+'\n'+'Horizontal Binning: '+str(hor_bin)+' Pixels'+'\n'+'Vertical Binning: '+str(ver_bin)+' Pixels'+'\n'+'X Resolution: ' +str(resx)+'\n'+'Y Resolution: '+str(resy)+'\n'+'X Pixel Size:'+str(sizex)+' Microns'+'\n'+'Y Pixel Size: '+str(sizey)+' Microns'+'\n'+'Bits per Pixel: '+str(bitspix)

        def cmd_enableRegulation(self,the_command):
                ''' No arguments on this function, just enable cooling if it is not on yet.'''
                try: 
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","CONNECT_COOLER","On")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","DISCONNECT_COOLER","Off")
                except Exception: return 'Unable to enable cooling on the camera. Check connection'
                return 'Successfully enabled cooling of the CCD'


        def cmd_disableRegulation(self,the_command):
                ''' No arguments on this function, just disable cooling of CCD.'''
                try: 
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","CONNECT_COOLER","Off")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","DISCONNECT_COOLER","On")
                except Exception: return 'Unable to disable cooling on the camera. Check connection'
                return 'Successfully disabled cooling of the CCD'

        def cmd_changeBinning(self,the_command):
                '''This function is used to change the binning settings of the camera readout. Input horizontal binning, then vertical binning. Example: changeBinning 2 1   This will make it such that the camera readout in 2x1 mode.'''
                commands = str.split(the_command)
                if len(commands)!=3: return 'Invalid inputs, please input both horizontal and vertical binning modes, separated by spaces'
                try: 
                        horbin=int(commands[1])
                        verbin=int(commands[2])
                except Exception: return 'Unable to convert binning values to integers. Did you input numbers for the binning factors?'
                try: 
                        dummy=indi.set_and_send_float("SX CCD SXVR-H694","CCD_BINNING","HOR_BIN",horbin)
                        dummy=indi.set_and_send_float("SX CCD SXVR-H694","CCD_BINNING","VER_BIN",verbin)
                except Exception: return 'Unable to change the binning factor on the camera. Check connection'
                return 'Successfully changed binning factors of the CCD readout.'

        def cmd_imageType(self,the_command):
                '''This function changes the image type of the readout. This will change the image type in the indi library to a suitable state, as well as change the global variable that will populate the images to the indicated type. So, for light images, the image type will be LIGHT and this same keyword will populate the header file. For arc images, the image type will still be LIGHT, but the header keywork will be ARC. '''
                commands=str.split(the_command)
                if len(commands)!=2: return 'Invalid number of arguments. Just put an image type here'
                try: 
                        self.imtype=commands[1].upper()
                        if self.imtype in self.frame_types:
                                for i in self.frame_types:
                                        if i==self.imtype: dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i,'On')
                                        else: dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i,'Off')
                        else:
                                for i in self.frame_types:
                                        if i=='LIGHT': dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i,'On')
                                        else: dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i,'Off')
                except Exception: return 'Unable to change image type'
                for i in self.frame_types:
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
                print 'Got this far'
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
		hdu.header.update('EXPTIME', self.endTime-self.startTime, comment='The frame exposure time in seconds')	
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
		hdu.header.update('CAMTEMP', indi.get_float("SX CCD SXVR-H694","CCD_TEMPERATURE","CCD_TEMPERATURE_VALUE"), 'Camera temperature (C)')
		hdu.header.update('SETPOINT', self.ccdSetpoint, 'Camera temperature setpoint (C)')
		hdu.header.update('COOLING', indi.get_text("SX CCD SXVR-H694","COOLER_CONNECTION","CONNECT_COOLER"), 'Camera cooling enabled?')
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
