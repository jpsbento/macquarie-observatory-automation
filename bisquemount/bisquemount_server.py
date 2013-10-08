# coding: utf-8
#*************************************************************************#
#                    Code to control the Bisque mount                     #
#*************************************************************************#

import sys
import string
import select
import socket
from datetime import datetime
import time
import serial
import binascii, ast

#Open port 0 at "9600,8,N,1", timeout of 5 seconds
#Open port connected to the mount
ser = serial.Serial('/dev/ttyUSB1',9600, timeout = 100) # non blocking serial port, will wait
						        # for ten seconds find the address
print ser.portstr       # check which port was rea3lly used
                        # we open a serial port to talk to the focuser

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # This client_socket is to communicate with the windows machine
client_socket.connect(("10.238.16.10",3040))			  # running 'TheSkyX'. If it doesn't receive a response after 50 mins
client_socket.settimeout(3000)					  # I need to make it do something

class BisqueMountServer:

	dome_slewing_enabled = 0 #can enable disable automatic dome slewing

	#parameters to do with the focus adjustment
	#Current amount by which the focusser should move
	move_focus_amount = 200
	#current value of Half-flux Diameter (HFD)
	sharp_value = 0
	#Boolean that is activated when the focuser should make an adjustment. This triggers the adjustFocus function when True.
	focussing=False
	
