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


#Should have a socket connection to the telescope software here so we can adjust the position of the telescope
#according to the star centering function


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # This client_socket is to communicate with the telescope
client_socket.connect(("10.238.16.11",3041))			  # note: IP for Bisque: 10.238.16.11, IP for Mead: 10.238.16.12
client_socket.settimeout(10)


class ImagingSourceCameraServer:

	# The central pixel coordinates
	central_xpixel = 320.0   # 640 x pixel width
	central_ypixel = 240.0   # 480 y pixel height
	xaxis_flip = 1.0
	north_vector = [0,0]
	east_vector = [0.0]
	theta = 1 
	transformation_matrix = [math.cos(self.theta), math.sin(self.theta), -1*math.sin(self.theta), math.cos(self.theta)]	

	# Transformation matrix to be visualised as follows:
	#
	#    |   cos(theta)   sin(theta)   |      ie      |   transformation_matrix[0]  transformation_matrix[1]   |
	#    |  -sin(theta)   cos(theta)   |              |   transformation_matrix[2]  transformation_matrix[3]   |
	#
	# Transformation matrix is a rotation matrix.

	#Store the default camera settings here
	frameRateDefault = 30.0
	exposureAutoDefault = 3
	exposureAbsoluteDefault = 333
	gainDefault = 1023
	brightnessDefault = 0
	gammaDefault = 100

	#Put in the allowed values for relevant options
	#We give an array for each variable
	frameRateAllowedValues = range(1,241) #setting up the allowed frame rates to be in 0.25 increments 
	for r in range(0,len(frameRateAllowedValues)):
		frameRateAllowedValues[r] = frameRateAllowedValues[r]*0.25
	exposureAutoAllowedValues = range(0,4)
	exposureAbsoluteAllowedValues = range(1, 36000001)
	gammaAllowedValues = range(1, 501)
	brightnessAllowedValues = range(0, 64)
	gainAllowedValues = range(260, 1024)



#********************* A bunch of sub commands to make the analysis easier ***********************#

	def is_float_try(self, stringtry):
		try:
			float(stringtry)
			return True
		except ValueError:
			return False

	def get_user_input(self, name_of_input, default_value, allowed_range):
		value = ''
		for i in range(0,3): # Gives the user 3 attemps for each parameter before default settings are used
			value = raw_input('Please input '+name_of_input+' (range: '+str(allowed_range[0])+' to '+str(allowed_range[-1])+' in increments of '+str(allowed_range[1]-allowed_range[0])+'): ')
			if value == 'quit' or value == 'exit': sys.exit('Goodbye.') # <-- Change this so the socket_server deals with this
			if self.is_float_try(value): 
				value = float(value)
				if value in allowed_range: break # Makes sure our setting is within the allowed range
				print 'Value not in allowed range.'
			if value == '':
				print 'Default setting used'
				return default_value
				sys.exit('Program quit due to internal error.')
			if not self.is_float_try(value): print 'WARNING invalid input'
			if not self.is_float_try(value) and i == 2: 
				print 'Default setting used'
				return default_value
			if not float(value) in allowed_range and i == 2: 
				print 'Default setting used'
				return default_value
		return value
	

	def find_brightest_star(self, readinfile):
		try: starfile = open(readinfile)
		except Exception: return 'ERROR file not found' # <-- change this to returning a number
		startemp = starfile.readlines()
		brighteststar = 50
		xpixel = 0
		ypixel = 0
		for lines in startemp:
			if lines[0][0] != '#': #don't want the comments
				linetemp = str.split(lines)
				if float(linetemp[2]) < brighteststar:
					brighteststar = float(linetemp[2])
					xpixel = float(linetemp[0])
					ypixel = float(linetemp[1])
		return [brighteststar, xpixel, ypixel]


	def check_if_file_exists(self, filename):
		i = 0 # counter to stop this going on forever
		while os.path.isfile(filename):
			temp = raw_input("'"+filename"' already exists. Do you wish to override it? (yes/no): ")
			if temp == 'yes': os.remove(filename)
			elif temp == 'no': filename = raw_input('Please enter a new output file name: ')
			else: 'Enter yes or no.'
			if i > 5: sys.exit('Goodbye.')
			i += 1
		return filename


