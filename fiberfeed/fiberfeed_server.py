# coding: utf-8
# A user can input the settings they want and then the program will take some images with the camera using these settings

import unicap
import time
import sys
import Image
import pyfits
import numpy
import os
import pyraf
from pyraf import iraf
import math
import socket

class FiberFeedServer:

	try:
		for i in unicap.enumerate_devices():
			if (i['model_name']=='DMK 21AU618.AS')&(i['vendor_name']==''):
				dev = unicap.Device(i) # I am assuming this will be the camera on the fiberfeed
		print dev
	except Exception: print 'Could not find the right camera. Check that it is connected.'


	magnitude_conversion = 0 # How to convert from the magnitude iraf gives out and the actual magnitude of a star.
				 # I *think* you just add this number (when calculated) to all Iraf mags and you're set.
	
	# The central pixel coordinates
	target_xpixel = 320.0   # 640 x pixel width
	target_ypixel = 240.0   # 480 y pixel height
	north_move_arcmins = 1
	east_move_arcmins = 1
	oneArcmininPixelsN = 1/2.  # This tells us how many pixels there are to one arcsecond in the North/South direction
	oneArcmininPixelsE = 1/2.  # This tells us how many pixels there are to one arcsecond in the East/West direction
	axis_flip = 1.0
	theta = 0 
	transformation_matrix = [math.cos(theta), math.sin(theta), -1*math.sin(theta), math.cos(theta)]	
	
	# Transformation matrix to be visualised as follows:
	#
	#    |   cos(theta)   sin(theta)   |      ie      |   transformation_matrix[0]  transformation_matrix[1]   |
	#    |  -sin(theta)   cos(theta)   |              |   transformation_matrix[2]  transformation_matrix[3]   |
	#
	# Transformation matrix is a rotation matrix.
	
	#Store the default camera settings here
	frameRateDefault = 30.0
	exposureAutoDefault = 1
	exposureAbsoluteDefault = 333
	gainDefault = 260
	brightnessDefault = 0
	gammaDefault = 100

	
	#Put in the allowed values for each option
	#We give an array for each variable
	frameRateRange = list(numpy.arange(1,60.25,step=0.25)) #setting up the allowed frame rates to be in 0.25 increments 
	exposureAutoRange = range(0,4)
	exposureAbsoluteRange = range(1, 36000001)
	gammaRange = range(1, 501)
	brightnessRange = range(0, 64)
	gainRange = range(260, 1024)

	# writing all these in arrays shortens the code later on
	properties = ['frame rate', 'Exposure, Auto', 'Exposure (Absolute)', 'Gain', 'Brightness', 'Gamma']
	set_values = [frameRateDefault, exposureAutoDefault, exposureAbsoluteDefault, gainDefault, brightnessDefault, gammaDefault]
	allowed_range = [frameRateRange, exposureAutoRange, exposureAbsoluteRange, gainRange, brightnessRange, gammaRange]
	default_values = [frameRateDefault, exposureAutoDefault, exposureAbsoluteDefault, gainDefault, brightnessDefault, gammaDefault]
	# We initially have the values to set as being the default values (some values unicap gave)

	image_chop=False
	
