#****************************************************************************#
#                     Code to control the meade mount                        #
#****************************************************************************#

import serial
import sys
import select
import string
from datetime import datetime
import time

#Open port connected to the mount
ser = serial.Serial('/dev/ttyUSB0',9600, timeout = 1)

print ser.portstr       #check which port was really used
#print ser.isOpen() #Bug test to check that the port is actually open

class MeademountServer:


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

	def cmd_setSiderealTime(self,the_command):
		'''Sets the sidereal time. Format should be HH:MM:SS'''
		if (len(the_command) ==2):
			commands = str.split(the_command)
			settime = commands[1]
			temp = list(settime)
			if (len(temp) = 8):
				if temp[2] == ':' and temp[5] == ':' and temp[0].isdigit() and temp[1].isdigit() and temp[3].isdigit() and temp[4].isdigit() and temp[6].isdigit() and temp[7].isdigit:
					ser.write(':SS '+settime+'#')
					return ser.readline()
				else: return 'ERROR, input in incorrect form'
			else: return 'ERROR input of incorrect length'
		else: return 'ERROR: Incorrect format, see help'
			

	def cmd_getLocalTime24(self,the_command):
		'''Gets the local time in 24 hour format'''
		ser.write(':GL#')
		return ser.readline()

	def cmd_getLocalTime12(self,the_command):
		'''Gets the local time in 12 hour format'''
		ser.write(':Ga#')
		return ser.readline()

	def cmd_setLocalTime(self,the_command):
		'''Sets the local time. Please input in form HH:MM:SS ie 17:05:30.
		NOTE parameter should always be in 24 hour format.'''
		if (len(the_command) ==2):
			commands = str.split(the_command)
			settime = commands[1]
			temp = list(settime)
			if (len(temp) = 8):
				if temp[2] == ':' and temp[5] == ':' and temp[0].isdigit() and temp[1].isdigit() and temp[3].isdigit() and temp[4].isdigit() and temp[6].isdigit() and temp[7].isdigit:
					ser.write(':SL '+settime+'#')
					return ser.readline()
				else: return 'ERROR, input in incorrect form'
			else: return 'ERROR input of incorrect length'
		else: return 'ERROR: Incorrect format, see help'

	def cmd_getCalanderDate(self,the_command):
		'''Gets the calander date.'''
		ser.write(':GC#')
		return ser.readline()


	def cmd_setCalanderDate(self,the_command): #need to check output
		'''Sets the calendar date. Please input in form: MM/DD/YY ie 08/25/89.'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			setdate = command[1]
			temp = list(setdate)
			if (len(temp) == 8):
				if temp[0].isdigit() and temp[1].isdigit() and temp[2] == '/' and temp[3].isdigit() and temp[4].isdigit() and temp[5] == '/' and temp[6].isdigit and temp[8].isdigit():
					ser.write(':SC '+setdate+'#')
					message = ser.readline()
					message = message + ser.readline()
					return message
				else: return "ERROR, incorrect input format"
			else: return "ERROR, incorrect input length."
		else: return "ERROR, incorrect input length"


	def cmd_getLatSite(self,the_command):
		'''Gets the latitude of the currently selected site.'''
		ser.write(':Gt#')
		return ser.readline()

	def cmd_setLatSite(self,the_command):
		'''Sets the latitude of the currently selected site. Please input as
		sDD*MM ie '+45*59'. Range: -90*00 to +90.00'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			lat = commands[1]
			temp = list(lat)
			if (len(temp) == 6):
				if temp[0] == '-' or temp[0] == '+':
					if temp[1].isdigit() and temp[2].isdigit and temp[3] == '.' and temp[4].isdigit and temp[5].isdigit():
						ser.write(':St '+lat+'#')
						return ser.readline()
					else: return 'ERROR incorrect input format'
				else: return 'ERROR incorrect input format'
			else: return 'ERROR incorrect input length'
		else: return 'ERROR, incorrect input length'

	def cmd_getLongSite(self,the_command):
		'''Gets the longitude of the currently selected site.'''
		ser.write(':Gg#')
		return ser.readline()

	def cmd_setLongSite(self,the_command):
		'''Sets the longitude of the currently selected site. Please input
		in form: DDD*MM ie: 254*09. Range 000*00 to 359*59'''
		if (len(the_command) == 2):
			commands = str.split(the_command)
			lon = commands[1]
			temp = list(lon)
			if (len(temp) == 6):
				if temp[0].isdigit() and temp[1].isdigit and temp[2].isdigit and temp[3] == '*' and temp[4].isdigit() and temp[5].isdigit():
					ser.write(':Sg '+lon+'#')
					return ser.readline()
				else: return 'ERROR, incorrect input format'
			else: return 'ERROR, incorrect input length'
		else: return "ERROR, incorrect input length"

	def cmd_getGMToffset(self,the_command):
		'''Gets the offset from Greenwich Mean Time.'''
		ser.write(':GG#')
		return ser.readline()
		

	def cmd_setGMToffset(self,the_command):
		'''Sets the offset from Greenwich Mean Time. Input as sHH ie '-05' Range:
		-24 to +24)'''
		if (len(the_command) ==2):
			commands = str.split(the_command)
			offset = commands[1]
			temp = list(offset)
			if (len(offset) == 3):
				if temp[0] == '-' or temp[0] == '+':
					if temp[1].isdigit() and temp[2].isdigit():
						ser.write(':SG '+offset'#')
						return ser.readline()
					else: return 'ERROR, incorrect input format'
				else: return 'ERROR, incorrect input format'
			else: return 'ERROR, incorrect input length'
		else: return 'ERROR, incorrect input length'

	#****END of part B commands go here, don't understand currently****#

	#******START of part C commands to control telescope motion********#	

	def cmd_move(self,the_command):
		'''Starts motion 'north', 'south', 'east', or 'west' at the current rate.'''
		if (len(the_command) == 2):
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
				return 'ERROR, invalid input see help'
		else: return 'ERROR, incorrect input length.'

	def cmd_slewcoord(self,the_command): #*** more than one output
		'''Slews telescope to current object coordinates. 0 returned if the
		telescope can complete the slew, 1 returned if object is below the
		horizon, 2 returned if the object is below the higher limit, 4
		returned if object is above the lower limit. If 1, 2 or 4 is returned
		a string containing an appropritate message is also returned.'''
		ser.write(':MS#')
		return ser.readline()

	def cmd_slewaltaz(self,the_command):
		'''Slews telescope to objct atl-az coordinates(set with the
		Sa and Sz commands). This command only works in the LAND and 
		ALTAZ modes.'''
		ser.write(':MA#')
		return ser.readline()
		

	def cmd_s(self,the_command):
		'''Stops all motion.'''
		ser.write(':Q#')
		ser.write(':Qn#')
		ser.write(':Qs#')
		ser.write(':Qe#')
		ser.write(':Q#')
		return 'telescope movement stopped'

	def cmd_setMotionRate(self,the_command):
		'''Sets the motion rate to 'guide', 'center', 'find' or 'slew'.'''
		if (len(the_command) == 2):
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
				return 'Error, see help'
		else: return 'ERROR, invalid input.'

	def cmd_setMaxSlewRate(self,the_command):
		'''Sets the max slew rate to "N" degrees per second
		where N is 2 through 4.'''
		if (len(the_command) ==2):
			commands = str.split(the_command)
			if int(commands[1]):
				if int(commands[1]) < 2 or int(commands[1] > 4):
					return 'ERROR, value not in range'
				else:
					N = int(commands[1])
					ser.write(':Sw '+N+'#')
					return ser.readline()
			else:
				return 'Error, did not put input number'
		else: return 'ERROR, incorrect input length'

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

	def cmd_homeStatus(self,the_command):
		'''Returns the home status: 0 if home search failed or not
		yet attempted, 1 if home position found, or 2 if a home
		search is in progress.'''
		ser.write(':h?#')
		value = ser.readline()
		if value == '0':
			return 'home search failed or not yet attempted'
		elif value == '1':
			return 'home position found'
		elif value == '2'
			return 'home search in progress'
		else: return value

	#******************* Part e) Library/Objects *********************#

	def cmd_getObjectRA(self,the_command):
		'''Gets object right ascension.'''
		ser.write(':Gr#')
		return ser.readline()

	def cmd_setObjectRA(self,the_command):
		'''Sets object right ascension. Please input in form:
		HH:MM:SS ie 09:08:02'''
		if (len(the_command) == 2):
			commands = str.split(the_commands)
			RA = commands[1]
			temp = list(RA)
			if (len(temp) == 8):
				if temp[0].isdigit() and temp[1].isdigit() and temp[2] == ':' and temp[3].isdigit() and temp[4].isdigit() and temp[5] ==':' and temp[6].isdigit() and temp[7].isdigit():
					ser.write(':Sr '+RA+'#')
					return ser.readline()
				else: return 'ERROR, incorrect format'
			else: return 'ERROR, incorrect format'
		else: return 'ERROR, incorrect input length'

	def cmd_getObjectDec(self,the_command):
		'''Gets object declination.'''
		ser.write(':Gd#')
		return ser.readline()

	def cmd_setObjectDec(self,the_command):
		'''Sets object declination. Please input in form: sDD*MM ie +59.09'''
		if (len(the_command) == 2):
			commands = str.split(the_command)
			DEC = commands[1]
			temp = list(DEC)
			if (len(temp) == 6):
				if temp[0] == '+' or temp[0] == '-':
					if temp[1].isdigit() and temp[2].isdigit() and temp[3] == '*' and temp[4].isdigit() and temp[5].isdigit():
						ser.write(':Sa '+DEC+'#')
						return ser.readline()
					else: return 'ERROR, incorrect input form'
				else: return 'ERROR incorrect input format'
			else: return 'ERROR, incorrect input length'
		else: return 'ERROR, incorrect input length'

	def cmd_setObjectAlt(self,the_command):
		'''Sets object altitude (for MA command). Please input in
		form: sDD*MM ie +10*06'''
		if (len(the_command) == 2):
			commands = str.split(the_command)
			Alt = commands[1]
			temp = list(Alt)
			if len(temp) == 6:
				if temp[0] == '+' or temp[0] == '-':
					if temp[1].isdigit() and temp[2].isdigit() and temp[3] == '*' and temp[4].isdigit and temp[5].isdigit:
						ser.write(':Sa '+Alt+'#')
						return ser.readline()
				else: return 'ERROR, incorrect input format'
			else: return 'ERROR, incorrect input format'
		else: return 'ERROR, incorrect input length'

	def cmd_setObjectAz(self,the_command):
		'''Sets object azimuth (for MA command). Please input in
		form: DDD*MM ie 258*09'''
		if (len(the_command) == 2):
			commands = str.split(the_command)
			Az = commands[1]
			temp = list(Az)
			if len(temp) == 6:
				if temp[0].isdigit and temp[1].isdigit() and temp[2].isdigit() and temp[3] == '*' and temp[4].isdigit and temp[5].isdigit:
					ser.write(':Sa '+Az+'#')
					return ser.readline()
			else: return 'ERROR, incorrect input format'
		else: return 'ERROR, incorrect input length'



	def cmd_sync(self,the_command): #OUTPUT?
		'''Sync. Matches current telescope coordinates to the object
		coordinates and sends a string indicating which objects
		coordinates were used.'''
		ser.write(':CM#')
		return ser.readline()
		

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
		if len(the_command) == 2:
			commands = str.split(the_command)
			findtype = commands[1]
			temp = list(findtype)
			if len(temp) == 5:
				if (temp[0] == 'G' or temp[0] == 'g') and (temp[1] == 'P' or temp[1] == 'p') and (temp[2] == 'D' or temp[2] == 'd') and (temp[3] == 'C' or temp[3] == 'c') and (temp[4] == 'O' or temp[4] == 'o'):
					ser.write(':Sy '+findtype+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, incorrect input'
		else: return 'ERROR, incorrect input length'

	def cmd_getFindMin(self,the_command):
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
		if len(the_command) == 2:
			commands = str.split(the_command)
			lim = commands[1]
			temp = list(lim)
			if len(temp) == 2:
				if temp[0].isdigit() and temp[1].isdigit():
					ser.write(':Sh '+lim+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR incorrect input length'

	def cmd_getLowerLim(self,the_command):
		'''Gets the current 'lower' limit.'''
		ser.write(':Go#')
		return ser.readline()

	def cmd_setLowerLim(self,the_command):
		'''Sets the current 'lower limit. Please use
		form" DD'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			lim = commands[1]
			temp = list(lim)
			if len(temp) == 2:
				if temp[0].isdigit() and temp[1].isdigit():
					ser.write(':Sh '+lim+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR incorrect input length'

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
		Please input in format: sMM.M Range 05.5 to 20.0. ie: 02.5'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			lim = command[1]
			temp = list(lim)
			if len(temp) == 4:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2] == '.' and temp[3].isdigit():
					ser.write(':Sb '+lim+'#')
					return ser.readline()
				else: return 'ERROR, incorrect input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, incorrect input length'

	def cmd_setFaintMagLim(self,the_command):
		'''Sets the fainter magnitude limit for the FIND operation.
		Please input in format: sMM.M Range 05.5 to 20.0. ie 02.5'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			lim = command[1]
			temp = list(lim)
			if len(temp) == 4:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2] == '.' and temp[3].isdigit():
					ser.write(':Sb '+lim+'#')
					return ser.readline()
				else: return 'ERROR, incorrect input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, incorrect input length'

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
		use form: NNN, range 000 to 200'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			lim = commands[1]
			temp = list(lim)
			if len(temp) == 3:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit():
					ser.write(':Sl '+lim+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, incorrect input length'

	def cmd_setSmallSizeLim(self,the_command):
		'''Sets the smaller size limit for the FIND operation. Please
		use form: NNN, range 000 to 200'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			lim = commands[1]
			temp = list(lim)
			if len(temp) == 3:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit():
					ser.write(':Sl '+lim+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, incorrect input length'

	def cmd_getFieldRadius(self,the_command):
		'''Gets the field radius of the FIELD operation.'''
		ser.write(':GF#')
		return ser.readline()

	def cmd_setFieldRadius(self,the_command):
		'''Sets the field radius of the FIELD operation. Please use
		form: NNN'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			radius = command[1]
			temp = list(radius)
			if len(temp) == 3:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit():
					ser.write(':SF '+radius+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, incorrect input length'

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

	def cmd_setObjNGC(self,the_command):
		'''Sets the object to the NGC specified by the number. Object
		type returned depends ob which object type is selected with
		the setNGCType command. Please input in form: NNNN ie 1234'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			NGC = commands[1]
			temp = list(NGC)
			if len(temp) == 4:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit() and temp[3].isdigit():
					ser.write(':LC '+NGC+'#')
					return 'object set to NGC '+NGC
				else: return 'ERROR, invalid input'
			else: return 'ERROR invalid input'
		else: return 'ERROR, incorrect input length'

	def cmd_setObjMessier(self,the_command):
		'''Sets the object to the Messier specified by the number.
		Please input in form: NNNN ie 1234'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			Messier = commands[1]
			temp = list(Messier)
			if len(temp) == 4:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit() and temp[3].isdigit():
					ser.write(':LM '+Messier+'#')
					return 'object set to Messier '+Messier
				else: return 'ERROR, invalid input'
			else: return 'ERROR invalid input'
		else: return 'ERROR, incorrect input length'

	def cmd_setObjStar(self,the_command):
		'''Sets the object to the Star specified by the number. Planets
		are 'stars' 901-909. Object type returned depends on which
		object type has been selected with the setStarType command. Please input
		in form: NNNN ie 1234'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			star = commands[1]
			temp = list(star)
			if len(temp) == 4:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit() and temp[3].isdigit():
					ser.write(':LS '+star+'#')
					return 'object set to star '+star
				else: return 'ERROR, invalid input'
			else: return 'ERROR invalid input'
		else: return 'ERROR, incorrect input length'

	def cmd_objectInfo(self,the_command):
		'''Gets the current object information.'''
		ser.write(':LI#')
		return ser.readline()

	def cmd_setNGCType(self,the_command):
		'''Sets the NGC object library type. 0 is the NGC library,
		1 is the IC library, and 2 is the UGC library. This operation
		is successful only if the user has a version of the software
		that includes the desired library.'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			libtype = commands[1]
			temp = list(libtype)
			if len(temp) == 1 and temp[0].isdigit():
				if (int(temp[0] == 0) or (int(temp[0]) == 1) or (int(temp[0]) == 2):
					ser.write(':Lo '+libtype+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'

	def cmd_setStarType(self,the_command):
		'''Sets the STAR object library type. 0 is the STAR library
		1 is the SAO library, and 2 is the GCVS library. This operation
		is successful only if the user has a version of the software that
		includes the desired library.'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			libtype = commands[1]
			temp = list(libtype)
			if len(temp) == 1 and temp[0].isdigit():
				if (int(temp[0] == 0) or (int(temp[0]) == 1) or (int(temp[0]) == 2):
					ser.write(':Ls '+libtype+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'

	#********* Part f) Miscellaneous ***********#

	def cmd_reticleBrightness(self,the_command):
		'''Control reticle brightness. + increases, - decreases, or 
		0, 1, 2, 3 sets to one of the corresponding flashing modes.'''
		if len(the_command) == 2:
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
				return 'ERROR, incorrect input, see help'
		else: return 'ERROR, invalid input length'

	def cmd_focus(self,the_command):
		''''out' starts focus out, 'in' starts focus in, 'stop' stops focus
		'fast' sets focus fast and 'slow' sets focus slow.'''
		if len(the_command) == 2:
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
				'ERROR, invalid input'
		else: return 'ERROR, invalid input length'

	def cmd_getSiteName(self,the_command):
		'''Get SITE name. Put 1, 2, 3 or 4 for corresponding site name.'''
		if len(the_command) == 2:
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
				return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'

	def cmd_setSiteName(self,the_command):
		'''Sets SITE name. Please input form: N XYZ where N is 
		site number and XYZ is site name.'''
		if len(the_command) == 3:
			commands = str.split(the_command)
			name = commands[2]
			temp = list(name)
			if len(temp) == 3:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit():
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
					return 'ERROR, invalid input, see help'
				else: return 'ERROR, invalid input format'
			else: return 'ERROR, invalid input format'
		else: return 'ERROR, invalid input length'

	def cmd_getTrackFreq(self,the_command):
		'''Gets the current track 'frequency'.'''
		ser.write(':GT#')
		return ser.readline()

	def cmd_setTrackFreq(self,the_command):
		'''Sets the current track 'frequency'. Please input in
		form: TT.T ie 59.2, range 56.4 to 60.1'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			freq = commands[1]
			temp = list(freq)
			if len(temp) == 4:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2] == '.' and temp[3].isdigit():
					ser.write('ST '+freq+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'

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
		if len(the_command) == 2:
			commands = str.split(the_command)
			if commands[1] == '+':
				ser.write(':T+#')
				return 'incremented manual frequency by one tenth'
			elif commands[1] == '-':
				ser.write('T-#')
				return 'decremented manual frequency by one tenth'
			else:
				return 'Error, see help'
		else: return 'ERROR, invalid input length'

	def cmd_getDistBars(self,the_command):
		'''Gets te distance 'bars' string.'''
		ser.write(':D#')
		return ser.readline()

	def cmd_setTelescopeAlignment(self,the_command):
		'''Sets the telescopes alignment type to LAND, POLAR or ALTAZ.'''
		if len(the_command) == 2:
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
				return 'ERROR, see help'
		else: return 'ERROR, invalid input length'

	def cmd_fieldDerotator(self,the_command):
		'''Turns the field de-rotator on and off ('on' for on and
		'off' for off.. obviously.)'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			if commands[1] == 'on':
				ser.write(':r+#')
				return 'field de-rotator on'
			elif commands[1] == 'off':
				ser.write(':r-#')
				return 'field de-rotator off'
			else:
				return 'ERROR, see help'
		else: return 'ERROR, invalid input length.'

	def cmd_fan(self,the_command):
		'''Turns the fan on ('on') and off ('off').'''
		if len(the_command) == 2:
			commands = str.split(the_command)
			if commands[1] == 'on':
				ser.write(':f+#')
				return 'fan is on'
			elif commands[1] == 'off':
				ser.write(':f-#')
				return 'fan is off'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'


#************************* End of user commands ********************************#

	#definition to write to the serial port
	#this is where we give the telescope mount a command


	#definition to log the output, stores all data in a file
	def log(self,message):
		print(str(datetime.now())+" "+str(message)+'\n')

#Background tast, will continually check the altitude of the mount
# to insure no crashes take place.
	def too_low_check(self):
		ser.write(':GA#')
		Alt = ser.read(10)
		temp = list(Alt)
		if len(temp) > 2:
			checkAlt = temp[0] + temp[1] + temp[2]
			if int(checkAlt) < 10:
				print 'telescope too low, moving up. Altitude at '+Alt
				ser.write(':Q#')
				ser.write(':Qn#')
				ser.write(':Qs#')
				ser.write(':Qe#')
				ser.write(':Q#')
				ser.write(':RM#')
				time.sleep(5)
				ser.write(':Mn#')
				time.sleep(5)
				ser.write(':Qn#')
				return 'stopped movement'
			else: return
		else: return 'ERROR reading Alitude'