#**************************************SERIAL COMMANDS FOR THE FOCUSER **************************************#
#The focuser echos the command back to the user.

	def cmd_focusGoToPosition(self,the_command):
		'''Tell the focuser to go to a position. The position is specified in counts with a maximum
		of 4 digits, ie: 8023'''
		commands = str.split(the_command)
		if len(commands) == 2 and commands[1].isdigit():
			positioncommand = self.convertnumberforfocuser(commands[1])
			ser.write('g')
			ser.write(str(positioncommand[0]))
			ser.write(str(positioncommand[1]))
			echo = ser.read(1) #then communicates again when command is either completed or terminated
			print echo
			focusresponse = ''
			#wait for a response
			while focusresponse == '':focusresponse = str(ser.read(1))
			if focusresponse == 'c': return 'Command complete'
			elif focusresponse == 'r': return 'Motor or encoder not working, operation terminated.'
			else: return focusresponse+' ERROR, not sure what.'+str(ord(focusresponse))
		else: return 'ERROR, invalid input'


	def cmd_focusReadPosition(self,the_command):
		'''This will read the position of the focuser.'''
		ser.write('p')
		echo = ser.read(1)
		#responsetemp = self.recvamount(2)
		#responselist = list(responsetemp)
		focusresponse = ser.read(2) #should block till we get our two bytes
		#for something in responselist:       #hopefully taking the number values of all the characters
			#response += ord(something)   #the focuser gives as and adding them gives us the position
		#return str(response)		     #although I'm not sure it'll be that simples
		return str(self.convertfocusoutput(focusresponse[0], focusresponse[1]))

	def cmd_focusReadStateRegister(self,the_command):
		'''After the focus controller receives the command byte, it will echo
		the command character back to the host, followed by the eight bit 
		status byte. All bits are active high; a 1 indicates the condition 
		is true, a 0 indicates it is false. Reading the device status resets
		the error conditions (bits 1 through 3 only).'''
		ser.write('t')
		echo = ser.read(1) #should set size=len(echo), where you figure out len(echo) from a trial attempt
		response = ''
		while response == '': response = ser.read()
		#import code; code.interact(local=locals())
		message = ''
		r0 = ord(response[0])
		# Lets assume that bit 7 is bit 0, and bit 0 is bit 7.
		if ((r0 >> 1) & 1): message += 'Focuser at maximum travel position. '
		if ((r0 >> 6) & 1): message += 'Focuser at zero position. '
		if ((r0 >> 4) & 1): message += 'Motor/encoder error. '
		if ((r0 >> 3) & 1): message += 'Serial reciver overrun error. '
		if ((r0 >> 2) & 1): message += 'Serial reciver framing error. '
		return message

	def cmd_focusReadIdentityRegister(self,the_command): #What does this actually do?
		'''This command will allow the host to read the focus controller identify byte.
		This is a one byte command. The command character is ‘b’. After the focus
		controller receives the command byte, it will echo the command character back to
		the host, followed by the eight bit identify byte. This identify byte is a lower
		case ‘j’ (6Ah).'''
		ser.write('b')
		echo = ser.read(1)
		return ser.read(1) # should be the 8-bit identity byte: 'j', which testing shows it is

	def cmd_focusWriteMaxTravelRegister(self,the_command): #NEED INPUT
		'''This command will allow the host to write the focus controller maximum 
		travel register. This command is used by the host PC to configure the focuser
		controller, based on the focuser characteristics defined by the user. When this
		command is received, all stored data in the EEPROM is updated. This is a three 
		byte command. The command character is ‘w’. This is followed by the desired 
		sixteen bit maximum count value, sent as two bytes, most significant byte first.'''
		commands = str.split(the_command)
		if len(commands) == 2 and commands[1].isdigit(): #**********************************
			ser.write('w')
			focusercommand = self.convertnumberforfocuser(commands[1])
			ser.write(focusercommand[0])
			ser.write(focusercommand[1])
			echo = ser.read(1) #echos the command back to us
			return echo
		else: return 'ERROR, invalid input'

	def cmd_focusWritePositionSpeedRegister(self,the_command): #NEED INPUT
		'''This command will allow the host to write the focus controller position speed
		register. This command is used by the host PC to configure the focuser controller,
		based on the focuser characteristics defined by the user. Position speed is used
		to move the focuser slowly when it is close to the desired Go To position. This is
		a three byte command. The command character is ‘d’. This is followed by the
		desired sixteen bit speed value, sent as two bytes, most significant byte first.'''
		commands = str.split(the_command)
		if len(commands) == 2 and commands[1].isdigit():
			ser.write('d')
			focusercommand = self.convertnumberforfocuser(commands[1]) 
			ser.write(focusercommand[0])
			ser.write(focusercommand[1])
			echo = ser.read(1) #echos the command back to us
			return 'echo'
		else: return 'ERROR, invalid input'

	def cmd_focusWriteMoveSpeedRegister(self,the_command): #NEED INPUT
		'''This command will allow the host to write the focus controller move speed
		register. This command is used by the host PC to configure the focuser controller,
		based on the focuser characteristics defined by the user. Move speed is used to
		move the focuser slowly when a Move In or Move Out command is issued. It is also
		the speed the focuser moves when a pushbutton is pressed. This is a three byte
		command. The command character is ‘e’. This is followed by the desired sixteen bit
		speed value, sent as two bytes, most significant byte first.'''
		commands = str.split(the_command)
		if len(commands) == 2 and commands[1].isdigit():
			ser.write('e')
			focusercommand = self.convertnumberforfocuser(commands[1]) #
			ser.write(focusercommand[0])
			ser.write(focusercommand[1])
			echo = ser.read(1) #the focuser echos the command back to us
			return echo

	def cmd_focusWriteShuttleSpeedRegister(self,the_command): #NEED INPUT
		'''This command will allow the host to write the focus controller shuttle speed
 		register. This command is used by the host PC to configure the focuser controller,
		based on the focuser characteristics defined by the user. Shuttle speed is used to
		move the focuser rapidly during a Go To Position command, when far from the desired
		position. It is also the speed the focuser moves when a pushbutton is pressed for
		more than three seconds, and the motor speeds up. This is a three byte command. The
		command character is ‘f’. This is followed by the desired sixteen bit speed value,
		sent as two bytes, most significant byte first.'''
		commands = str.split(the_command)
		if len(commands) == 2 and commands[1].isdigit():
			ser.write('f')
			focuscommand = self.convertnumberforfocuser(commands[1])
			ser.write(focuscommand[0])
			ser.write(focuscommand[1])
			echo = ser.read(1) #echos the command back to us
			return echo

	def cmd_focusSetZeroPosition(self,the_command):
		'''This command will set the Position register value to zero, regardless of the
		actual drawtube position. The position value stored in the EEPROM is also
		updated.'''
		ser.write('z')
		return ser.read(1) #echo echo echo

	def cmd_focusMove(self,the_command):
		'''Tell the focuser to move in or out. Increments by 0.01". Note that if the push
		buttons on the manual control pad for the focuser are pushed while this command is in
		operation, motion will be terminated.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			if commands[1] == 'in':
				ser.write('i')
				message = ser.read(1)
				if message[-1] == 'r': return 'Motor or encoder not working'
				else: return message
			elif commands[1] == 'out':
				ser.write('o')
				message = ser.read(1)
				if message[-1] == 'r': return 'Motor or encoder not working'
				else: return message
			else: return 'ERROR invalid input'
		else: return 'ERROR invalid input'

	def cmd_fs(self,the_command):
		'''Stops focuser motion.'''
		ser.write('s')
		return ser.read(1)

	def cmd_focusTelescope(self,the_command):
		'''function that activates the focus adjustment loop function (see below). 
		Is essentially sets the global variable self.focussing to true, which should 
		trigger the contents of the function adjustFocus.'''
		commands = str.split(the_command)
		if len(commands)!=2: return 'ERROR:, this function just needs the half-flux diameter value as input'
		try: self.HFD=float(commands[1])
		except Exception: return 'HFD value must be a float.'
		self.focussing=True
		return 'Focussing'
		
	
	def cmd_focusSetAmount(self,the_command):
		'''function to reset the amount by which the focuser is moving. 
		This can be used by the uber server user to reset the focussing amount when it needs to be more than 1.'''
		commands = str.split(the_command)
		if len(commands)!=2: return 'ERROR: this function just needs the focussing amount in counts'
		try: self.move_focus_amount=int(commands[1])
		except Exception: return 'Could not convert focus amount into integer'
		return 'New focus amount set'
		
	def adjustFocus(self):
		'''routine to adjust the focuser position based on a new half-flux diameter measurement. This is the actual function that adjusts the focus.
		This function is here to ensure that the focussing routine runs independently of the uber server.'''
		if self.focussing:
			focusposition = self.cmd_focusReadPosition("focusReadPosition")     #read current focus position
			try: focusposition = int(focusposition)
			except Exception: return 'ERROR: can not convert focus position to integer'
			print focusposition, self.HFD, self.move_focus_amount              #print the values of the focuser position, HFD and amount of adjustment for monitoring purposes.
			#if the HFD has increased since last time, reverse the direction of motion and half the amount. Otherwise, just leave as is and then move the focuser. 
			if self.HFD >= self.sharp_value: 
				self.move_focus_amount = int((self.move_focus_amount*-1)/2)
				if self.move_focus_amount==0: self.move_focus_amount=1
			self.cmd_focusGoToPosition("focusGoToPosition "+str(int(focusposition)+self.move_focus_amount))
			self.sharp_value=self.HFD
			self.focussing=False


#************************************** COMMANDS TO TALK TO MOUNT **************************************#
		

	def cmd_find(self,the_command):
		'''Will find an object in TheSky's Star chart and return data. It will spill out all the info on the target in a string.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			obj = commands[1]
			linestoreplace = ['sky6StarChart.Find("object");\r\n']
			newlines = ['sky6StarChart.Find("'+obj+'");\r\n']
			if self.editscript('Find.template', 'Find.js', linestoreplace,newlines):
				script = self.readscript('Find.js')
				client_socket.send(script)
				return self.messages()
			else: return 'ERROR with files'
		else: return 'ERROR, invalid input.'

	def cmd_objInfo(self,the_command):
		'''Will return a string containing a dictionary with the current target's info, in a more manageable manner'''
		commands = str.split(the_command)
		if len(commands)>1: return 'This function does not take arguments'
		try:
			script = self.readscript('ObjInfo.js')
			client_socket.send(script)
			dummy=self.messages()
			dum=dummy.split(';')
		except Exception: return 'Something went wrong with reading the output from the SkyX regarding the object information'
		#This is a list of all the parameters that a target can possibly have.
		params=[ 'NAME1', 'NAME2', 'NAME3', 'NAME4', 'NAME5', 'NAME6', 'NAME7', 'NAME8', 'NAME9', 'NAME10', 'CATALOG_ID', 'ALL_INFO', 'OBJ_TYPE', 'RISE_SET_INFO', 'STAR_SPECTRAL', 'STAR_BAYER_FLAMSTEED', 'SATELLITE_NAME', 'SATELLITE_TLE1', 'SATELLITE_TLE2', 'SOURCE_CATALOG', 'DB_FIELD_0', 'DB_FIELD_1', 'DB_FIELD_2', 'DB_FIELD_3', 'DB_FIELD_4', 'DB_FIELD_5', 'DB_FIELD_6', 'DB_FIELD_7', 'DB_FIELD_8', 'DB_FIELD_9', 'DB_FIELD_10', 'DB_FIELD_11', 'DB_FIELD_12', 'DB_FIELD_13', 'DB_FIELD_14', 'DB_FIELD_15', 'TEXT_LINE', 'DATE', 'TIME', 'OBSERVING_NOTES', 'CATID', 'OBJECTTYPE', 'STAR_ID', 'STAR_GSC_BLOCK', 'STAR_GSC_NUM', 'INDEX', 'NGC_IC_NEG_ID', 'SKIP_INDEX', 'NST_FIELD_CNT', 'PERINFO_TEXTPOSN', 'ACTIVE', 'SATELLITE_ECLIPSED', 'SATELLITE_IS_EXT', 'CATALOG', 'RA_NOW', 'DEC_NOW', 'RA_2000', 'DEC_2000', 'AZM', 'ALT', 'MAJ_AXIS_MINS', 'MIN_AXIS_MINS', 'EARTH_DIST_KM', 'SUN_DIST_AU', 'PA', 'MAG', 'PHASE_PERC', 'RISE_TIME', 'TRANSIT_TIME', 'SET_TIME', 'HA_HOURS', 'AIR_MASS', 'STAR_MAGB', 'STAR_MAGV', 'STAR_MAGR', 'SCREEN_X', 'SCREEN_Y', 'RA_RATE_ASPERSEC', 'DEC_RATE_ASPERSEC', 'ALT_RATE_ASPERSEC', 'AZIM_RATE_ASPERSEC', 'AZIM_RISE_DEGS', 'AZIM_SET_DEGS', 'MPL_ACTIVE', 'MPL_EPOCH_M', 'MPL_EPOCH_D', 'MPL_EPOCH_Y', 'MPL_MA', 'MPL_ECCENT', 'MPL_SEMIMAJOR', 'MPL_INCLIN', 'MPL_LAN', 'MPL_LONG_PERI', 'MPL_ECLIP', 'MPL_MAGPARM1', 'MPL_MAGPARM2', 'COMET_PERIH_M', 'COMET_PERIH_D', 'COMET_PERIH_Y', 'COMET_ECCENT', 'COMET_PERIDIST', 'COMET_INCLIN', 'COMET_LAN', 'COMET_LONG_PERI', 'COMET_ECLIP', 'COMET_MAGPARM1', 'COMET_MAGPARM2', 'PLANET_SHELIO_L', 'PLANET_SHELIO_B', 'PLANET_SHELIO_R', 'PLANET_SGEO_L', 'PLANET_SGEO_B', 'PLANET_SGEO_R', 'PLANET_SGEOMEAN_L', 'PLANET_SGEOMEAN_B', 'PLANET_SGEOMEAN_R', 'PLANET_TRUE_RA', 'PLANET_TRUE_DEC', 'PLANET_ALTWREFRACT', 'PLANET_APPMAG', 'PLANET_APPANGDIAM', 'MOON_TRUE_ECLIP_L', 'MOON_TRUE_ECLIP_B', 'MOON_TRUE_ECLIP_R', 'MOON_PARALLAX', 'MOON_ANGDIAM', 'MOON_DIST_KM', 'MOON_TRUE_EQ_RA', 'MOON_TRUE_EQ_DEC', 'MOON_TOPO_ANG_DIAM', 'MOON_ALT_WREFRACT', 'MOON_TOTAL_LIBR_L', 'MOON_TOTAL_LIBR_B', 'MOON_OPTICAL_LIBR_L', 'MOON_OPTICAL_LIBR_B', 'MOON_PHYS_LIBR_L', 'MOON_PHYS_LIBR_B', 'MOON_POS_ANGLE', 'MOON_PHASE_ANGLE', 'MOON_PABL', 'SUN_POS_ANGLE', 'SUN_HELIO_LONG', 'SUN_HELIO_LAT', 'DECL_SUN', 'DECL_EARTH', 'POLAR_DIAM', 'LCM_I', 'LCM_II', 'MARS_DEFECT_ILLUM', 'JUPITER_CRCT_PHASE', 'SATURN_ARING_AXIS', 'SATURN_BRING_AXIS', 'SAT_JD', 'SAT_LAT', 'SAT_LON', 'SAT_EARTH_ALT', 'SAT_RANGE', 'SAT_RANGE_RATE', 'SAT_DEPTH_EC', 'STAR_PARALLAX', 'STAR_PM_RA', 'STAR_PM_DEC', 'STAR_POS_ERR_RA', 'STAR_POS_ERR_DEC', 'STAR_POS_ERR_PRLX', 'STAR_PM_POS_ERR_RA', 'STAR_PM_POS_ERR_DEC', 'TWIL_CIVIL_START', 'TWIL_CIVIL_END', 'TWIL_NAUT_START', 'TWIL_NAUT_END', 'TWIL_ASTRON_START', 'TWIL_ASTRON_END', 'SIDEREAL', 'JUL_DATE', 'CLICK_DIST', 'POINT3D_X', 'POINT3D_Y', 'POINT3D_Z', 'FRAME_SIZE_MINS', 'SUN_DIST_LY', 'DIST_PARSEC', 'SCALE_ASPIX', 'HEIGHT', 'WIDTH', 'UMBRA_RAD', 'PENUMBRA_RAD', 'ANG_SEP_PRIOR', 'PA_PRIOR', 'COUNT' ]
		if len(params)==len(dum):
			d=dict()
			for p,j in zip(params,dum):
				dummy={p:j}
				d.update(dummy)
		else: return 'The params list and the parameter output from TheSky are not the same size'
		return str(d)
				
	def cmd_slewToObject(self,the_command):
		'''Function that will take an object as input and use the find and objInfo functions to slew to it'''
		commands = str.split(the_command)
		if len(commands)!=2: return 'This function takes a single argument with the object name'
		dummy=self.cmd_find('find '+commands[1])
		if 'ERROR' in dummy: return 'Unsuccessful attempt at finding object of interest' 
		#get the dictionary of object properties from TheSkyX
		d=ast.literal_eval(self.cmd_objInfo('objInfo'))
		if d['ALT']<0.0: return 'Unable to slew. Object below the horizon!'
		#slew the telescope
		result=self.cmd_slewToRaDec('slewToRaDec '+str(d['RA_2000'])+' '+str(d['DEC_2000']))
		if 'ERROR' in result: return 'Unable to slew the telescope to the intended target'
		return 'Telescope Slewing'

	def cmd_getTargetRaDec(self,the_command): #***************************
		'''Returns the RA and dec of the target.'''
		commands = str.split(the_command)
		if len(commands) == 2:
			obj = commands[1]
			linestoreplace = ['var Target = "object";/*Parameterize*/\r\n']
			newlines = ['var Target = "'+obj+'";/*Parameterize*/\r\n']
			if self.editscript('GetTargetRaDec.template', 'GetTargetRaDec.js', linestoreplace,newlines):
				script = self.readscript('GetTargetRaDec.js')
				client_socket.send(script)
				return self.messages()
			else: return 'ERROR reading files'
		else: return 'ERROR, invalid input length'

	def cmd_mountGetRaDec(self,the_command):
		'''Gets the current RA and Dec of the mount.'''
		TheSkyXCommand = self.readscript('MountGetRaDec.js')
		client_socket.send(TheSkyXCommand)
		return self.messages()

	def cmd_SkyDomeGetAz(self,the_command):
		'''Gets the current Azimuth from the virtual dome'''
		TheSkyXCommand = self.readscript('DomeGetAz.js')
		client_socket.send(TheSkyXCommand)
		return self.messages()

	def cmd_SkyDomeForceTrack(self,the_command):
		'''Gets the virtual TheSkyX dome to track along with the telescope'''
		TheSkyXCommand = self.readscript('ForceDomeTracking.js')
		client_socket.send(TheSkyXCommand)
		return self.messages()

	def cmd_getRA(self, the_command):
		'''Returns just the RA of the mount with a simple number output'''
		TheSkyXCommand = self.readscript('MountGetRaDec.js')
		client_socket.send(TheSkyXCommand)
		response = self.messages()
		responses = str.split(response, '|')
		RA = responses[0]
		return RA

	def cmd_getDec(self, the_command):
		'''Returns just the Dec of the mount with a simple number output'''
		TheSkyXCommand = self.readscript('MountGetRaDec.js')
		client_socket.send(TheSkyXCommand)
		response = self.messages()
		responses = str.split(response, '|')
		Dec = responses[1]
		return Dec

	def cmd_mountGetAzAlt(self,the_command):
		'''Gets the current Altitide and Azimuth of the mount.'''
		TheSkyXCommand = self.readscript('MountGetAzAlt.js')
		client_socket.send(TheSkyXCommand)
		return self.messages()

	def cmd_getAzimuth(self, the_command):
		'''Gets the current Azimuth of the mount with a simple number output, range 0 to 360 degrees'''
		TheSkyXCommand = self.readscript('MountGetAzAlt.js')
		client_socket.send(TheSkyXCommand)
		response = self.messages()
		responses = str.split(response, '|')
		Az = responses[0]
		return Az


	def cmd_getAltitude(self, the_command):
		'''Gets the current Altitude of the mount with a simple number output, range -90 to 90 degrees'''
		TheSkyXCommand = self.readscript('MountGetAzAlt.js')
		client_socket.send(TheSkyXCommand)
		response = self.messages()
		responses = str.split(response, '|')
		Alt = responses[1]
		return Alt



	def cmd_moveTelescope(self, the_command):
		'''Will move the telescope by a specified amount. To move up, down, right, or left
		type ie 'moveTelescope north'. To move a specific Ra and Dec coordinate type:
		'moveTelescope 21 20' for example, where 21 is the  Ra and 20 is the Dec'''
		commands = str.split(the_command)
		if len(commands) == 3:
			dRa = commands[1]
			dDec = commands[2]
			linestoreplace = ['var TargetRA = RAtemp;\r\n','var TargetDec = Dectemp;\r\n']
			newlines = ['var TargetRA = "'+dRa+'";\r\n','var TargetDec = "'+dDec+'";\r\n']
			if self.is_float_try(dRa) and self.is_float_try(dDec):
				if self.editscript('MountGoto.template', 'MountGoto.js', linestoreplace,newlines):
					script = self.readscript('MountGoto.js')
					client_socket.send(script)
					return self.messages()
				else: return 'ERROR writing script'
			else: return 'ERROR invalid input'
		elif len(commands) == 2:
			script = ''
			if commands[1] == 'up': script = self.readscript('moveUp.js')
			elif commands[1] == 'down': script = self.readscript('moveDown.js')
			elif commands[1] == 'left': script = self.readscript('moveLeft.js')
			elif commands[1] == 'right': script = self.readscript('moveRight.js')
			else: return 'ERROR invalid input'
			client_socket.send(script)
			return self.messages()
		else: return 'ERROR, invalid input'

	def cmd_findHome(self,the_command):
		'''Will put the telescope in it's 'home' position. This is the position it needs
		to be in before any observing can take place.'''
		script = self.readscript('FindHome.js')
		client_socket.send(script)
		return self.messages()

	def cmd_jog(self,the_command):
		'''Jogs the telescope by a given amount (specified in arcminutes) in a given direction.
		Please input jog direction first and jog amount second. The directions that can be used are: 
		North, South, East, West, Up, Down, Left, Right. '''
		commands = str.split(the_command)
		allowed_directions = ['North','South','East','West','Up','Down','Left','Right']
		if len(commands) == 3:
			dJog = commands[2]
			dDirection = commands[1]
			linestoreplace = ['var dJog = "amountJog";\r\n','var dDirection = "direction";\r\n']
			newlines = ['var dJog = "'+dJog+'";\r\n','var dDirection = "'+dDirection+'";\r\n']
			if self.is_float_try(dJog) and dDirection in allowed_directions:
				if self.editscript('Jog.template', 'Jog.js', linestoreplace,newlines):
					script = self.readscript('Jog.js')
					client_socket.send(script)
					return self.messages()
				else: return 'ERROR: Could not change the template script for Jog.'
			else: return 'ERROR: Either amount not a float or direction not in allowed directions.'
		else: return 'ERROR: Please input the direction and the amount in arcmins.'
		

	def cmd_park(self,the_command):
		'''This will put the telescope in it's parked position, this is the position the
		telescope needs to be in before the telescope is turned off/not in use.'''
		script = self.readscript('Park.js')
		client_socket.send(script)
		return self.messages()

	def cmd_runQuery(self,the_command):
		'''Runs whatever 'Current query' is loaded in TheSkyX and returns a list of the object names.'''
		script = self.readscript('RunQuery.js')
		client_socket.send(script)
		return self.messages()

	def cmd_setParkPosition(self,the_command): # Not sure it's a good idea to be able to remotely set this
		'''This will set the telescopes current position as the park position. Please don't use
		this unless there is an error given of the nature 'no park position set'.'''
		script = self.readscript('setParkPosition.js')
		client_socket.send(script)
		return self.messages()


	def cmd_s(self,the_command):
		'''Stops all telescope motion.'''
		script = self.readscript('moveStop.js')
		client_socket.send(script)
		return self.messages()

	def cmd_slewToRaDec(self,the_command):
		'''Will slew the telescope to the Ra and Dec put in.'''
		commands = str.split(the_command)
		if len(commands) == 3:
			dRa = commands[1]
			dDec = commands[2]
			linestoreplace = ['var TargetRa = Ratemp;\r\n','var TargetDec = Dectemp;\r\n']
			newlines = ['var TargetRa = "'+dRa+'";\r\n','var TargetDec = "'+dDec+'";\r\n']
			if self.is_float_try(dRa) and self.is_float_try(dDec):
				if self.editscript('SlewToRaDec.template', 'SlewToRaDec.js', linestoreplace,newlines):
					script = self.readscript('SlewToRaDec.js')
					client_socket.send(script)
					return self.messages()
				else: return "ERROR with files"
			else: return 'ERROR invalid input'
		else: return 'ERROR invalid input'

	def cmd_slewToAzAlt(self,the_command):
		'''Will slew the telescope to the Az and Alt put in.'''
		commands = str.split(the_command)
		if len(commands) == 3:
			dAz = commands[1]
			dAlt = commands[2]
			linestoreplace = ['var TargetAz = Aztemp;\r\n','var TargetAlt = Alttemp;\r\n']
			newlines = ['var TargetAz = "'+dAz+'";\r\n','var TargetAlt = "'+dAlt+'";\r\n']
			if self.is_float_try(dAz) and self.is_float_try(dAlt):
				if self.editscript('SlewToAzAlt.template', 'SlewToAzAlt.js', linestoreplace,newlines):
					script = self.readscript('SlewToAzAlt.js')
					client_socket.send(script)
					return self.messages()
				else: return "ERROR with files"
			else: return 'ERROR invalid input'
		else: return 'ERROR invalid input'



	def cmd_tracking(self,the_command):
		'''Turns tracking on or off and determines whether to use the sidereal time to set the tracking
		rate, or use a user input, input in form: 'tracking:on/off usesidereal:yes/no RaRate DecRate' ie if you
		wanted to turn tracking on and use sidereal rate input: 'on yes 0 0' to turn tracking on but set the rate
		to your own input put: 'on no 1.5 1.2'.'''
		commands = str.split(the_command)
		tracking = 0 #initially set tracking off
		usesidereal = 1 #intially set to use the sidereal time for tracking rates
		dRaRate = 0.0 #initally set ra tracking rate to 0
		dDecRate = 0.0 #initally set dec tracking rate to 0
		if len(commands) == 5:
			if commands[1] == 'on': tracking = 1 #turn tracking on
			if commands[2] == 'no': currentrates = 0 #use the current rates input by user
			if self.is_float_try(commands[3]) and self.is_float_try(commands[4]):
				dRaRate = commands[3]
				dDecRate = commands[4]
			else: return 'ERROR, invalid input'
			linestoreplace = ['\tsky6RASCOMTele.SetTracking(0,1,0,0);\r\n']
			newlines = ['\tsky6RASCOMTele.SetTracking('+str(tracking)+','+str(usesidereal)+','+str(dRaRate)+','+str(dDecRate)+');\r\n']
			if self.editscript('MountTracking.template', 'MountTracking.js', linestoreplace,newlines):
				script = self.readscript('MountTracking.js')
				client_socket.send(script)
				return self.messages()
			else: return 'ERROR in writing script'
		else: return 'ERROR, invalid input'
				

	def cmd_sendSomething(self, the_command):
		'''Not quite sure what the point of this function is.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			info = ''
			del commands[0]
			for i in range(len(commands)):
				info += commands[i]+' '
			TheSkyXCommand = info
			client_socket.send(TheSkyXCommand)
			return self.messages()
		else: return 'ERROR, invalid input'


	def cmd_telescopeConnect(self,the_command):
		'''Connect with the telescope.'''
		TheSkyXCommand = self.readscript('telescopeConnect.js')
		client_socket.send(TheSkyXCommand)
		return self.messages()


	def cmd_IsDomeGoToComplete(self,the_command):
		#This function doesn't actually work, since it returns that the dome is finished regardless of the motion of the dome!!!!!!
		'''Check whether the dome movement is done in the Sky virtual dome. 
		This function is very useful to make sure no dome motion is ordered before it has stopped moving.'''
		TheSkyXCommand = self.readscript('IsGoToComplete.js')
		client_socket.send(TheSkyXCommand)
		return self.messages()

	def cmd_IsSlewComplete(self,the_command):
		'''Check whether the telescope movement is done in the Sky. 
		This function is very useful to make sure no telescope motion is ordered before the telescope has stopped moving.'''
		TheSkyXCommand = self.readscript('IsSlewComplete.js')
		client_socket.send(TheSkyXCommand)
		return self.messages()


#************************************** END OF USER COMMANDS **************************************#


	def is_float_try(self,stringtry):
		'''Check to see if input is a float.'''
		try:
			float(stringtry)
			return True
		except ValueError:
			return False

	def readscript(self,script):
		'''Will read a file and return the text.'''
		try:
			f = open(script,'r')
			temp = f.read()
			f.close()
			return temp
		except ValueError:
			return -1

	def editscript(self,script, newscript, linestoreplace, newlines):
		'''This will make a script based on the template script to send to TheSky.'''
		try:
			f = open(script,'r') #open the template file
			newf = open(newscript,'w') # write the actual file we want to send to TheSkyX
			temp = []
			temp = f.readlines()
			j = 0
			if len(linestoreplace) != len(newlines): return 0 # catch error
			for s in linestoreplace:
				for i in range(len(temp)):
					if temp[i] == s:
						temp[i] = newlines[j]
				j += 1
			for line in temp:	
				newf.write(line)
			newf.close()
			f.close()
			return 1
		except ValueError:
			return 0

	def convertnumberforfocuser(self, inputnumber):
		'''This will take a user input number and convert it for sending to the focuser in the correct format'''
		numbertoprocess = int(inputnumber)
		temphigher = int(numbertoprocess/256)   # here we have split the number so as to get the two byte form
		templower = numbertoprocess - temphigher*256
		bigend = chr(temphigher)
		littleend = chr(templower)
		return [bigend, littleend]


	def convertfocusoutput(self, outputbig, outputlittle):
		'''This will take the output from the focuser and convert it to a user friendly format'''
		#templist = list(output) #I'm going to assume the length of the string is 2
		bigint = ord(outputbig) #The focuser sends the bigend first
		littleint = ord(outputlittle)
		tophalf = bigint*256
		bottomhalf = littleint
		totalnumber = tophalf+bottomhalf #by now we should have converted the two bytes into one number for easy reading
		return totalnumber	




	def messages(self):  # Need to work on the timeouts.
		'''I'm trying to make this so if you don't get a response within 5 minutes instead
		of hanging indefinitely or completely quitting, the user is simply told, and can 
		try again.'''
		data = ''
		success = 0
		for i in range(300):
			time.sleep(1)
			try:
				data = str(client_socket.recv(50000))
				success = 1
			except ValueError:
				data = 'ERROR, TheSkyX is not responding.'
			if success: break
		return data
	

	