#******************************* The main camera commands ***********************************#

	def cmd_captureImages(self, the_command):
		'''This takes the photos to be used for science. Input the name of the images to capture (images will then be
		numbered: ie filename1.fits filename2.fits) and the number of images to capture. Note: when specifying a filename
		you do not need to include the extention: ie input "filename" not "filename.fits". Optional input is to force the routine to not show the images once it has taken them. Just add 'no' at the end of the call. '''
		commands = str.split(the_command)
		if len(commands) < 3: return 'Please input number of images to capture.'
		try: int(commands[2])
		except Exception: return 'Invalid number.'
		upperlimit = int(commands[2])
		base_filename = commands[1]
		if len(commands)==3:
			capture = self.capture_images(base_filename, upperlimit)
			if not capture: return 'ERROR capturing images'
		if (len(commands)==4):
			if (commands[3]=='no'):
				capture = self.capture_images(base_filename, upperlimit,show=False)
				if not capture: return 'ERROR capturing images'
			else:
				return 'Type "no" for no image display. Otherwise, leave empty.'
		return 'Capture complete'

	def cmd_brightStarCoords(self, the_command):
		'''This takes one photo to be used to detect the brightest star and find its coordinates. '''
		#capture image from the camera and save it as a fits file
		try: dummy = self.cmd_imageCube('imageCube guiding_test')
		except Exception: print 'Could not capture images'
		#analyse the image using iraf and find the brightest star. This step requires iraf's daofind to be fully setup with stuff on eparam/
		try: brightcoords = self.analyseImage('program_images/guiding_test.fits','program_images/guiding_test.txt')
		except Exception: return 'Could not analyse image.'
		#return the coordinates, magnitude and sharpness
		if brightcoords == 0: return 'no stars found.'
		return str(brightcoords[0])+' '+str(brightcoords[1])+' '+str(brightcoords[2])+' '+str(brightcoords[3])


	def cmd_adjustExposure(self, the_command):
		'''This function will adjust the exposure time of the camera until the brightest pixel is between a given range, close to the 8 bit resolution maximum of the imagingsource cameras (255)'''
		max_pix=0
		print 'Adjusting exposure time. Please wait.'
		while (max_pix < 200)|(max_pix>245):
			try: dummy = self.cmd_captureImages('captureImages exposure_adjust 5 no')
			except Exception: print 'Could not capture image'
			im=pyfits.getdata('exposure_adjust_4.fits')
			max_pix=im.max()
			print 'max_pix=',max_pix
			if max_pix < 200:
				prop = self.dev.get_property('Exposure (Absolute)')
				if prop['value'] < 10000:
					if max_pix < 100:
						prop['value']+=100
					else: 
						prop['value']+=10
					print 'Exposure=',prop['value']*10**(-4),'s'
					self.dev.set_property( prop )
					self.set_values[2]=prop['value']
				else: 
					return 'Exposure too big already, maybe there is no star in the field...'
			if max_pix > 245:
				prop = self.dev.get_property('Exposure (Absolute)')
				if prop['value']> 51:
					prop['value']-=50
					print 'Exposure=',prop['value'],'ms'
					self.dev.set_property( prop )
					self.set_values[2]=prop['value']
				elif prop['value']<51 and prop['value']>2: 
					prop['value']-=1
					print 'Exposure=',prop['value'],'ms'
					self.dev.set_property( prop )
					self.set_values[2]=prop['value']
				else: return 'Exposure too short to reduce. Maybe this is too bright?'
		return 'Finished adjusting exposure'
		
	def cmd_setCameraValues(self,the_command):
		'''This sets up the camera with the exposure settings etc. wanted by the user. If no input is given this will list the allowed values for each of the settings, otherwise a user can set each setting individually. The properties are: \nFrameRate \nExposureAuto \nExposureAbs \nGain \nBrightness \nGamma. \nTo set a property type: setCameraValues FrameRate 3 \nTo get a list of properties type: setCameraValues show.\nTo use the default settings type "setCameraValues default"'''
		commands = str.split(the_command)
		if len(commands) == 1:
			message = ""
			for i in range(0, len(self.properties)-1):
				message += " property: "+self.properties[i]+', allowed range: '+str(self.allowed_range[i][0])+' to '+str(self.allowed_range[i][-1])+', in increments of: '+str(float(self.allowed_range[i][1]) - int(self.allowed_range[i][0]))+"\n"
			return message
		elif len(commands) == 2 and commands[1] == 'show':
			message = ''
			for i in range(0, len(self.properties)):
				message += '\n'+self.properties[i]+': '+str(self.set_values[i])
			return message+'\n'

		elif len(commands) == 2 and commands[1] == 'default':
			for i in range(0,len(self.properties)-1):
				prop = self.dev.get_property( self.properties[i] )
				prop['value'] = float(self.default_values[i])
				self.dev.set_property( prop )
				self.set_values=self.default_values
			return 'Default settings used for all properties.'

		elif len(commands) == 3:
			#fmts = self.dev.enumerate_formats()
			#props = self.dev.enumerate_properties()
			pro = commands[1]
			try: float(commands[2])
			except Exception: return 'Invalid input'
			if pro == 'FrameRate' and float(commands[2]) in self.allowed_range[0]: self.set_values[0] = float(commands[2])
			elif pro == 'ExposureAuto' and float(commands[2]) in self.allowed_range[1]: self.set_values[1] = int(commands[2])
			elif pro == 'ExposureAbs' and float(commands[2]) in self.allowed_range[2]: self.set_values[2] = int(commands[2])
			elif pro == 'Gain' and float(commands[2]) in self.allowed_range[3]: self.set_values[3] = int(commands[2])
			elif pro == 'Brightness' and float(commands[2]) in self.allowed_range[4]: self.set_values[4] = int(commands[2])
			elif pro == 'Gamma' and float(commands[2]) in self.allowed_range[5]: self.set_values[5] = int(commands[2])
			else: return 'Invalid input, type "setCameraValues show" for a list of current values and ranges'
			for i in range(0,len(self.properties)-1):
				prop = self.dev.get_property( self.properties[i] )
				prop['value'] = float(self.set_values[i])
				try: self.dev.set_property( prop )
				except Exception: 
					self.set_values[i] = self.default_values[i]
					return 'Property update failed. Error when updating: '+str(prop['identifier'])
			return str(pro)+' value updated'

		else: return 'Invalid command. Type "setCameraValues" for a list of allowed inputs and ranges'
		

	def cmd_starDistanceFromCenter(self, the_command):
		'''This checks the position of the brighest star in shot with reference to the center of the frame and
		the sharpness of the same star. A call to this function will return a vector distance between the centeral
		pixel and the brightest star in arcseconds in the North and East directions. When calling this function 
		you must specify which file for daofind to use (do not add the file extension, ie type "filename" NOT "filename.fits"'''
		commands = str.split(the_command)
		if len(commands) != 2: return 'Invalid input, give name of file with data.'
		filename = commands[1]	
		dDec = 0
		dAz = 0
		brightest_star_info = self.analyseImage(filename+'.fits', filename+'.txt') 
		if not brightest_star_info: return 'No star found to measure distance to'
		star_sharp = float(brightest_star_info[3])  # We will use this to check the focus of the star
		star_mag = float(brightest_star_info[0])    # We use this to identify the brightest star
		xpixel_pos = float(brightest_star_info[1])  # x pixel position of the brightest star
		ypixel_pos = float(brightest_star_info[2])  # y pixel position of the brightest star
		# Find distance from the center of the image
		x_distance = float(self.target_xpixel) - xpixel_pos # The position of the star relative to the central pixel
		y_distance = float(self.target_ypixel) - ypixel_pos
		vector_to_move = [x_distance, y_distance]
		print vector_to_move 
		translated_N = self.transformation_matrix[0]*x_distance + self.transformation_matrix[1]*y_distance
		translated_E =  (self.transformation_matrix[2]*x_distance + self.transformation_matrix[3]*y_distance)*self.axis_flip

		#Need to convert distance into coordinates for the telescope orientation

		# we should have it in RA Dec
		dArcminN = translated_N/self.oneArcmininPixelsN
		dArcminE = translated_E/self.oneArcmininPixelsE # Now we convert where to move a positive is a move East
		return str([dArcminN, dArcminE])
		# ^ This returns the distance between the central pixel and the brightest star in arcmins in the North and East directions		
		
	def cmd_orientationCapture(self, the_command):  # need to have some define settings for this perhaps who knows
		'''This will take the photos for camera orientation and automatically name them so that another function 
		can calculate the orientation easily. For the base photograph type the command "base", to take the 
		photograph after the telescope has been moved North type "north amountmoved" where amountmoved is in arcseconds. 
		To take the photograph after the telescope has been moved East type "east amountmoved" where again amountmoved 
		is in arcseconds'''
		commands = str.split(the_command)
		image_name = ''
		if len(commands) == 2 and commands[1] == 'base': image_name = 'base_orientation'
		elif len(commands) == 3:
			if commands[1] == 'North' and self.is_float_try(commands[2]):
				image_name = 'north_orientation'
				self.north_move_arcmins = float(commands[2])
			elif commands[1] == 'East' and self.is_float_try(commands[2]):
				image_name = 'east_orientation'
				self.east_move_arcmins = float(commands[2])
			else: return 'ERROR see help'
		else: return 'Invalid input'

		capture = self.cmd_imageCube('imageCube '+image_name)
		if not 'Final image created' in capture: return 'ERROR capturing image'
		else: return str(commands[1])+' image captured.' # change this to a number perhaps for ease when automating

	def cmd_focusCapture(self,the_command):
		'''This will capture the images to be used for focusing an image. When calling this image you need
		to give the function the focuser counts the photo is being taken at. Might make life easier to combine
		this with the orientate capture'''
		commands = str.split(the_command)
		if len(commands) !=2: return 'ERROR'
		try: focus_count = int(commands[1])
		except Exception: return 'ERROR'
		filename = 'focusImage'

		capture = self.capture_images(filename, 1)
		if not capture: return 'ERROR capturing images'

		bright_star_info = self.analyseImage(filename+'.fits', 'focus_output.txt')
		sharpness_value = bright_star_info[3]
		return sharpness_value

	def cmd_calculateCameraOrientation(self, the_command):
		'''This does the maths for the camera orientation. Theta is the angle between the positive x axis of the camera and the North direction'''
		base_star_info = self.analyseImage('program_images/base_orientation.fits','program_images/base_orientation.txt')
		north_star_info = self.analyseImage('program_images/north_orientation.fits','program_images/north_orientation.txt')
		east_star_info = self.analyseImage('program_images/east_orientation.fits','program_images/east_orientation.txt')
		if base_star_info == 0 or north_star_info == 0 or east_star_info == 0:
			return 'Orientation photos need to be taken or no stars detected.'
		#brightest_star_info = self.find_brightest_star(outfile) # need to account for error here
									 # also what if brighter star comes into field of view?
		#star_sharp = float(brightest_star_info[3])    # We will use this to check the focus of the star
		
		try:
			base_xpixel_pos = float(base_star_info[1])    # x pixel position of the brightest star
			base_ypixel_pos = float(base_star_info[2])    # y pixel position of the brightest star
			#base_star_mag = float(brightest_star_info[2]) # We use this to identify the brightest star
			north_xpixel_pos = float(north_star_info[1])
			north_ypixel_pos = float(north_star_info[2])
			#north_star_mag = float(north_star_info[2])
			east_xpixel_pos = float(east_star_info[1])  # The east move is to determine if we need a swap or not
			east_ypixel_pos = float(east_star_info[2])
			#east_star_mag = float(east_star_info[2])
		except Exception: return 'For some reason, could not convert pixel positions to floats...'

		print 'base position= ',base_star_info
		print 'north position= ',north_star_info
		print 'east position= ',east_star_info

		vector_movedN = [north_xpixel_pos - base_xpixel_pos, north_ypixel_pos - base_ypixel_pos]
		print 'vector_movedN ',vector_movedN
		hypotenuseN = math.hypot(vector_movedN[0], vector_movedN[1]) # this is number of pixels moved whilst moving North
		self.oneArcmininPixelsN = hypotenuseN/self.north_move_arcmins
		print 'hypotenuseN ',hypotenuseN, ' oneArcmininPixelsN', self.oneArcmininPixelsN

		if vector_movedN[0] == 0 and vector_movedN[1] > 0: self.theta = math.pi/2.0
		elif vector_movedN[0] == 0 and vector_movedN[1] < 0: self.theta = 3.0*math.pi/2.0
		elif vector_movedN[1] == 0 and vector_movedN[0] > 0: self.theta = 0
		elif vector_movedN[1] == 0 and vector_movedN[0] < 0: self.theta = math.pi
		else: self.theta = math.atan(vector_movedN[1]/vector_movedN[0])
