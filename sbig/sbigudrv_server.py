import sbigudrv as sb
import numpy as np
          
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
		b = sb.SetTemperatureRegulationParams()
		b.regulation = 1
		try: tempC = int(commands[1])
		except Exception: return 'invalid input'
		v1 = (3.0 * np.exp((0.943906 * (25.0 -tempC))/25.0))
		temp = int(4096.0/((10.0/v1) + 1.0))
		b.ccdSetpoint = temp
		sb.SBIGUnivDrvCommand(sb.CC_SET_TEMPERATURE_REGULATION, b, None)
		a = sb.QueryTemperatureStatusResults()
		sb.SBIGUnivDrvCommand(sb.CC_QUERY_TEMPERATURE_STATUS,None,a)
		SPa = a.ccdThermistor
		v2 = 4096.0/SPa	
		v3 = 10.0/(v2-1.0)
		ccdThermistorC = 25.0 - 25.0 *((np.log(v3/3.0))/0.943906)
		return 'regulation = ' +str(b.regulation) +', power = '+str(a.power) + ', CCD set point (A/D) = ' + str(a.ccdSetpoint) + ', CCD set point (C) = ' + str(tempC)+', current CCD temp (A/D) = ' + str(a.ccdThermistor) + ', current CCD temp (C) = ' + str(ccdThermistorC)
		
	def cmd_checkTemperature(self,the_command):
		a = sb.QueryTemperatureStatusResults()
		sb.SBIGUnivDrvCommand(sb.CC_QUERY_TEMPERATURE_STATUS,None,a)
		SP = a.ccdSetpoint
		v1 = 4096.0/SP
		v2 = 10.0/(v1-1.0)
		setPointC = int(25.0 - 25.0 *((np.log(v2/3.0))/0.943906))
		
		v3 = 4096.0/a.ccdThermistor
		v4 = 10.0/(v3-1.0)
		TempC = 25.0 - 25.0 *((np.log(v4/3.0))/0.943906)
		
		return 'regulation = ' +str(a.enabled) +', power = '+str(a.power) + ', CCD set point (A/D) = ' + str(a.ccdSetpoint) + ', CCD set point (C) = ' + str(setPointC)+', current CCD temp (A/D) = ' + str(a.ccdThermistor) + ', current CCD temp (C)' + str(TempC)

	def cmd_disableRegulation(self,the_command):
		b = sb.SetTemperatureRegulationParams()
		b.regulation = 0
		b.ccdSetpoint = 1000
		sb.SBIGUnivDrvCommand(sb.CC_SET_TEMPERATURE_REGULATION, b, None)
		a = sb.QueryTemperatureStatusResults()
		sb.SBIGUnivDrvCommand(sb.CC_QUERY_TEMPERATURE_STATUS,None,a)
		
		v1 = 4096.0/b.ccdSetpoint
		v2 = 10.0/(v1-1.0)
		setPointC = int(25.0 - 25.0 *((np.log(v2/3.0))/0.943906))
		
		v3 = 4096.0/a.ccdThermistor
		v4 = 10.0/(v3-1.0)
		TempC = 25.0 - 25.0 *((np.log(v4/3.0))/0.943906)
		
		return 'regulation = ' +str(b.regulation) +', power = '+str(a.power) + ', CCD set point (A/D) = ' + str(a.ccdSetpoint) + ', CCD set point (C) = ' + str(setPointC)+', current CCD temp (A/D) = ' + str(a.ccdThermistor) + ', current CCD temp (C)' + str(TempC)

			
		
