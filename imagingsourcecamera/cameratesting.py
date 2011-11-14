# A user can input the settings they want and then the program will take some images with the camera using these settings

import unicap
import time
import sys

#Store the default camera settings here
frameRateDefault = 30.0
exposureAutoDefault = 3
exposureAbsoluteDefault = 333
gainDefault = 1023
brightnessDefault = 0
gammaDefault = 100


#Put in the allowed values for relevant options
frameRateAllowedValues = range(1,241) #setting up the allowed frame rates to be in 0.25 increments 
for r in range(0,len(frameRateAllowedValues)):
	frameRateAllowedValues[r] = frameRateAllowedValues[r]*0.25
exposureAutoAllowedValues = range(0,4)
exposureAbsoluteAllowedValues = range(1, 36000001)
gammaAllowedValues = range(1, 501)
brightnessAllowedValues = range(0, 64)
gainAllowedValues = range(260, 1024)

def is_float_try(stringtry):
	try:
		float(stringtry)
		return True
	except ValueError:
		return False

def get_user_input(name_of_input, default_value, allowed_range):
	value = ''
	for i in range(0,3):
		value = raw_input('Please input '+name_of_input+' (range: '+str(allowed_range[0])+' to '+str(allowed_range[-1])+' in increments of '+str(allowed_range[1]-allowed_range[0])+'): ')
		if value == 'quit' or value == 'exit': sys.exit('Goodbye.')
		if is_float_try(value): 
			value = float(value)
			if value in allowed_range: break
			print 'Value not in allowed range.'
		if value == '':
			print 'Default setting used'
			return default_value
			sys.exit('Program quit due to internal error.')
		if not is_float_try(value): print 'WARNING invalid input'
		if not is_float_try(value) and i == 2: 
			print 'Default setting used'
			return default_value
		if not float(value) in allowed_range and i == 2:
			print 'Default setting used'
			return default_value
	return value
			



frameRateValue = get_user_input('Frame Rate', frameRateDefault, frameRateAllowedValues)
exposureAutoValue = get_user_input('Exposure Auto', exposureAutoDefault, exposureAutoAllowedValues)
exposureAbsoluteValue = get_user_input('Exposure Absolute', exposureAbsoluteDefault, exposureAbsoluteAllowedValues)
gainValue = get_user_input('Gain', gainDefault, gainAllowedValues)
brightnessValue = get_user_input('Brightness', brightnessDefault, brightnessAllowedValues)
gammaValue = get_user_input('Gamma', gammaDefault, gammaAllowedValues)*100


dev = unicap.Device( unicap.enumerate_devices()[0] )

fmts = dev.enumerate_formats()


props = dev.enumerate_properties()

prop = dev.get_property( 'frame rate' )
prop['value'] = float(frameRateValue)
print float(frameRateValue)
dev.set_property( prop )

prop = dev.get_property( 'Exposure, Auto' )
prop['value'] = int(exposureAutoValue) #default should be 1
dev.set_property( prop )

prop = dev.get_property( 'Exposure (Absolute)' )
prop['value'] = int(exposureAbsoluteValue)
dev.set_property( prop )

prop = dev.get_property( 'Gain' )
prop['value'] = int(gainValue) #default should be max
dev.set_property( prop )

prop = dev.get_property( 'Brightness' )
prop['value'] = int(brightnessValue) #default should be 0
dev.set_property( prop )

prop = dev.get_property( 'Gamma' )
prop['value'] = int(gammaValue) #default should be 100 ie linear
dev.set_property( prop )


#start capturing video
dev.start_capture()

#dev.set_property( prop )
imgbuf = dev.wait_buffer( 10 )

for i in range( 0, 4 ):
	#dev.set_property( prop )
	t1 = time.time()
	imgbuf = dev.wait_buffer( 11 )
	dt = time.time() - t1
	print 'dt: %f  ===> %f' % ( dt, 1.0/dt )
	filename="i"+str(i)+".raw"
	print filename
	dummy = imgbuf.save( filename )
	print dummy
print 'Captured an image. Colourspace: ' + str( imgbuf.format['fourcc'] ) + ', Size: ' + str( imgbuf.format['size'] )
	

print imgbuf.get_pixel((0,0))
print imgbuf.get_pixel((1,1))

dev.stop_capture()