#		print str(self.theta)

		if vector_movedN[0] < 0: self.theta = math.pi+ self.theta
		print 'angle=',str(self.theta)

		# Need to recalculate the transformation matrix:
		self.transformation_matrix = [math.cos(self.theta), math.sin(self.theta), -1*math.sin(self.theta), math.cos(self.theta)]	
		print self.transformation_matrix
		vector_movedE = [east_xpixel_pos - north_xpixel_pos, east_ypixel_pos - north_ypixel_pos]
		print 'vector_movedE ',vector_movedE
		hypotenuseE = math.hypot(vector_movedE[0], vector_movedE[1]) # this is number of pixels moved for E/W
		self.oneArcmininPixelsE = hypotenuseE/self.east_move_arcmins
		print 'hypotenuseE ',hypotenuseE, ' oneArcmininPixelsE', self.oneArcmininPixelsE

		translated_y =  self.transformation_matrix[2]*vector_movedE[0] + self.transformation_matrix[3]*vector_movedE[1]
		print translated_y
		if translated_y <= 0: self.axis_flip = -1 # because positive is west, negative is east
		else: self.axis_flip = 1
		return 'Orientation complete '+str(self.theta)

		#  The above camera orientation command uses the following definition for the axis' with all rotations
		#  being made in an anticlockwise direction
		#
		#	      W
		#             |
		#             |
		#	      |
		#  S ------------------- N
		#	      |
		#	      |
		#	      |
		#	      E
		#
		# so if we had a zero rotation angle, North would be along the x axis
		#


	def cmd_calibrateMagnitude(self, the_command):
		'''We need a way to also convert the magnitudes from IRAF to actual magnitudes. Do this by centering on a star with
		a known magnitude, reading out the maginitude from IRAF and then calculating the conversion to use for all
		future stars.'''
		commands = str.split(the_command)
		if len(commands) != 2: return 'ERROR, input actual star magnitude'
		try: star_magnitude = float(commands[1])
		except Exception: return 'ERROR, input number for star magnitude'

		self.capture_images('magnitudeCalibration', 1) # we need to neaten this up

		star_info = self.analyseImage('magnitudeCalibration.fits', 'magnitudeCalibration.txt') # put in these parameters
		try: star_magnitude_IRAF = float(star_info[0])
		except Exception: return 'ERROR reading daofind output'

		self.magnitude_conversion = float(star_magnitude) - float(star_magnitude_IRAF)
		print magnitude_conversion
		return 'Magnitude correction calibrated'

	def cmd_Chop(self, the_command):
		'''Changes the value of self.image_chop such that, if it is True, any time an image taken from the camera is analysed, only a scetion in the middle is considered. This is mostly for the purposes of adjusting the exposure and looking for bright stars.'''
		commands = str.split(the_command)
		if len(commands)==1: return 'Image chop is set to '+str(self.image_chop)
		elif len(commands)==2 and commands[1]=='on': self.image_chop=True
		elif len(commands)==2 and commands[1]=='off': self.image_chop=False
		else: return 'Incorrect usage of function. Activate chopping of images using "on" or "off".'
		return 'Image chop status set to '+str(self.image_chop)

	def cmd_imageCube(self, the_command):
		'''This function can be used to pull a series of images from the camera and coadd them in a simple way. This is slightly better process for measuring the position of a star for the purposes of guiding. In essence, this will take 10 images, average them and create a master image for analysis to be perfomed on.'''
		commands = str.split(the_command)
		if len(commands) != 2: return 'Please just specify the name of the final image'
		#make upperlimit images and average combine them.
		upperlimit = 10
		base_filename = commands[1]
		print 'Starting to capture images'
		capture = self.capture_images('program_images/'+base_filename, upperlimit,show=False)
		if not capture: return 'ERROR capturing images'
		print 'Finished capturing images'
		self.check_if_file_exists('program_images/'+base_filename+'.fits')
		self.check_if_file_exists('program_images/inlist')
		iraf.images(_doprint=0)
		os.system('ls program_images/'+base_filename+'_*.fits > inlist')
		try: iraf.imcombine(input='@inlist', output='program_images/'+base_filename+'.fits', combine='average',reject='none',outtype='integer', scale='none', zero='none', weight='none')
		except Exception: return 'Could not combine images'
		return 'Final image created. It is image program_images/'+base_filename+'.fits'

	def cmd_defineCenter(self, the_command):
		'''This function can be used to define the pixel coordinates that coincide with the optical axis of the telescope (or where we want the guide star to be at all times).'''
		commands=str.split(the_command)
		if len(commands) != 3: return 'Please specify the x and y coordinates as separate values'
		try: 
			new_x=float(commands[1])
			new_y=float(commands[2])
		except Exception: return 'ERROR: invalid coordinate format. They must be floats'
		self.target_xpixel=new_x
		self.target_ypixel=new_y
		return 'Central coordinates updated'

	def cmd_centerIsHere(self, the_command):
		'''This function can be used to define the pixel coordinates that coincide with the optical axis of the telescope (or where we want the guide star to be at all times) by taking images and working out where the bright star is. Very similar to cmd_defineCenter, but takes the images as well and defines the bright star coordinates as the central coords.'''
		commands=str.split(the_command)
		if len(commands) != 1: return 'no input needed for this function'
		dummy=self.cmd_imageCube('imageCube central')
		star_info = self.analyseImage('program_images/central.fits', 'program_images/central.txt') # put in these parameters
		try: 
			new_x=float(star_info[1])
			new_y=float(star_info[2])
		except Exception: return 'Finding brightest star failed'
		dummy=self.cmd_defineCenter('defineCenter '+str(new_x)+' '+str(new_y))
		return 'Finished updating central coordinates'

