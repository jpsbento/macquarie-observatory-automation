#****************************************************************************#
#                     Code to control the meade mount                        #
#****************************************************************************#

import serial
import sys
import select
import string
from datetime import datetime
import time

#Open port 0 at "9600,8,N,1", no timeout
ser = serial.Serial('/dev/ttyUSB0',9600, timeout = 1)  #open first serial port, we talk to the mount
                        #via serial comms
print ser.portstr       #check which port was really used
print ser.isOpen()

class MeademountServer:

#Global variables
	mountmoving = False

#A list of user commands:

	#*************START of part B General telescope info**************#

	def cmd_getRA(self,the_command):
		'''Returns the current right ascension of the telescope.'''
		ser.write(':GR#')
		return ser.read(100)

	def cmd_getDec(self,the_command):
		'''Returns the current declination of the telescope.'''
		ser.write(':GD#')
		return ser.readline()

	def cmd_getAlt(self,the_command):
		'''Returns the current Altitude of the telescope.'''
		ser.write(':GA#')
		return ser.readline()

	def cmd_getAz(self,the_command):
		'''Returns the current Azimuth of the telescope'''
		ser.write(':GZ#')
		return ser.readline()

	def cmd_getSiderealTime(self,the_command):
		'''Returns the current sidereal time.'''
		ser.write(':GS#')
		return ser.readline()

	def cmd_setSiderealTime(self,the_command): #**********************
		'''Sets the sidereal time. Format should be HH:MM:SS'''
		temp=string.split(the_command)
		if (len(temp)==1):
			return "Error, incorrect format"
		elif (len(temp)==2):
			command = ':SS '+str(temp[1])+'#'
			ser.write(command)
			return ser.readline()
		else:
			return "Error, incorrect format"
			

	def cmd_getLocalTime24(self,the_command):
		'''Gets the local time in 24 hour format'''
		ser.write(':GL#')
		return ser.readline()

	def cmd_getLocalTime12(self,the_command):
		'''Gets the local time in 12 hour format'''
		ser.write(':Ga#')
		return ser.readline()

	def cmd_setLocalTime(self,the_command): #********************
		'''Sets the local time. NOTE parameter should always be in 24 hour format.'''
		ser.write(':SL HH:MM:SS#')
		return ser.readline()

	def cmd_getCalanderDate(self,the_command):
		'''Gets the calander date.'''
		ser.write(':GC#')
		return ser.readline()

	def cmd_setCalanderDate(self,the_command): #****************more than one output
		'''Sets the calendar date.'''
		ser.write('SC MM/DD/YY#')
		message = ser.readline()
		message = message + ser.readline()
		return message

	def cmd_getLatSite(self,the_command):
		'''Gets the latitude of the currently selected site.'''
		ser.write('Gt#')
		return ser.readline()

	def cmd_setLatSite(self,the_command): #****************************
		'''Sets the latitude of the currently selected site.'''
		ser.write(':St sDD*MM#')
		return ser.readline()

	def cmd_getLongSite(self,the_command):
		'''Gets the longitude of the currently selected site.'''
		ser.write(':Gg#')
		return ser.readline()

	def cmd_setLongSite(self,the_command): #*****************************
		'''Sets the longitude of the currently selected site.'''
		ser.write(':Sg DDD*MM#')
		return ser.readline()

	def cmd_getGMToffset(self,the_command):
		'''Gets the offset from Greenwich Mean Time.'''
		ser.write(':GG#')
		return ser.readline()
		

	def cmd_setGMToffset(self,the_command): #**************************
		'''Sets the offset from Greenwich Mean Time.'''
		ser.write(':SG sHH#')
		return ser.readline()

	#****END of part B commands go here, don't understand currently****#

	#******START of part C commands to control telescope motion********#	

	def cmd_move(self,the_command):
		'''Starts motion 'north', 'south', 'east', or 'west' at the current rate.'''
		self.mountmoving = True
		commands = str.split(the_command)
		if commands[1] == 'north':
			ser.write(':Mn#')
			return 'moving north'
		elif commands[1] == 'south':
			ser.write(':Ms#')
			return 'moving south'
		elif commands[1] == 'east':
			ser.write(':Me#')
			return 'moving east'
		elif commands[1] == 'west':
			ser.write(':Mw#')
			return 'moving west'
		else:
			return 'ERROR, see "help move"'

	def cmd_slewcoord(self,the_command): #*** more than one output
		'''Slews telescope to current object coordinates'''
		ser.write(':MS#')
		return ser.readline()

	def cmd_slewaltaz(self,the_command):
		'''Slews telescope to objct atl-az coordinates(set with the
		Sa and Sz commands). This command only works in the LAND and 
		ALTAZ modes.'''
		ser.write(':MA#')
		return ser.readline()
		

	def cmd_s(self,the_command):
		'''Stops motion of telescope.'''
		self.mountmoving = False
		ser.write(':Qn#')
		ser.write(':Qs#')
		ser.write(':Qe#')
		ser.write(':Qw#')
		ser.write(':Q#')
		return 'stopped move'

	def cmd_setMotionRate(self,the_command):
		'''Sets the motion rate to 'guide', 'center', 'find' or 'slew'.'''
		commands = str.split(the_command)
		if commands[1] == 'guide':
			ser.write(':RG#')
			return 'motion rate set to guide'
		elif commands[1] == 'center':
			ser.write(':RC#')
			return 'motion rate set to center'
		elif commands[1] == 'find':
			ser.write(':RM#')
			return 'motion rate set to find'
		elif commands[1] == 'slew':
			ser.write(':RS#')
			return 'motion rate set to slew'
		else:
			return 'ERROR, see "help setMotionRate"'

	def cmd_setMaxSlewRate(self,the_command): #******************************
		'''Sets the max slew rate to "N" degrees per second
		where N is 2 through 4.'''
		commands = str.split(the_command)
		if int(commands[1]): #*** does it allow floats????
			N = int(commands[1])
			ser.write(':Sw '+N+'#')
			return ser.readline()
		else:
			return 'ERROR, see "help setMaxSlewRate"'

	#********************* Part d) Home Postion commands *******************#

	def cmd_homeSearchSavePos(self,the_command):
		'''Starts a home positions search and saves the telescope
		position. NOTE: All commands except ":Q#" and ":h?#" are
		disabled during the search.'''
		ser.write(':hS#')
		return 'home position search started, telescope position saved'

	def cmd_homeSearchSaveVal(self,the_command):
		'''Starts a home position search and sets the telescope
		position according to the saved values.  NOTE: All commands except
		 ":Q#" and ":h?#" are disabled during the search.'''
		ser.write('hF#')
		return 'home position search started, telescope pos set to saved values'

	def cmd_goHome(self,the_command):
		'''Slews the telescope to the home position.'''
		ser.write(':hP#')
		return 'slewing to home position'

	def cmd_homeStatus(self,the_command): # Need to process value
		'''Returns the home status: 0 if home search failed or not
		yet attempted, 1 if home position found, or 2 if a home
		search is in progress.'''
		ser.write(':h?#')
		return ser.readline()

	#******************* Part e) Library/Objects *********************#

	def cmd_getObjectRA(self,the_command):
		'''Gets object right ascension.'''
		ser.write(':Gr#')
		return ser.readline()

	def cmd_setObjectRA(self,the_command): # user input
		'''Sets object right ascension. Please input in form:
		HH:MM:SS'''
		commands = str.split(the_command)
		RA = commands[1]
		ser.write(':Sr '+RA+'#')
		return ser.readline()

	def cmd_getObjectDec(self,the_command):
		'''Gets object declination.'''
		ser.write(':Gd#')
		return ser.readline()

	def cmd_setObjectDec(self,the_command):
		'''Sets object declination.'''
		commands = str.split(the_command)
		DEC = commands[1]
		ser.write(':Sa '+DEC+'#')
		return ser.readline()

	def cmd_setObjectAlt(self,the_command):
		'''Sets object altitude (for MA command). Please input in
		form: sDD*MM'''
		commands = str.split(the_command)
		Alt = commands[1]
		ser.write(':Sa '+Alt+'#')
		return ser.readline()

	def cmd_setObjectAz(self,the_command):
		'''Sets object azimuth (for MA command). Please input in
		form: DDD*MM'''
		commands = str.split(the_command)
		Az = commands[1]
		ser.write(':Sz '+Az+'#')
		return ser.readline()

	def cmd_sync(self,the_command):
		'''Sync. Matches current telescope coordinates to the object
		coordinates and sends a strinf indicating which objects
		coordinates were used.'''
		ser.write(':CM#')
		

	def cmd_getFindType(self,the_command):
		'''Gets the "type" string for the FIND operation. A capital letter
		means that the corresponding type is selected while a lower case
		indicates it is not.'''
		ser.write(':Gy#')
		return ser.readline()

	def cmd_setFindType(self,the_command):
		'''Sets the 'type' string for the FIND operation. Input should
		look like: GPDCO a capital indicates the corresponding type is
		selected while a lower case indicates it is not.'''
		commands = str.split(the_command)
		findtype = commands[1]
		ser.write(':Sy '+findtype+'#')
		return ser.readline()

	def cmd_getFindMin(self,the_command): #Don't understand output
		'''Gets the current minimum quality for the FIND operation.'''
		ser.write(':Gq#')
		return ser.readline()

	def cmd_nextFindMin(self,the_command):
		'''Steps to the next minumum quantity for the FIND operation.'''
		ser.write(':Sq#')
		return 'Stepped to next min quantity for FIND'

	def cmd_getHigherLim(self,the_command):
		'''Gets the current 'higher' limit.'''
		ser.write(':Gh#')
		return ser.readline()

	def cmd_setHigherLim(self,the_command):
		'''Sets the current 'higher' limit. Please input in
		form: DD.'''
		commands = str.split(the_command)
		lim = commands[1]
		ser.write(':Sh '+lim+'#')
		return ser.readline()

	def cmd_getLowerLim(self,the_command):
		'''Gets the current 'lower' limit.'''
		ser.write(':Go#')
		return ser.readline()

	def cmd_setLowerLim(self,the_command):
		'''Sets the current 'lower limit. Please use
		form" DD'''
		commands = str.split(the_command)
		lim = commands[1]
		ser.write(':So '+lim+'*#')
		return ser.readline()

	def cmd_getBrightMagLim(self,the_command):
		'''Gets the brighter magnitude limit for the FIND operation.'''
		ser.write(':Gb#')
		return ser.readline()

	def cmd_getFaintMagLim(self,the_command):
		'''Gets the fainter magnitude limit for the FIND operation.'''
		ser.write(':Gf#')
		return ser.readline()

	def cmd_setBrightMagLim(self,the_command):
		'''Sets the brighter magnitude limit for the FIND operation.
		Please input in format: sMM.M'''
		commands = str.split(the_command)
		lim = command[1]
		ser.write(':Sb '+lim+'#')
		return ser.readline()

	def cmd_setFaintMagLim(self,the_command):
		'''Sets the fainter magnitude limit for the FIND operation.
		Please input in format: sMM.M'''
		commands = str.split(the_command)
		lim = commands[1]
		ser.write(':Sf '+lim+'#')
		return ser.readline()

	def cmd_getLargeSizeLim(self,the_command):
		'''Gets the larger size limit for the FIND operation.'''
		ser.write(':Gl#')
		return ser.readline()

	def cmd_getSmallSizeLim(self,the_command):
		'''Gets the smaller size limit for the FIND operation.'''
		ser.write(':Gs#')
		return ser.readline()

	def cmd_setLargeSizeLim(self,the_command):
		'''Sets the larger size limit for the FIND operation. Please
		use form: NNN'''
		commands = str.split(the_command)
		lim = commands[1]
		ser.write(':Sl '+lim+'#')
		return ser.readline()

	def cmd_setSmallSizeLim(self,the_command):
		'''Sets the smaller size limit for the FIND operation. Please
		use form: NNN'''
		commands = str.split(the_command)
		lim = commands[1]
		ser.write(':Ss '+lim+'#')
		return ser.readline()

	def cmd_getFieldRadius(self,the_command):
		'''Gets the field radius of the FIELD operation.'''
		ser.write(':GF#')
		return ser.readline()

	def cmd_setFieldRadius(self,the_command):
		'''Sets the field radius of the FIELD operation. Please use
		form: NNN'''
		commands = str.split(the_command)
		radius = command[1]
		ser.write(':SF '+radius+'#')
		return ser.readline()

	def cmd_startFind(self,the_command):
		'''Starts a FIND operation.'''
		ser.write(':LF#')
		return 'FIND operation started.'

	def cmd_findNextObj(self,the_command):
		'''Finds the next object in a FIND sequence.'''
		ser.write(':LN#')
		return 'Finding next object in FIND sequence.'''

	def cmd_findPrevObj(self,the_command):
		'''Finds the previous object in a FIND sequence.'''
		ser.write(':LB#')
		return 'Finding previous object in FIND sequence.'

	def cmd_fieldOp(self,the_command):
		'''Performs a FIELD operation returning a string containing
		the number of objects in the field and the object that is
		closest to the center of the field.'''
		ser.write(':Lf#')
		return ser.readline()

	def cmd_setObjNGC(self,the_command): #change help
		'''Sets the object to the NGC specified by the number. Object
		type returned depends ob which object type is selected with
		the Lo command. Please input in form: NNNN'''
		commands = str.split(the_command)
		NGC = commands[1]
		ser.write(':LC '+NGC+'#')
		return 'object set to NGC '+NGC

	def cmd_setObjMessier(self,the_command):
		'''Sets the object to the Messier specified by the number.
		Please input in form: NNNN'''
		commands = str.split(the_command)
		Messier = commands[1]
		ser.write(':LM '+Messier+'#')
		return 'object set to Messier '+Messier

	def cmd_setObjStar(self,the_command): #change help
		'''Sets the object to the Star specified by the number. Planets
		are 'stars' 901-909. Object type returned depends on which
		object type has been selected with the Ls command. Please input
		in form: NNNN'''
		commands = str.split(the_command)
		star = commands[1]
		ser.write(':LS '+star+'#')
		return 'object set to star '+star

	def cmd_objectInfo(self,the_command):
		'''Gets the current object information.'''
		ser.write(':LI#')
		return ser.readline()

	def cmd_setNGCType(self,the_command):
		'''Sets the NGC object library type. 0 is the NGC library,
		1 is the IC library, and 2 is the UGC library. This operation
		is successful only if the user has a version of the software
		that includes the desired library.'''
		commands = str.split(the_command)
		libtype = commands[1]
		ser.write(':Lo '+libtype+'#')
		return ser.readline()

	def cmd_setStarType(self,the_command):
		'''Sets the STAR object library type. 0 is the STAR library
		1 is the SAO library, and 2 is the GCVS library. This operation
		is successful only if the user has a version of the software that
		includes the desired library.'''
		commands = str.split(the_command)
		libtype = commands[1]
		ser.write(':Ls '+libtype+'#')
		return ser.readline()

	#********* Part f) Miscellaneous ***********#

	def cmd_reticleBrightness(self,the_command):
		'''Control reticle brightness. + increases, - decreases, or 
		0, 1, 2, 3 sets to one of the corresponding flashing modes.'''
		commands = str.split(the_command)
		if commands[1] == '+':
			ser.write(':B+#')
			return 'reticle brightness increased'
		elif commands[1] == '-':
			ser.write(':B-#')
			return 'reticle brightness decreased'
		elif commands[1] == '0':
			ser.write(':B0#')
			return 'reticle flashing mode 0'
		elif commands[1] == '1':
			ser.write(':B1#')
			return 'reticle flashing mode 1'
		elif commands[1] == '2':
			ser.write(':B2#')
			return 'reticle flashing mode 2'
		elif commands[1] == '3':
			ser.write(':B3#')
			return 'reticle flashing mode 3'
		else:
			return 'ERROR, see "help reticleBrightness"'

	def cmd_focus(self,the_command):
		''''out' starts focus out, 'in' starts focus in, 'stop' stops focus
		'fast' sets focus fast and 'slow' sets focus slow.'''
		commands = str.split(the_command)
		if commands[1] == 'out':
			ser.write(':F+#')
			return 'started focusing out'
		elif commands[1] == 'in':
			ser.write(':F-#')
			return 'started focusing in'
		elif commands[1] == 'stop':
			ser.write(':FQ#')
			return 'stopped focus change'
		elif commands[1] == 'fast':
			ser.write(':FF#')
			return 'set focus fast'
		elif commands[1] == 'slow':
			ser.write(':FS#')
			return 'set focus slow'
		else:
			'Error, see help'

	def cmd_getSiteName(self,the_command):
		'''Get SITE name. Put 1, 2, 3 or 4 for corresponding site name.'''
		commands = str.split(the_command)
		if commands[1] == '1':
			ser.write(':GM#')
			return ser.readline()
		elif commands[1] == '2':
			ser.write(':GN#')
			return ser.readline()
		elif commands[1] == '3':
			ser.write(':GO#')
			return ser.readline()
		elif commands[1] == '4':
			ser.write(':GP#')
			return ser.readline()
		else:
			return 'Error, see help'

	def cmd_setSiteName(self,the_command):
		'''Sets SITE name. Please input form: N XYZ where N is 
		site number and XYZ is site name.'''
		commands = str.split(the_command)
		name = commands[2]
		if command[1] == '1':
			ser.write(':SM '+name+'#')
			return ser.readline()
		elif commands[1] == '2':
			ser.write(':SN '+name+'#')
			return ser.readline()
		elif commands[1] == '3':
			ser.write(':SO '+name+'#')
			return ser.readline()
		elif commands[1] == '4':
			ser.write(':SP '+name+'#')
			return ser.readline()
		else:
			return 'Error, see help'

	def cmd_getTrackFreq(self,the_command):
		'''Gets the current track 'frequency'.'''
		ser.write(':GT#')
		return ser.readline()

	def cmd_setTrackFreq(self,the_command):
		'''Sets the current track 'frequency'. Please input in
		form: TT.T'''
		commands = str.split(the_command)
		freq = commands[1]
		ser.write('ST '+freq+'#')
		return ser.readline()

	def cmd_switchManual(self,the_command):
		'''Switch to manual.'''
		ser.write(':TM#')
		return 'set to manual'

	def cmd_switchQuartz(self,the_command):
		'''Switch to quartz.'''
		ser.write(':TQ#')
		return 'set to quartz'

	def cmd_changeManFreq(self,the_command):
		'''+ increments manual frequency by one tenth. - decrements
		manual frequency by one tenth.'''
		commands = str.split(the_command)
		if commands[1] == '+':
			ser.write(':T+#')
			return 'incremented manual frequency by one tenth'
		elif commands[1] == '-':
			ser.write('T-#')
			return 'decremented manual frequency by one tenth'
		else:
			return 'Error, see help'

	def cmd_getDistBars(self,the_command):
		'''Gets te distance 'bars' string.'''
		ser.write(':D#')
		return ser.readline()

	def cmd_setTelescopeAlignment(self,the_command):
		'''Sets the telescopes alignment type to LAND, POLAR or ALTAZ.'''
		commands = str.split(the_commands)
		if commands[1] == 'LAND':
			ser.write(':AL#')
			return 'set telescope alignment type to LAND.'
		elif commands[1] == 'POLAR':
			ser.write(':AP#')
			return 'set telescope alignment type to POLAR'
		elif commands[1] == 'ALTAZ':
			ser.write(':AA#')
			return 'set telescope alignment type to ALTAZ'
		else:
			return 'Error, see help'

	def cmd_fieldDerotator(self,the_command):
		'''Turns the field de-rotator on and off ('on' for on and
		'off' for off.. obviously.'''
		commands = str.split(the_command)
		if commands[1] == 'on':
			ser.write(':r+#')
			return 'field de-rotator on'
		elif commands[1] == 'off':
			ser.write(':r-#')
			return 'field de-rotator off'
		else:
			return 'Error, see help'

	def cmd_fan(self,the_command):
		'''Turns the fan on ('on') and off ('off').'''
		commands = str.split(the_command)
		if commands[1] == 'on':
			ser.write(':f+#')
			return 'fan is on'
		elif commands[1] == 'off':
			ser.write(':f-#')
			return 'fan is off'