#******************************* The main camera commands ***********************************#

	def camera_orientation(self):
		'''This can be used to find the orientation of the camera. We can do this by taking an image,
		moving the camera a little North and taking another image, and finding the NS axis on the image,
		and then do the same moving the camera a little East. Find the orientation by comparing the before
		and after positions of the star after each move. We can then use the orientaion to give correct
		commands to the telescope.'''
		# We need to call the capture command
		self.single_image_capture()
		
		# Take image, find brightest stars pixel coordinates
		original_point = self.find_brightest_star('single_image_output.txt')
		
		# Move telescope North slightly
		client_socket.send('move north')
		time.sleep(1)
		client_socket.send('s')

		# Take image, find brightest stars pixel coordinates
		self.single_image_capture()
		northmove_point = self.find_brightest_star('single_image_output.txt')
		
		# Compare with previous coordinates and get a North vector
		north_vector = [float(original_point[0]) - float(northmove_point[0]), float(original_point[1]) - float(northmove_point[1])]
		
		# Now find the angle of this vector to find theta
		
		self.theta = math.atan(abs(north_vector[1])/abs(north_vector[0]))
		if (float(original_point[0]) > float(northmove_point[0])) and (float(original_point[1]) > float(northmove_point[1])):
			#add math.pi to theta
		elif (float(original_point[0]) > float(northmove_point[0])):
			#add (math.pi)/2 to theta
		elif (float(original_point[1]) > float(northmove_point[1])):
			#minus (math.pi)/2 to theta
		elif (float(original_point[0]) - float(northmove_point[0])) = 0 and (float(original_point[1]) > float(northmove_point[1])):
			#theta = math.pi
		elif (float(original_point[0]) - float(northmove_point[0])) = 0 and (float(original_point[1]) < float(northmove_point[1])):
			#theta = 0
		else: #Somethings screwed up		

		# Move telescope East slightly
		client_socket.send('move east')
		time.sleep(1)
		client_socket.send('s')
		
		# Take image, find brighest stars pixel coordinates
		self.single_image_capture()
		eastmove_point = self.find_brightest_star('single_image_output.txt')
		east_vector = [float(northmove_point[0]) - float(eastmove_point[0]), float(northmove_point[1]) - float(eastmove_point[1])]
		#Transform this vector into our new coordinate system. If the 'x' componant is positive, we're fine
		#if it's negative however, we need to flip the x axis so +ve on the camera = West and -ve on the camera = East
		new_vectorend = [float(transformation_matrix[0]*north_vector[0] + float(transformation_matrix[1]*north_vector[1], \
			         float(transformation_matrix[2]*north_vector[1] + float(transformation_matrix[3]*north_vector[1]]

		# We also need to transform the northmove_point for comparison
		new_vectorstart = [float(transformation_matrix[0]*east_vector[0] + float(transformation_matrix[1]*east_vector[1], \
			           float(transformation_matrix[2]*east_vector[1] + float(transformation_matrix[3]*east_vector[1]]

		# The north componant of this vector *should* be (basically) zero as we have only moved East.
		# Possibly put a check in here to make sure that is the case.
		eastdirection_vector = [new_vectorend[0] - new_vectorstart[0] , new_vectorend[1] - new_vectorstart[1]]
		# eastdirecton_vector[0] == 0
		if new_vectorstart[1] > new_vectorend[1]: self.xaxis_flip = -1.0 # We need to flip the 'x-axis' in this case !!!!!!!
		else: self.xaxis_flip = 1.0

		# Now look at location of star wrt central pixel
		# Current location in camera pixel coordinates is new_vectorend

		#current_position = [float(eastmove_point[0]) - self.central_xpixel , float(eastmove_point[1]) - self.central_ypixel]
		#current_poscoordchange = [float(transformation_matrix[0]*current_position[0] + float(transformation_matrix[1]*current_position[1], \
					  float(transformation_matrix[2]*current_position[0] + float(transformation_matrix[2]*current_position[1]]

		# We need to possibly flip the x-axis, depending
		#flip_axis_command = [current_poscoordchange[0] , current_poscoordchange[1]*self.xaxis_flip]

		# We now need to convert pixel distance 
		#command_to_send_telescope = [flip_axis_command[0]*self.some_x_conversion , flip_axis_command[1]*self.some_y_conversion]
		# command_to_send_telescope = [ Left move, Up move ]

		#client_socket.send(commands) # !!!!!!!!!!!!!!!!!!!!!!!! FIX 



	def set_camera_values(self):
		'''This sets up the camera with the exposure settings etc. wanted by the user.'''
		frameRateValue = self.get_user_input('Frame Rate', frameRateDefault, frameRateAllowedValues)
		exposureAutoValue = self.get_user_input('Exposure Auto', exposureAutoDefault, exposureAutoAllowedValues)
		exposureAbsoluteValue = self.get_user_input('Exposure Absolute', exposureAbsoluteDefault, exposureAbsoluteAllowedValues)
		gainValue = self.get_user_input('Gain', gainDefault, gainAllowedValues)
		brightnessValue = self.get_user_input('Brightness', brightnessDefault, brightnessAllowedValues)
		gammaValue = self.get_user_input('Gamma', gammaDefault, gammaAllowedValues)*100
		
		dev = unicap.Device( unicap.enumerate_devices()[0] )
		
		fmts = dev.enumerate_formats()
		
		props = dev.enumerate_properties()
		
		prop = dev.get_property( 'frame rate' )
		prop['value'] = float(frameRateValue)
		print float(frameRateValue)
		dev.set_property( prop )
		
		prop = dev.get_property( 'Exposure, Auto' )
		prop['value'] = int(exposureAutoValue) # default should be 1
		dev.set_property( prop )
		
		prop = dev.get_property( 'Exposure (Absolute)' )
		prop['value'] = int(exposureAbsoluteValue)
		dev.set_property( prop )
		
		prop = dev.get_property( 'Gain' )
		prop['value'] = int(gainValue) # default should be max
		dev.set_property( prop )
		
		prop = dev.get_property( 'Brightness' )
		prop['value'] = int(brightnessValue) # default should be 0
		dev.set_property( prop )
		
		prop = dev.get_property( 'Gamma' )
		prop['value'] = int(gammaValue) # default should be 100 ie linear
		dev.set_property( prop )



	def single_image_capture(self):
		'''This captures the image we will use for centering bright stars.'''
		# start capturing video
		# For this we wont want massively long exposures, just exposures that are long enough so should
		# not use the user input settings.
		dev.start_capture()
		
		dev.set_property( prop )
		imgbuf = dev.wait_buffer( 10 ) #Prolly wont work with the below
		time.sleep(10)  # Give the camera some time to adjust itself before taking photos
				# Instead of this might need to take photos and discard to get desired effect
		dev.set_property( prop )
		t1 = time.time()
		imgbuf = dev.wait_buffer( 11 )
		dt = time.time() - t1
		#print 'dt: %f  ===> %f' % ( dt, 1.0/dt )
		filename = "single_image.raw" #These perhaps as global variables?
		filename2 = "single_image.jpg"
		filename3 = "single_image.fits"
		#filename="i"+str(i)+".raw"
		#filename2 = "i"+str(i)+".jpg"
		#filename3 = "i"+str(i)+".fits"
		#print filename
		#dummy = imgbuf.save( filename )
		rgbbuf = imgbuf.convert( 'RGB3' )
		dummy = rgbbuf.save( filename ) #saves it in RGB3 raw image format
		Image.open( filename ).save( filename2 ) #saves as a jpeg
		os.system("convert -depth 8 -size 640x480+17 "+ filename +" "+ filename3) #saves as a fits file
		#Image.open( filename ).save( filename3 ) 
		#print dummy
		#print 'Captured an image. Colourspace: ' + str( imgbuf.format['fourcc'] ) + ', Size: ' + str( imgbuf.format['size'] )
		
		#print imgbuf.get_pixel((0,0))
		#print imgbuf.get_pixel((1,1))
		
		#rgbbuf = imgbuf.convert( 'RGB3' )
		#dummy = rgbbuf.save( 'test.raw' )
		#print dummy
		
		#Image.open( 'test.raw').save( 'test.jpg' )
		
		dev.stop_capture()



	def star_centering(self): #sort some global variables
		'''This checks the position of the brighest star in shot with reference to the center of the frame.
		If the star is too far from the center it will send a command to the telescope to move, and the
		process will repeat untill we have a centered star.'''
		centering = 1
		while centering:
			self.single_image_capture()
			#infile = raw_input('Please enter an input file: ')
			infile = 'single_image.fits' #for automation just call centering photos this for simplicity
			#outfile = raw_input('Please enter an output file: ')
			outfile = 'single_image_output.txt'
			outfile = self.check_if_file_exists(outfile) # the doafind function wont overwrite existing files so
								     # if we want to do this, we have to first delete the file
			iraf.noao(_doprint=0)     # load noao
			iraf.digiphot(_doprint=0) # load digiphot
			iraf.apphot(_doprint=0)   # load apphot
		
			iraf.daofind(image=infile, output=outfile) # this will take a fits file
								   # find all the stars and return
								   # a list of them in a text file
			brightest_star_info = self.find_brightest_star(outfile)
			star_mag = float(brightest_star_info[0])
			xpixel_pos = float(brightest_star_info[1])
			ypixel_pos = float(brightest_star_info[2])
			# Find distance from the center of the image
			x_distance = float(self.central_xpixel) - xpixel_pos
			y_distance = float(self.central_ypixel) - ypixel_pos
			vector_to_move = [x_distance, y_distance]
			if math.hypot(x_distance, y_distance) > somelimit:  # !!! <-- Need to decide a limit
				translated_x = (self.transformation_matrix[0]*x_distance + self.transformation_matrix[1]*y_distance)*self.xaxis_flip
				translated_y =  self.transformation_matrix[2]*x_distance + self.transformation_matrix[3]*y_distance
				#Need to convert distance into coordinates for the telescope orientation
				#Tell telescope to move
				#client_socket.send(COMMAND)
				# we should have it in RA Dec
			else: centering = 0 # Star is centered so we can stop the loop




	def capture_images(self, upperlimit):
		'''This takes the photos to be used for science.'''
		self.star_centering() # first we need to center the star we wish to image
		dev.start_capture()
		dev.set_property( prop )
		imgbuf = dev.wait_buffer( 10 ) #Prolly wont work with the below
		time.sleep(10)  #Give the camera some time to adjust itself before taking photos
				#Instead of this might need to take photos and discard to get desired effect
		
		for i in range( 0, upperlimit ):
			dev.set_property( prop )
			t1 = time.time()
			imgbuf = dev.wait_buffer( 11 )
			dt = time.time() - t1
			#print 'dt: %f  ===> %f' % ( dt, 1.0/dt )
			filename="i"+str(i)+".raw"
			filename2 = "i"+str(i)+".jpg"
			filename3 = "i"+str(i)+".fits"
			#print filename
			#dummy = imgbuf.save( filename )
			rgbbuf = imgbuf.convert( 'RGB3' )
			dummy = rgbbuf.save( filename ) # saves it in RGB3 raw image format
			Image.open( filename ).save( filename2 ) # saves as a jpeg
			os.system("convert -depth 8 -size 640x480+17 "+ filename +" "+ filename3) # saves as a fits file
			#Image.open( filename ).save( filename3 ) 
			#print dummy
		#print 'Captured an image. Colourspace: ' + str( imgbuf.format['fourcc'] ) + ', Size: ' + str( imgbuf.format['size'] )
		#print imgbuf.get_pixel((0,0))
		#print imgbuf.get_pixel((1,1))
		#rgbbuf = imgbuf.convert( 'RGB3' )
		#dummy = rgbbuf.save( 'test.raw' )
		#print dummy
		#Image.open( 'test.raw').save( 'test.jpg' )
		dev.stop_capture()