#*********************************** End of user commands ***********************************#

	def capture_images(self, base_filename, upperlimit,show=True):
		'''This takes the photos to be used for science. Input the name of the images to capture (images will then be
		numbered: ie filename1.fits filename2.fits) and the number of images to capture. Note: when specifying a filename
		you do not need to include the extention: ie input "filename" not "filename.fits"'''
		try: int(upperlimit)
		except Exception: return False

# plt.draw()
# dev.start_capture()
# imgbuf = dev.wait_buffer( 10 ) 
# b = bytearray(imgbuf.to_string())
# a = np.array(b)
# a = a.reshape(480,640)
# im = np.array(bytearray(imgbuf.tostring())).reshape(480,640)
# dev.stop_capture
		self.dev.start_capture()
		imgbuf = self.dev.wait_buffer( 10 ) 
		for i in range( 0, upperlimit ):
			#self.dev.set_property( prop )
			t1 = time.time()
			imgbuf = self.dev.wait_buffer( 11 )
			dt = time.time() - t1
			#print 'dt: %f  ===> %f' % ( dt, 1.0/dt )
			if upperlimit > 1: filename= base_filename+'_'+str(i)  # if we are taking several images we need to number them
			else: filename = base_filename
			rgbbuf = imgbuf.convert( 'RGB3' )
			dummy = rgbbuf.save( filename+'.raw' ) # saves it in RGB3 raw image format
			img = Image.open( filename+'.raw' )
			if show==True:
				img.show()
			img.save( filename+'.jpg' ) # saves as a jpeg
			os.system("convert -depth 8 -size 640x480+17 "+ filename+'.raw' +" "+ filename+'.fits') # saves as a fits file
			if self.image_chop:
				im_temp=pyfits.getdata(filename+'.fits')
				im=self.chop(im_temp)
				os.system('rm '+filename+'.fits')
				pyfits.writeto(filename+'.fits',im)
		self.dev.stop_capture()
		return True

	def analyseImage(self, input_image, outfile):
		iraf.noao(_doprint=0)     # load noao
		iraf.digiphot(_doprint=0) # load digiphot
		iraf.apphot(_doprint=0)   # load apphot
		#iraf.daofind.setParam('image',FitsFileName)		#Set ImageName
		iraf.daofind.setParam('verify','no')			#Don't verify
		iraf.daofind.setParam('interactive','no')		#Interactive
		#these parameters have to be set everytime because whenever any routine uses iraf, the settings get changed for all functions. THerefore, if the other camera changes any of the parameters, these would be set identically is daofind was attempted.
		iraf.daofind.setParam('scale',3)    #plate scale in arcsecs
		iraf.daofind.setParam('fwhmpsf',30)  #FWHM of PSF in arcsecs
