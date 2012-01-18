import sbigudrv as sb
          
sb.SBIGUnivDrvCommand(sb.CC_OPEN_DRIVER, None,None)

r = sb.QueryUSBResults()
sb.SBIGUnivDrvCommand(sb.CC_QUERY_USB, None,r)

p = sb.OpenDeviceParams()
p.deviceType=0x7F00
sb.SBIGUnivDrvCommand(sb.CC_OPEN_DEVICE, p, None)

p = sb.EstablishLinkParams()
r = sb.EstablishLinkResults()
sb.SBIGUnivDrvCommand(sb.CC_ESTABLISH_LINK,p,r)

class SBigUDrv:

	def cmd_setTemperature(self,the_command):
		commands = str.split(the_command)
		if len(commands) < 2 : return 'error: no input value'
		b = self.sb.SetTemperatureRegulationParams()
		b.Regulation = 1
		try: temp = int(commands[1])
		except Exception: return 'invalid input'
		b.ccdSetpoint = temp
		self.sb.SBIGUnivDrvCommand(sb.CC_SET_TEMPERATURE_REGULATION, b, None)
		a = self.sb.QueryTemperatureStatusResults()
		self.sb.SBIGUnivDrvCommand(sb.CC_QUERY_TEMPERATURE_STATUS,None,a)
		return 'fan power = '+str(a.power) + ', CCD set point = ' + str(a.ccdSetpoint) +', current CCD temp = ' + str(a.ccdThermistor)
		
	def cmd_checkTemperature(self,the_command):
		a = self.sb.QueryTemperatureStatusResults()
		self.sb.SBIGUnivDrvCommand(sb.CC_QUERY_TEMPERATURE_STATUS,None,a)
		return 'fan power = '+str(a.power) + ', CCD set point = ' + str(a.ccdSetpoint) +', current CCD temp = ' + str(a.ccdThermistor)

			
		
