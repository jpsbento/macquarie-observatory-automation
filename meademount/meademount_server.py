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
ser = serial.Serial('/dev/ttyUSB0',9600, timeout = 1) #non blocking serial port, will wait
						      #for one second

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






	#****END of part B commands go here, don't understand currently****#

	#******START of part C commands to control telescope motion********#	

	def cmd_move(self,the_command):
		'''Starts motion 'north', 'south', 'east', or 'west' at the current rate.'''
		commands = str.split(the_command)
		if (len(commands) == 2):
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


	def cmd_fs(self,the_command):
		'''Halts the focuser motion.'''
		ser.write(':FQ#')
		return 'focuser motion stopped'

	def cmd_s(self,the_command):
		'''Stops all motion of the telescope.'''
		ser.write(':Q#')
		ser.write(':Qn#')
		ser.write(':Qs#')
		ser.write(':Qe#')
		ser.write(':Q#')
		return 'telescope movement stopped'




	#********************* Part d) Home Postion commands *******************#



	#******************* Part e) Library/Objects *********************#














	#********* Part f) Miscellaneous ***********#














	def cmd_getAlignmentMenuEntry(self,the_command): #NEW PROCESS VALUE
		'''Gets the Aligment Menu Entry, 0 1 or 2.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			temp = list(commands[1])
			if len(temp) == 1:
				if temp == '0' or temp == '1' or temp =='2':
					ser.write(':G'+temp+'#')
					return ser.read(1024)
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'
			



	def cmd_getCalanderDate(self,the_command):
		'''Gets the calander date.'''
		ser.write(':GC#')
		return ser.readline()


	def cmd_setCalanderDate(self,the_command): #need to check output
		'''Sets the calendar date. Please input in form: MM/DD/YY ie 08/25/89.'''
		commands = str.split(the_command)
		if len(commands) == 2:
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


	def cmd_getDistBars(self,the_command):
		'''Gets te distance 'bars' string.'''
		ser.write(':D#')
		return ser.readline()


	def cmd_setFan(self,the_command):
		'''Turns the fan on ('on') and off ('off') or returns the
		optical tube assembly temerature ('temp').'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == 'on':
				ser.write(':f+#')
				return 'fan is on'
			elif commands[1] == 'off':
				ser.write(':f-#')
				return 'fan is off'
			elif commands[1] == 'temp':
				ser.write(':fT#')
				return ser.read(1024)
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'











	def cmd_setFocus(self,the_command):
		''''out' starts focus out, 'in' starts focus in, 'stop' stops focus
		'fast' sets focus fast and 'slow' sets focus slow.'''
		commands = str.split(the_command)
		if len(commands) == 2:
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
			elif commands[1] == '1' or commands[1] == '2' or commands[1] == '3' or commands[1] == '4':
				ser.write(':F'+commands[1]+'#')
				return 'set focuser speed to '+commands[1]
			else:
				'ERROR, invalid input'
		else: return 'ERROR, invalid input length'


	def cmd_fieldOperation(self,the_command):
		'''Performs a FIELD operation returning a string containing
		the number of objects in the field and the object that is
		closest to the center of the field.'''
		ser.write(':Lf#')
		return ser.readline()


	def cmd_getFieldRadius(self,the_command):
		'''Gets the field radius of the FIELD operation.'''
		ser.write(':GF#')
		return ser.readline()

	def cmd_setFieldRadius(self,the_command):
		'''Sets the field radius of the FIELD operation. Please use
		form: NNN'''
		commands = str.split(the_command)
		if len(commands) == 2:
			radius = command[1]
			temp = list(radius)
			if len(temp) == 3:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit():
					ser.write(':SF '+radius+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, incorrect input length'

	def cmd_setFieldDerotator(self,the_command):
		'''Turns the field de-rotator on and off ('on' for on and
		'off' for off.. obviously.)'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == 'on':
				ser.write(':r+#')
				return 'field de-rotator on'
			elif commands[1] == 'off':
				ser.write(':r-#')
				return 'field de-rotator off'
			else:
				return 'ERROR, see help'
		else: return 'ERROR, invalid input length.'

	def cmd_getFindMin(self,the_command):
		'''Gets the current minimum quality for the FIND operation.'''
		ser.write(':Gq#')
		temp = ser.readline()
		if temp == 'SU#':
			return 'Super'
		elif temp == 'EX#':
			return 'Excellent'
		elif temp == 'VG#':
			return 'Very good'
		elif temp == 'GD#':
			return 'Good'
		elif temp == 'FR#':
			return 'fair'
		elif temp == 'PR#':
			return 'Poor'
		elif temp == 'VP#':
			return 'Very poor'
		else: return temp

	def cmd_nextFindMin(self,the_command):
		'''Steps to the next minumum quantity for the FIND operation.'''
		ser.write(':Sq#')
		return 'Stepped to next min quantity for FIND'



	def cmd_getFindType(self,the_command):
		'''Gets the "type" string for the FIND operation. A capital letter
		means that the corresponding type is selected while a lower case
		indicates it is not. G - galaxies, P - planetary nebulas,
		D - diffuse nebulas, C - Globular clusters, O - Open clusters.'''
		ser.write(':Gy#')
		return ser.readline()

	def cmd_setFindType(self,the_command):
		'''Sets the 'type' string for the FIND operation. Input should
		look like: GPDCO a capital indicates the corresponding type is
		selected while a lower case indicates it is not. G - galaxies,
		P - planetary nebulas, D - diffuse nebulas, C - Globular clusters,
		O - Open clusters.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			findtype = commands[1]
			temp = list(findtype)
			if len(temp) == 5:
				if (temp[0] == 'G' or temp[0] == 'g') and (temp[1] == 'P' or temp[1] == 'p') and (temp[2] == 'D' or temp[2] == 'd') and (temp[3] == 'C' or temp[3] == 'c') and (temp[4] == 'O' or temp[4] == 'o'):
					ser.write(':Sy '+findtype+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, incorrect input'
		else: return 'ERROR, incorrect input length'

	def cmd_startFind(self,the_command):
		'''Starts a FIND operation.'''
		ser.write(':LF#')
		return 'FIND operation started.'

	def cmd_getGMToffset(self,the_command):
		'''Gets the offset from Greenwich Mean Time.'''
		ser.write(':GG#')
		return ser.readline()
		

	def cmd_setGMToffset(self,the_command):
		'''Sets the offset from Greenwich Mean Time. Input as sHH ie '-05' Range:
		-24 to +24)'''
		commands = str.split(the_command)
		if (len(commands) ==2):
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

	def cmd_setGPS(self,the_command): #NEW
		''''on' to turn the GPS on, 'off' for off, 'NMEA' for the NMEA
		data stream to be turned on, 'power' to power up the GPS and
		update the system time from the GPS stream.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			temp = commands[1]
			if temp == 'on':
				ser.write(':g+#')
				return 'GPS turned on'
			elif temp == 'off':
				ser.write('g-#')
				return 'GPS turned off'
			elif temp == 'NMEA':
				ser.write(':gps#')
				return ser.read(1024)
			elif temp == 'power':
				ser.write(':gT#')
				return ser.read(1024)
		else: return 'ERROR, invalid input'



	def cmd_getLimit(self,the_command):
		'''Gets the current higher and lower limits.'''
		ser.write(':Gh#')
		higherlim = ser.readline()
		ser.write(':Go#')
		lowerlim = ser.readline()
		return 'Higher limit: '+str(higherlim)+', lower limit: '+lowerlim

	def cmd_setLimit(self,the_command):
		'''Sets the current limit. Please input limit inform: DD. To set the higher limit type:
		eg 'setLimit higher 50', to set the lower limit type: 'setLimit lower 20', to set both
		limits type 'setLimit 50 20' typing the higher limit first.'''
		commands = str.split(the_command)
		if len(commands) == 3:
			if (commands[1] == 'higher' or commands[1] == 'lower') and commands[2].isdigit():
				if commands[1] == 'higher':
					ser.write('Sh '+str(commands[2])+'#')
					return ser.readline()
				if commands[1] == 'lower':
					ser.write('So '+str(commands[2])+'#')
					return ser.readline()
			elif commands[1].isdigit() and commands[2].isdigit():
				ser.write('Sh '+str(commands[1])+'#')
				temp = ser.readline()
				ser.write('So '+str(commands[2])+'#')
				temp = temp+' '+ser.readline()
				return str(temp)
			else: return 'ERROR, invalid input'
		else: return 'ERROR invalid input'

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
		commands = str.split(the_command)
		if (len(commands) ==2):
			settime = commands[1]
			temp = list(settime)
			if (len(temp) = 8):
				if temp[2] == ':' and temp[5] == ':' and temp[0].isdigit() and temp[1].isdigit() and temp[3].isdigit() and temp[4].isdigit() and temp[6].isdigit() and temp[7].isdigit:
					ser.write(':SL '+settime+'#')
					return ser.readline()
				else: return 'ERROR, input in incorrect form'
			else: return 'ERROR input of incorrect length'
		else: return 'ERROR: Incorrect format, see help'

	def cmd_getMagLimit(self,the_command):
		'''Gets the brighter and the fainter magnitude limit for the FIND operation.'''
		ser.write(':Gb#')
		brighter = ser.readline()
		ser.write(':Gf#')
		fainter = ser.readline()
		return 'Brighter limit: '+str(brighter)+', fainter limit: '+str(fainter)

	def cmd_setMagLimit(self,the_command):
		'''Sets the magnitude limits for the FIND operation. Please input in format: 
		sMM.M Range 05.5 to 20.0. To set the bright magnitude limit type: 'setMagLim bright 15.2'
		to set the faint magnitude limit type: 'setMagLim faint 5.5'. To set both limits at the same
		time type: 'setMagLim 15.2 5.5' writing the brighter limit first.'''
		commands = str.split(the_command)
		if len(commands) == 3:
			if commands[1] == 'bright' or commands[1] == 'faint':
				lim = commands[2]
				temp = list(commands[2])
				if len(temp) < 5:
					if temp[len(temp)-2] == '.': del temp[len(temp)-2]
					for i in len(temp):
						if temp[i].isdigit():
						else: return 'ERROR, invalid input
					if commands[1] == 'bright':
						ser.write(':Sb '+lim+'#')
						return ser.readline()
					if commands[1] == 'faint':
						ser.write(':Sf '+lim+'#')
						return ser.readline()
			else:
				temp1 = list(commands[1])
				temp2 = list(commands[2])
				if len(temp2) < 5:
					if temp[len(temp2)-2] == '.': del temp[len(temp2)-2]
					for i in len(temp2):
						if temp2[i].isdigit():
						else: return 'ERROR, invalid input
				else: return 'ERROR invalid input'
				if len(temp1) < 5:
					if temp[len(temp1)-2] == '.': del temp[len(temp1)-2]
					for i in len(temp1):
						if temp1[i].isdigit():
						else: return 'ERROR, invalid input
				else: return 'ERROR, invalid input'
				ser.write(':Sb '+str(commands[1])+'#')
				buf = ser.readline()
				ser.write.(':Sf '+str(commands[2])+'#')
				buf = buf+' '+ser.readline()
				return buf
		else: return 'ERROR, invalid input'

	def cmd_setMaxSlewRate(self,the_command):
		'''Sets the max slew rate to "N" degrees per second
		where N is 2 through 4.'''
		commands = str.split(the_command)
		if (len(commands) ==2):
	
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

	def cmd_setMotionRate(self,the_command):
		'''Sets the motion rate to 'guide', 'center', 'find' or 'slew'.'''
		commands = str.split(the_command)
		if (len(commands) == 2):
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

	def cmd_findObject(self,the_command):
		'''To  the next object in a FIND sequence type 'findObject next'. To find the previous 
		object in a Find sequence tpye 'findObject previous'.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == 'next':
				ser.write(':LN#')
				return 'Finding next object in FIND sequence.'
			elif commands[1] == 'previous'
				ser.write('LB#')
				return 'Finding last object in FIND sequence.'
			else: return 'ERROR, invalid input.'
		else: return 'ERROR, invalid input'


	def cmd_setObjectAlt(self,the_command):
		'''Sets object altitude (for MA command). Please input in
		form: sDD*MM ie +10*06'''
		commands = str.split(the_command)
		if (len(commands) == 2):
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
		commands = str.split(the_command)
		if (len(commands) == 2):
			Az = commands[1]
			temp = list(Az)
			if len(temp) == 6:
				if temp[0].isdigit and temp[1].isdigit() and temp[2].isdigit() and temp[3] == '*' and temp[4].isdigit and temp[5].isdigit:
					ser.write(':Sa '+Az+'#')
					return ser.readline()
			else: return 'ERROR, incorrect input format'
		else: return 'ERROR, incorrect input length'

	def cmd_getObjectDec(self,the_command):
		'''Gets object declination.'''
		ser.write(':Gd#')
		return ser.readline()

	def cmd_setObjectDec(self,the_command):
		'''Sets object declination. Please input in form: sDD*MM ie +59.09'''
		commands = str.split(the_command)
		if (len(commands) == 2):
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

	def cmd_getObjectRA(self,the_command):
		'''Gets object right ascension.'''
		ser.write(':Gr#')
		return ser.readline()

	def cmd_setObjectRA(self,the_command):G
		'''Sets object right ascension. Please input in form:
		HH:MM:SS ie 09:08:02'''
		commands = str.split(the_commands)
		if (len(commands) == 2):
			RA = commands[1]
			temp = list(RA)
			if (len(temp) == 8):
				if temp[0].isdigit() and temp[1].isdigit() and temp[2] == ':' and temp[3].isdigit() and temp[4].isdigit() and temp[5] ==':' and temp[6].isdigit() and temp[7].isdigit():
					ser.write(':Sr '+RA+'#')
					return ser.readline()
				else: return 'ERROR, incorrect format'
			else: return 'ERROR, incorrect format'
		else: return 'ERROR, incorrect input length'

	def cmd_getObjectInfo(self,the_command):
		'''Gets the current object information.'''
		ser.write(':LI#')
		return ser.readline()

	def cmd_setObjectMessier(self,the_command):
		'''Sets the object to the Messier specified by the number.
		Please input in form: NNNN ie 1234'''
		commands = str.split(the_command)
		if len(commands) == 2:
			Messier = commands[1]
			temp = list(Messier)
			if len(temp) == 4:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit() and temp[3].isdigit():
					ser.write(':LM '+Messier+'#')
					return 'object set to Messier '+Messier
				else: return 'ERROR, invalid input'
			else: return 'ERROR invalid input'
		else: return 'ERROR, incorrect input length'

	def cmd_setObjectNGC(self,the_command):
		'''Sets the object to the NGC specified by the number. Object
		type returned depends ob which object type is selected with
		the setNGCType command. Please input in form: NNNN ie 1234'''
		commands = str.split(the_command)
		if len(commands) == 2:
			NGC = commands[1]
			temp = list(NGC)
			if len(temp) == 4:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit() and temp[3].isdigit():
					ser.write(':LC '+NGC+'#')
					return 'object set to NGC '+NGC
				else: return 'ERROR, invalid input'
			else: return 'ERROR invalid input'
		else: return 'ERROR, incorrect input length'

	def cmd_setObjectStar(self,the_command):
		'''Sets the object to the Star specified by the number. Planets
		are 'stars' 901-909. Object type returned depends on which
		object type has been selected with the setStarType command. Please input
		in form: NNNN ie 1234'''
		commands = str.split(the_command)
		if len(commands) == 2:
			star = commands[1]
			temp = list(star)
			if len(temp) == 4:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2].isdigit() and temp[3].isdigit():
					ser.write(':LS '+star+'#')
					return 'object set to star '+star
				else: return 'ERROR, invalid input'
			else: return 'ERROR invalid input'
		else: return 'ERROR, incorrect input length'


	def cmd_getSiderealTime(self,the_command):
		'''Returns the current sidereal time.'''
		ser.write(':GS#')
		return ser.readline()

	def cmd_setSiderealTime(self,the_command):
		'''Sets the sidereal time. Format should be HH:MM:SS'''
		commands = str.split(the_command)
		if (len(commands) ==2):

			settime = commands[1]
			temp = list(settime)
			if (len(temp) = 8):
				if temp[2] == ':' and temp[5] == ':' and temp[0].isdigit() and temp[1].isdigit() and temp[3].isdigit() and temp[4].isdigit() and temp[6].isdigit() and temp[7].isdigit:
					ser.write(':SS '+settime+'#')
					return ser.readline()
				else: return 'ERROR, input in incorrect form'
			else: return 'ERROR input of incorrect length'
		else: return 'ERROR: Incorrect format, see help'


	def cmd_getSiteName(self,the_command):
		'''Get SITE name. Put 1, 2, 3 or 4 for corresponding site name.'''
		commands = str.split(the_command)
		if len(commands) == 2:
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
		commands = str.split(the_command)
		if len(commands) == 3:
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

	def cmd_getSiteLatitude(self,the_command):
		'''Gets the latitude of the currently selected site.'''
		ser.write(':Gt#')
		return ser.readline()

	def cmd_setSiteLatitude(self,the_command):
		'''Sets the latitude of the currently selected site. Please input as
		sDD*MM ie '+45*59'. Range: -90*00 to +90.00'''
		commands = str.split(the_command)
		if len(commands) == 2:
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

	def cmd_getSiteLongitude(self,the_command):
		'''Gets the longitude of the currently selected site.'''
		ser.write(':Gg#')
		return ser.readline()

	def cmd_setSiteLongitude(self,the_command):
		'''Sets the longitude of the currently selected site. Please input
		in form: DDD*MM ie: 254*09. Range 000*00 to 359*59'''
		commands = str.split(the_command)
		if (len(commands) == 2):
			lon = commands[1]
			temp = list(lon)
			if (len(temp) == 6):
				if temp[0].isdigit() and temp[1].isdigit and temp[2].isdigit and temp[3] == '*' and temp[4].isdigit() and temp[5].isdigit():
					ser.write(':Sg '+lon+'#')
					return ser.readline()
				else: return 'ERROR, incorrect input format'
			else: return 'ERROR, incorrect input length'
		else: return "ERROR, incorrect input length"


	def cmd_getSizeLimit(self,the_command):
		'''Gets the size limit for the FIND operation, type 'large' for larger limit
		or 'small' for the smaller limit or for both input nothing.'''
		commands = str.split(the_command)
		if len(commands) == 1:
			ser.write(':Gl#')
			largelim = ser.readline()
			ser.write(':Gs#')
			smalllim = ser.readline()
			return 'large size limit: '+str(largelim)+', small size limit: '+str(smalllim)
		elif len(commands) == 2:
			if commands[1] == 'large' or commands[1] == 'Large':
				ser.write(':Gl#')
				return ser.readline()
			elif commands[1] == 'small' or commands[1] == 'Small':
				ser.write(':Gs#')
				return ser.readline()
			else: return 'ERROR, invalid input.'
		else: return 'ERROR invalid input'

	def cmd_setSizeLimit(self,the_command):
		'''Sets the larger size limit for the FIND operation. Please
		use form: NNN, range 000 to 200 Input ie 'setSizeLim large 160'
		or 'setSizeLim small 20' or to set both at the same time type
		'setSizeLim 20 160'. No decimals please.'''
		commands = str.split(the_command)
		if len(commands) == 3:
			if commands[1] == 'large' and commands[2].isdigit():
				ser.write('Sl '+commands[2]+'#')
				return ser.readline()
			elif commands[1] == 'small' and commands[2].isdigit():
				ser.write('Ss '+commands[2]+'#')
				return ser.readline()
			elif commands[1].isdigit() and commands[2].isdigit():
				ser.write('Sl '+commands[1]+'#')
				temp = ser.readline()
				ser.write('Ss '+commands[2]+'#')
				temp = temp+' '+ser.readline()
				return temp
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input'

	def cmd_getTrackFreq(self,the_command):
		'''Gets the current track 'frequency'.'''
		ser.write(':GT#')
		return ser.readline()

	def cmd_setTrackFreq(self,the_command):
		'''Sets the current track 'frequency'. Please input in
		form: TT.T ie 59.2, range 56.4 to 60.1'''
		commands = str.split(the_command)
		if len(commands) == 2:
			freq = commands[1]
			temp = list(freq)
			if len(temp) == 4:
				if temp[0].isdigit() and temp[1].isdigit() and temp[2] == '.' and temp[3].isdigit():
					ser.write('ST '+freq+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'


	def cmd_setNGCType(self,the_command):
		'''Sets the NGC object library type. 0 is the NGC library,
		1 is the IC library, and 2 is the UGC library. This operation
		is successful only if the user has a version of the software
		that includes the desired library.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			libtype = commands[1]
			temp = list(libtype)
			if len(temp) == 1 and temp[0].isdigit():
				if (int(temp[0] == 0) or (int(temp[0]) == 1) or (int(temp[0]) == 2):
					ser.write(':Lo '+libtype+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'

	def cmd_setReticleBrightness(self,the_command):
		'''Control reticle brightness. + increases, - decreases, or 
		0, 1, 2, 3 sets to one of the corresponding flashing modes.'''
		commands = str.split(the_command)
		if len(commands) == 2:
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





	def cmd_setStarType(self,the_command):
		'''Sets the STAR object library type. 0 is the STAR library
		1 is the SAO library, and 2 is the GCVS library. This operation
		is successful only if the user has a version of the software that
		includes the desired library.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			libtype = commands[1]
			temp = list(libtype)
			if len(temp) == 1 and temp[0].isdigit():
				if (int(temp[0] == 0) or (int(temp[0]) == 1) or (int(temp[0]) == 2):
					ser.write(':Ls '+libtype+'#')
					return ser.readline()
				else: return 'ERROR, invalid input'
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input length'

	def cmd_setTelescopeAlignment(self,the_command):
		'''Sets the telescopes alignment type to LAND, POLAR or ALTAZ.'''
		commands = str.split(the_commands)
		if len(commands) == 2:
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

	def cmd_changeManualFreq(self,the_command):
		'''+ increments manual rate by 0.1 Hz. - decrements
		manual rate by 0.1 Hz.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == '+':
				ser.write(':T+#')
				return 'incremented manual frequency by one tenth'
			elif commands[1] == '-':
				ser.write('T-#')
				return 'decremented manual frequency by one tenth'
			else:
				return 'Error, see help'
		else: return 'ERROR, invalid input length'

	def cmd_goHome(self,the_command):
		'''Slews the telescope to the home position.'''
		ser.write(':hP#')
		return 'slewing to home position'

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

	def cmd_highPrecisionToggle(self,the_command): #NEW
		'''Toggles high precision pointing. Enables/disables it. When
		high precision pointing is enabled scope will first allow the operator
		to center a nearby bright star before moving to the actual target.'''
		ser.write(':P#')
		return ser.read(1024)

	def cmd_sleep(self,the_command):
		'''Puts telescope to sleep. Powers off motors, encoders, displays and lights.'''
		ser.write(':hN#')
		return 'Telescope gone to sleep. *Zzzzzzz...*'

	def cmd_wakeUp(self,the_command):
		'''Wakes up sleeping telescope.'''
		ser.write(':hW#')
		return 'Telescope woken up. *Coffeeeeee...*'

	def cmd_slewAltAz(self,the_command):
		'''Slews telescope to objct atl-az coordinates(set with the
		Sa and Sz commands). This command only works in the LAND and 
		ALTAZ modes.'''
		ser.write(':MA#')
		return ser.readline()

	def cmd_slewCoord(self,the_command): #*** more than one output
		'''Slews telescope to current object coordinates. 0 returned if the
		telescope can complete the slew, 1 returned if object is below the
		horizon, 2 returned if the object is below the higher limit, 4
		returned if object is above the lower limit. If 1, 2 or 4 is returned
		a string containing an appropritate message is also returned.'''
		ser.write(':MS#')
		return ser.readline()


	def cmd_startTelescopeAutomaticAlignmentSequence(self,the_command): #NEW
		'''Starts the Telescope Automatic Alignment Sequence. Returns
		1 when complete (can take several minutes). 0 if scope not
		AzEl mounted or align fails.'''
		ser.write(':Aa#')
		return ser.read(1024)

	def cmd_switchManual(self,the_command):
		'''Switch to manual.'''
		ser.write(':TM#')
		return 'set to manual'

	def cmd_switchQuartz(self,the_command):
		'''Switch to quartz.'''
		ser.write(':TQ#')
		return 'set to quartz'

	def cmd_sync(self,the_command): #OUTPUT?
		'''Sync. Matches current telescope coordinates to the object
		coordinates and sends a string indicating which objects
		coordinates were used.'''
		ser.write(':CM#')
		return ser.readline()

	def cmd_syncSelenopgraphic(self,the_command): #NEW
		'''Syncs the telescope with the current Selenographic coordinates.'''
		ser.write(':CL#')
		return ser.read(1024)
		



	def cmd_?(self,the_command): #NEW
		'''Set help text cursor to the start of the first line. '+' for
		next line of help text and '-' for previous line of help text.'''
		commands = str.split(the_command)
		if len(commands) == 1:
			ser.write(':??#')
			return ser.read(1024)
		elif len(commands) == 2:
			if commands[1] == '+':
				ser.write(':?+#')
				return ser.read(1024)
			elif commands[1] == '-':
				ser.write('?-#')
				return ser.read(1024)
			else: return 'ERROR, invalid input'
		else: return 'ERROR, invalid input'


	

#************************* End of user commands ********************************#

	#definition to write to the serial port
	#this is where we give the telescope mount a command


	#definition to log the output, stores all data in a file
	def log(self,message):
		print(str(datetime.now())+" "+str(message)+'\n')

#Background task, will continually check the altitude of the mount
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