#		iraf.daofind.setParam('datamin',100)  #Minimum flux for a detection of star. adjustExposure should be ran before this is attempted, making sure the star of interest is bright enough. IF the flux drops below this point then we have a problem (maybe clouds?)
		iraf.daofind.setParam('sigma',1.0)    #standard deviation of the background counts
		iraf.daofind.setParam('emission','Yes') #stellar features are positive
		iraf.daofind.setParam('datamax',255)  #Need to have somewhere else in the code that adjusts the exposure if a star saturates
		iraf.daofind.setParam('threshold',15.0)  #threshold above background where a detection is valid
		iraf.daofind.setParam('nsigma',1.5)     #Width of convolution kernel in sigma
		self.check_if_file_exists(outfile)
		try: iraf.daofind(image = input_image, output = outfile)
		except Exception: return 0
		brightest_star_info = self.find_brightest_star(outfile)
		return brightest_star_info

	def is_float_try(self, stringtry):
		try:
			float(stringtry)
			return True
		except ValueError:
			return False

	def find_brightest_star(self, readinfile):
		try: starfile = open(readinfile)
		except Exception: return 'ERROR; Unable to open file' # <-- change this to returning a number
		startemp = starfile.readlines()
		brighteststar = 50
		xpixel = 0
		ypixel = 0
		for lines in startemp:
			if lines[0][0] != '#': #don't want the comments
				linetemp = str.split(lines)
				#print linetemp
				if float(linetemp[2]) < brighteststar:
					starmag = float(linetemp[2])
					xpixel = float(linetemp[0])
					ypixel = float(linetemp[1])
					starsharp = float(linetemp[3])
					brighteststar=starmag
		try: return [starmag, xpixel, ypixel, starsharp]
		except Exception: return 0

	def check_if_file_exists(self, filename):
		#i = 0 # counter to stop this going on forever
		if os.path.isfile(filename): os.remove(filename)
		return filename


	def chop(self,im):
		'''Function that will return a section of the image that we are interested in. This will just chop off a box of width 'width' centred at middle_x,middle_y'''
		middle_y=240
		middle_x=320
		width=60
		return im[middle_y-width/2:middle_y+width/2,middle_x-width/2:middle_x+width/2]
	