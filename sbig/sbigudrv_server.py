import sbigudrv as sb
import numpy as np
import matplotlib.pyplot as plt
import pyfits
import time
import ctypes
import os
#import the tools to do time and coordinate transforms
import ctx

#the following lines establish a link with the camera via the USB port, these run 
#automatically when sbigudrv_main is excecuted
sb.SBIGUnivDrvCommand(sb.CC_OPEN_DRIVER, None,None)

r = sb.QueryUSBResults()
sb.SBIGUnivDrvCommand(sb.CC_QUERY_USB, None,r)

p = sb.OpenDeviceParams()
# The next line is the first available USB camera
p.deviceType=0x7F00
sb.SBIGUnivDrvCommand(sb.CC_OPEN_DEVICE, p, None)

p = sb.EstablishLinkParams()
r = sb.EstablishLinkResults()
sb.SBIGUnivDrvCommand(sb.CC_ESTABLISH_LINK,p,r)


class SBigUDrv:
	#Some parameters for the default status

	
        #FUNCTIONS: the following two functions are used in the imaging process, they relate to filenames and prevet crashes 
	#when there are typos in directories or	duplicate filenames
	
	#Checks to see if directory is specified, if it exists and then prompts to reinput if there is an issue.
	def checkDir(self,directory_to_check):
		if '/' in directory_to_check: 
			self.dir = ''
			path = directory_to_check +'.fits'
			#splits the address at the last /
			existTestVal=os.path.split(path)[0]
			existTestOutcome = os.path.exists(existTestVal)
			while existTestOutcome == False:
				print 'the directory specified does not exist, remove any / to save to\
				 sbig/images/ or check the directory and retry\n input directory/filename:'
				directory_to_check = raw_input()
				directory_to_check = directory_to_check.partition('.fits')[0]
				if '/' in directory_to_check:
					self.dir = ''
					existTestVal=os.path.split(directory_to_check)[0]
					existTestOutcome = os.path.exists(existTestVal)
				
				else:
					self.dir =self.defualt_dir
					existTestOutcome = True
								
		else:
			self.dir =self.defualt_dir
	
		self.fullpath = self.dir +  directory_to_check + '.fits'

	#Checks to see if the filename given exists and prompts for overight or rename if it does
	def checkFile (self,file_to_check):
		presence = os.path.exists(file_to_check)
		if presence == True:
			print 'file already exists, would you like to overwrite existing file? (yes/no)'
			selection = raw_input()
			while selection != 'yes' and selection != 'no' and selection != 'n' and selection !='y':
				print 'please enter yes or no, note if you do choose to not\
					 overwrite you will be promted to enter an alternate file name'
				selection = raw_input()
			if selection == 'yes' or selection == 'y':
				os.remove(file_to_check)
			elif selection == 'no' or selection == 'n':
				print 'please enter a new filename, if an identical filename is entered you will be notified'
			
				#offers a new name (or directory for input)
				fileInput2 = raw_input()
				filename2= fileInput2.partition('.fits')[0]
				original = self.fullpath
				self.checkDir(filename2)
				#checks to see if the new filename is identical to original input and corrects if neccessary
				while self.fullpath == original:
					print 'file name identical, please select another name'
					filename2 = raw_input()
					self.checkDir(filename2)
				#used in the focus cmd, set to false to prevent file name changes causing errors
				self.presencePrior = False
	
	#command that takes an image
	def capture(self,exposureTime,shutter,fileInput,imtype='Light'):	
		#This command checks the temperature at the time it is run
		a = sb.QueryTemperatureStatusResults()
		sb.SBIGUnivDrvCommand(sb.CC_QUERY_TEMPERATURE_STATUS,None,a)
		#A-D unit conversion
		SP = a.ccdSetpoint
		v1 = 4096.0/SP
		v2 = 10.0/(v1-1.0)
		setPointC = int(25.0 - 25.0 *((np.log(v2/3.0))/0.943906))
		v3 = 4096.0/a.ccdThermistor
		v4 = 10.0/(v3-1.0)
		TempC = 25.0 - 25.0 *((np.log(v4/3.0))/0.943906)
		TempC_rounded = round(TempC, 2)
	      	#associates the binary output of the refulation variable with on or off for the purposes of printing
		if a.enabled == 1 : reg = 'on'
		elif a.enabled == 0 : reg = 'off'
		camtemp=TempC_rounded
		ccdSetpoint=setPointC
		cooling=reg
		#Get CCD Parameters, this is required for later during readout
		p = sb.GetCCDInfoParams()
		p.request = 0
		r = sb.GetCCDInfoResults0()
		sb.SBIGUnivDrvCommand(sb.CC_GET_CCD_INFO,p,r)
		width = r.readoutInfo[0].width
		height = r.readoutInfo[0].height
		gain= r.readoutInfo[0].gain
		
		#Start the Exposure
		startTime = time.time()
		p = sb.StartExposureParams()
		p.ccd = 0
		p.exposureTime = int(exposureTime * 100)
		# anti blooming gate, currently untouched (ABG shut off)
		p.abgState = 0 

		#sets up file name
		filename= fileInput.partition('.fits')[0]
		#calls checking functions	
		self.checkDir(filename)
		self.checkFile(self.fullpath)

		#sets the shutter to open or closed.
		print ' shutter: ' + str(shutter) + '\n file: ' + str(self.fullpath) + '\n exposure: ' + str(exposureTime) + ' seconds' 
		if shutter == 'open': shutter_status = 1
		elif shutter == 'closed':shutter_status = 2
		p.openShutter = shutter_status
		sb.SBIGUnivDrvCommand(sb.CC_START_EXPOSURE,p,None)
		p = sb.QueryCommandStatusParams()
		p.command = sb.CC_START_EXPOSURE
		r = sb.QueryCommandStatusResults()
		r.status = 0
		#Wait for the exposure to end
		while (r.status & 1) == 0:
			sb.SBIGUnivDrvCommand(sb.CC_QUERY_COMMAND_STATUS,p,r)
			time.sleep(0.1)
		p = sb.EndExposureParams()
		p.ccd=0
		result = sb.SBIGUnivDrvCommand(sb.CC_END_EXPOSURE,p,None)
		#Readout the CCD
		#Start Readout
		p = sb.StartReadoutParams()
		p.ccd=0
                #No binning
		p.readoutMode=0
		#specifies region to read out, starting top left and moving over
		#entire height and width
		p.top=0
		p.left=0
		#NOTE: FOR THE CAMERA IN THE LAB HEIGHT AND WIDTH NEED TO BE HARD CODED TO THE RELEVANT VALUES AS THE GETCCDPARAMS FUNCTION GIVES 
		#ERONEOUS HEIGHTS AND WIDTHS
		p.height=height
		p.width=width
		# NOTE: WHEN USING THE LAB CAMERA THESE ARE THE WIDTHS 
		#AND HEIGHTS, FOR THE CAMERA IN THE OBSERVATORY COMMENT OUT THE NEXT 2 LINES
		#width = 3326
		#height = 2504
		result = sb.SBIGUnivDrvCommand(sb.CC_START_READOUT,p,None)
		#Set aside some memory to store the array
		im = np.zeros([width,height],dtype='ushort')
		line = np.zeros([width],dtype='ushort')
		p = sb.ReadoutLineParams()
		p.ccd = 0
		p.readoutMode=0
		p.pixelStart=0
		p.pixelLength=width
		#readout line by line
		for i in range(0,height):
			sb.SBIGUnivDrvCommand(sb.CC_READOUT_LINE,p,line)
			im[:,i]=line
		#end readout
		p = sb.EndReadoutParams()
		p.ccd=0
		sb.SBIGUnivDrvCommand(sb.CC_END_READOUT,p,None)
		im = np.transpose(im)
		#plt.imshow(im)
				
		#gets end time
		endTime = time.time()	

		#saves image as fits file
		hdu = pyfits.PrimaryHDU(im)

		#sets up fits header. Most things are self explanatory
		hdu.header.update('EXPTIME', float(exposureTime), comment='The frame exposure time in seconds')	
		hdu.header.update('NAXIS1', width, comment='Width of the CCD in pixels')
		hdu.header.update('NAXIS2', height, comment='Height of the CCD in pixels')
		hdu.header.update('GAIN', gain, comment='CCD gain in e-/ADU')
		hdu.header.update('XFACTOR', 1, 'Camera x binning factor')
		hdu.header.update('YFACTOR', 1, 'Camera y binning factor')
		#UTC time header keywords
		start=time.gmtime(startTime)
		dateobs=str(start[0])+'-'+str(start[1]).zfill(2)+'-'+str(start[2]).zfill(2)
		hdu.header.update('DATE-OBS', dateobs, 'UTC YYYY-MM-DD')
		starttime=str(start[3]).zfill(2)+':'+str(start[4]).zfill(2)+':'+str(start[5]).zfill(2)
		hdu.header.update('UTSTART', starttime , 'UTC HH:MM:SS.ss Exp. Start')
		middleTime=startTime+(endTime-startTime)/2.
		middle=time.gmtime(middleTime)
		midtime=str(middle[3]).zfill(2)+':'+str(middle[4]).zfill(2)+':'+str(middle[5]).zfill(2)
		hdu.header.update('UTMIDDLE', midtime , 'UTC HH:MM:SS.ss Exp. Midpoint')
		end=time.gmtime(endTime)
		endtime=str(end[3]).zfill(2)+':'+str(end[4]).zfill(2)+':'+str(end[5]).zfill(2)
		hdu.header.update('UTEND', endtime , 'UTC HH:MM:SS.ss Exp. End')
		ut=str(middle[2]).zfill(2)+'/'+str(middle[1]).zfill(2)+'/'+str(middle[0])+':'+str(middle[3]).zfill(2)+':'+str(middle[4]).zfill(2)+':'+str(middle[5]).zfill(2)
		hdu.header.update('JD', ctx.ut2jd(ut), 'Julian date of Midpoint of exposure')
		hdu.header.update('LST', ctx.ut2lst(ut,151.112,flag=1), 'Local sidereal time of Midpoint')
		#local time header keywords
		start=time.localtime(startTime)
		dateobs=str(start[0])+'-'+str(start[1]).zfill(2)+'-'+str(start[2]).zfill(2)
		hdu.header.update('LDATEOBS', dateobs , 'LOCAL YYYY-MM-DD')
		starttime=str(start[3]).zfill(2)+':'+str(start[4]).zfill(2)+':'+str(start[5]).zfill(2)
		hdu.header.update('LTSTART', starttime , 'Local HH:MM:SS.ss Exp. Start')
		middleTime=startTime+(endTime-startTime)/2.
		middle=time.localtime(middleTime)
		midtime=str(middle[3]).zfill(2)+':'+str(middle[4]).zfill(2)+':'+str(middle[5]).zfill(2)
		hdu.header.update('LTMIDDLE', midtime , 'Local HH:MM:SS.ss Exp. Midpoint')
		end=time.localtime(endTime)
		endtime=str(end[3]).zfill(2)+':'+str(end[4]).zfill(2)+':'+str(end[5]).zfill(2)
		hdu.header.update('LTEND', endtime , 'Local HH:MM:SS.ss Exp. End')

		hdu.header.update('CAMTEMP', camtemp, 'Camera temperature (C)')
		hdu.header.update('SETPOINT', ccdSetpoint, 'Camera temperature setpoint (C)')
		hdu.header.update('COOLING', str(cooling), 'Camera cooling enabled?')
		if exposureTime==0:
			imtype='Bias'
		elif shutter=='closed':
			imtype='Dark'
		hdu.header.update('IMGTYPE', imtype, 'Image type')
		'''
		hdu.header.update('FILTER', , 'NEED to query this')
'''
		hdu.writeto(self.fullpath)


	
	def cmd_closeLink(self,the_command):
		#turns of the temperature regualtion, if not already done, before closing the lin
		b = sb.SetTemperatureRegulationParams()
		b.regulation = 0
		b.ccdSetpoint = 1000
		sb.SBIGUnivDrvCommand(sb.CC_SET_TEMPERATURE_REGULATION, b, None)
		# No argument - this function shuts down the driver and connection to the CCD, run before quitting
		sb.SBIGUnivDrvCommand(sb.CC_CLOSE_DEVICE, None,None)
		sb.SBIGUnivDrvCommand(sb.CC_CLOSE_DRIVER, None,None)
		return 'link closed \n'

	def cmd_establishLink(self,the_command):
		#reconnects the link without having to quit the server, in case you change your mind after closing the link essentially
		sb.SBIGUnivDrvCommand(sb.CC_OPEN_DRIVER, None,None)
		r = sb.QueryUSBResults()
		sb.SBIGUnivDrvCommand(sb.CC_QUERY_USB, None,r)
		p = sb.OpenDeviceParams()
		p.deviceType=0x7F00
		sb.SBIGUnivDrvCommand(sb.CC_OPEN_DEVICE, p, None)
		p = sb.EstablishLinkParams()
		r = sb.EstablishLinkResults()
		sb.SBIGUnivDrvCommand(sb.CC_ESTABLISH_LINK,p,r)
		return 'link established \n'	

	def cmd_getCCDParams(self,the_command):
		# No argument - this function gets the CCD parameters using GET_CCD_INFO. Technically, 
		# this returns the parameters for the first CCD.
		p = sb.GetCCDInfoParams()
		p.request = 0
		r = sb.GetCCDInfoResults0()
		sb.SBIGUnivDrvCommand(sb.CC_GET_CCD_INFO,p,r)
		#Width and height are just integers.
		gain = hex(r.readoutInfo[0].gain)
		gain=float(gain[2:])*0.01
		pixel_width = hex(r.readoutInfo[0].pixel_width)
		pixel_width = float(pixel_width[2:])*0.01
		return 'width: '+str(r.readoutInfo[0].width)+ ' height: '+str(r.readoutInfo[0].height)+\
	' gain(e-/ADU): '+str(gain)+' pixel_width (microns): '+str(pixel_width)

	def cmd_setTemperature(self,the_command):
		#this command sets the temperature of the imaging CCD, input is in degrees C
		commands = str.split(the_command)
		if len(commands) < 2 : return 'error: no input value'
		b = sb.SetTemperatureRegulationParams()
		b.regulation = 1
		#tests input validity, if not an integer value then input is rejected
		try: tempC = int(commands[1])
		except Exception: return 'invalid input (Please input an integer value in degrees C)'
		#Converts the degrees C input into A-D units, A-D units are interpretted and used by the driver
		v1 = (3.0 * np.exp((0.943906 * (25.0 -tempC))/25.0))
		temp = int(4096.0/((10.0/v1) + 1.0))
		b.ccdSetpoint = temp
		sb.SBIGUnivDrvCommand(sb.CC_SET_TEMPERATURE_REGULATION, b, None)
		#calls the querey temperature command to check current CCD status
		time.sleep(0.1)	
		a = sb.QueryTemperatureStatusResults()
		sb.SBIGUnivDrvCommand(sb.CC_QUERY_TEMPERATURE_STATUS,None,a)
		#converts thermistor value and setpoint to degrees C
		SPa = a.ccdThermistor
		v2 = 4096.0/SPa	
		v3 = 10.0/(v2-1.0)
		ccdThermistorC = 25.0 - 25.0 *((np.log(v3/3.0))/0.943906)
		ccdThermistorC_rounded = round(ccdThermistorC, 2)
		#associates the binary output of the refulation variable with on or off for the purposes of printing
		if b.regulation == 1 : reg = 'on'
		elif b.regulation == 0 : reg = 'off'
		#prints useful values to screen
		return ' regulation = ' +str(reg) +'\n power = '+str(a.power) + '\n CCD set point (A/D) = '\
		    + str(a.ccdSetpoint) + ', CCD set point (C) = ' + str(tempC)+'\n current CCD temp (A/D) = '\
		    + str(a.ccdThermistor) + ', current CCD temp (C) = ' + str(ccdThermistorC_rounded) +'\n'
		
	def cmd_checkTemperature(self,the_command):
		#This command checks the temperature at the time it is run
		a = sb.QueryTemperatureStatusResults()
		sb.SBIGUnivDrvCommand(sb.CC_QUERY_TEMPERATURE_STATUS,None,a)
		#A-D unit conversion
		SP = a.ccdSetpoint
		v1 = 4096.0/SP
		v2 = 10.0/(v1-1.0)
		setPointC = int(25.0 - 25.0 *((np.log(v2/3.0))/0.943906))
		
		v3 = 4096.0/a.ccdThermistor
		v4 = 10.0/(v3-1.0)
		TempC = 25.0 - 25.0 *((np.log(v4/3.0))/0.943906)
		TempC_rounded = round(TempC, 2)

	      	#associates the binary output of the refulation variable with on or off for the purposes of printing
		if a.enabled == 1 : reg = 'on'
		elif a.enabled == 0 : reg = 'off'
		
		#prints useful values
		return 'regulation = ' +str(reg) +'\n power = '+str(a.power) + '\n CCD set point (A/D) = ' \
		    + str(a.ccdSetpoint) + ', CCD set point (C) = ' + str(setPointC)+'\n current CCD temp (A/D) = ' \
		    + str(a.ccdThermistor) + ', current CCD temp (C)' + str(TempC_rounded) + '\n'

	def cmd_disableRegulation(self,the_command):
		#disables temperature regulation, important to run before quitting
		b = sb.SetTemperatureRegulationParams()
		b.regulation = 0
		b.ccdSetpoint = 1000
		sb.SBIGUnivDrvCommand(sb.CC_SET_TEMPERATURE_REGULATION, b, None)
		a = sb.QueryTemperatureStatusResults()
		sb.SBIGUnivDrvCommand(sb.CC_QUERY_TEMPERATURE_STATUS,None,a)

		#A-D unit conversion	
		v1 = 4096.0/b.ccdSetpoint
		v2 = 10.0/(v1-1.0)
		setPointC = int(25.0 - 25.0 *((np.log(v2/3.0))/0.943906))
		
		v3 = 4096.0/a.ccdThermistor
		v4 = 10.0/(v3-1.0)
		TempC = 25.0 - 25.0 *((np.log(v4/3.0))/0.943906)
		TempC_round = round(TempC, 2)

		#associates the binary output of the refulation variable with on or off for the purposes of printing
		if b.regulation == 1 : reg = 'on'
		elif b.regulation == 0 : reg = 'off'

		return 'regulation = ' +str(reg) +'\n power = '+str(a.power) + '\n CCD set point (A/D) = '\
		    + str(a.ccdSetpoint) + ', CCD set point (C) = ' + str(setPointC)+'\n current CCD temp (A/D) = '\
		    + str(a.ccdThermistor) + ', current CCD temp (C)' + str(TempC_round)+ '\n'


	#Captures an image
	def cmd_exposeAndWait(self,command):
		# This function takes a full frame image and waits for the image to be read out
		# prior to exiting.
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
		self.defualt_dir = 'images/'
		if len(commands)==4:
			self.capture(exposureTime,shutter,fileInput)	
		else: 
			self.capture(exposureTime,shutter,fileInput,imtype=commands[4])
		return 'Exposure Complete'

	def cmd_focusCalculate(self,command):
		#This function will return the best focus position interpolating between images 1,2,3,4 and 5
		return str(2.0)
		
	def cmd_focusImages(self,command):	
		# This function takes a dark image and a serious of images at different focai. 
		# The user enters a root name and the iamges are saved to a focus folder with appropriate suffixes
		commands = str.split(command)
		if len(commands) < 2 : return 'error: enter a root filename (with optional directory address)'
		#stores root of filename
		fileInput = str(commands[1]) 
		#strips .fits off the end (if present) to prevent confusion in the code later 
		filename= fileInput.partition('.fits')[0]
		#tests to see if the specified directory exists, if no directory specified defaults to save in directory focusCal			
		self.defualt_dir = 'focusCal/'
		self.checkDir(filename)
		#Tests to see if the root file has already been saved, if it has prompt for another name or delete, since there are multiple files with each 
		#root name the existance of the dark file is checked, then self.checkFile is called, if the dark file is removed (overwritten) the second check
		#will be false and all files with that root will be removed.
		fullpathTest= self.fullpath.partition('.fits')[0]
		self.presencePrior = os.path.exists(fullpathTest+'Dark.fits')
		self.checkFile(fullpathTest + 'Dark.fits')
		presencePost = os.path.exists(fullpathTest+'Dark.fits')
		fullpathTest2= self.fullpath.partition('.fits')[0]
		if self.presencePrior == True and presencePost == False:
			os.remove(fullpathTest2+'Focus1.fits')
			os.remove(fullpathTest2+'Focus2.fits')
			os.remove(fullpathTest2+'Focus3.fits')
			os.remove(fullpathTest2+'Focus4.fits')
			os.remove(fullpathTest2+'Focus5.fits')

		#Once the directory is varified and the filename checked for duplicates the dark image is taken
		self.capture(0.1,'closed',fileInput+'Dark.fits')	
				
		#Now 5 images at varying focai are captured			
		self.capture(0.1,'open',fileInput+'Focus1.fits')	
		self.capture(0.1,'open',fileInput+'Focus2.fits')	
		self.capture(0.1,'open',fileInput+'Focus3.fits')	
		self.capture(0.1,'open',fileInput+'Focus4.fits')	
		self.capture(0.1,'open',fileInput+'Focus5.fits')

		#NEED TO CHANGE FOCUS BETWEEN IMAGE CAPTURES
		#conduct dark subtraction 
		#analyse focus using iraf tools