#************************* End of user commands ********************************#

	#definition to write to the serial port
	#this is where we give the telescope mount a command
	#
	def serialread(self):
		
		self.data = str.split(ser.readline(),',')

		self.log(message)
		return message


	#definition to log the output, stores all data in a file
	def log(self,message):
		print(str(datetime.now())+" "+str(message)+'\n'),

#	def Altitude_check(self):
#		if self.mountmoving == True:
#			ser.write(':GA#')
#			Alt = ser.read(10)
#			temp = list(Alt)
#			checkAlt = temp[0] + temp[1] + temp[2]
#			#print str(int(checkAlt))
#			if int(checkAlt) < 35:
#				ser.write(':Qn#')
#				ser.write(':Qs#')
#				ser.write(':Qe#')
#				ser.write(':Qw#')
#				ser.write(':Q#')
#				print 'stopped movement'
#				#time.sleep(5)
#				#ser.write(':Mn#')
#				#print 'moving north slightly'
#				#time.sleep(5)
#				#ser.write(':Qn#')
#				#print 'stopped movement'
#				self.mountmoving = False
#
#			#print checkAlt
#			#print temp
#			return
#		else: return
		
#This meathod will avoid crashing the telescope with the mount	
	def too_low_check(self):
		ser.write(':GA#')
		Alt = ser.read(10)
		temp = list(Alt)
		checkAlt = temp[0] + temp[1] + temp[2]
		#print str(int(checkAlt))
		if int(checkAlt) < 10:
			print 'telescope too low, moving up, Altitude at'+Alt
			ser.write(':Qn#')
			ser.write(':Qs#')
			ser.write(':Qe#')
			ser.write(':Qw#')
			ser.write(':Q#')
			ser.write(':RM#')
			self.mountmoving= False
			time.sleep(5)
			ser.write(':Mn#')
			time.sleep(5)
			ser.write(':Qn#')
			print 'stopped movement'
			return
		else: return

