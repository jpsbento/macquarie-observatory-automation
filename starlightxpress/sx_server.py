from indiclient import *
import numpy as np
import matplotlib.pyplot as plt
import pyfits
import time
import ctypes
import os, commands
#import the tools to do time and coordinate transforms
import ctx

"""#the following lines establish a link with the camera via the USB port, these run 
#automatically when sx_main is excecuted
try: 
        if not os.path.exists('/tmp/myFIFO'):
                dummy=subprocess.call('mkfifo /tmp/myFIFO', shell=True)
        if len(commands.getoutput('pgrep indi'))==0:
                indiserver_process=subprocess.Popen('indiserver -f /tmp/myFIFO -p 7777',shell=True)
                sxserver_process=subprocess.call('echo start indi_sx_ccd -n \"SX CCD\" > /tmp/myFIFO', shell=True)
except Exception: print 'Unable to start indi server'

procs=[indiserver_process,sxserver_process]

@atexit.register
def kill_subprocesses():
        for proc in procs:
                proc.kill()
"""
#Try to connect to the camera
try: 
        indi=indiclient("localhost",7777)
        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","CONNECT","On")
        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","DISCONNECT","Off")
        #set the camera saving images locally instead of sending them onto some sort of client. This is not designed to have a client. 
        dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_CLIENT","Off")
        dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_BOTH","Off")
        dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_LOCAL","On")
        dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","CONNECT_COOLER","On")
        dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","DISCONNECT_COOLER","Off")
        print 'successfully connected to camera'
except Exception: print 'Can not connect to camera'
time.sleep(1)
#Check connection
try: 
        result=indi.get_text("SX CCD SXVR-H694","CONNECTION","CONNECT")
        if result=='Off':
                print 'Unable to connect to SX camera'
except Exception: print 'Unable to check camera connection'




class SX:
	#Some parameters for the default stats
        frame_types=['LIGHT','BIAS','DARK','FLAT']
        
        def cmd_checkTemperature(self,the_command):
		'''This command checks the temperature at the time it is run. No inputs for this function'''
                try: 
                        temp=indi.get_float("SX CCD SXVR-H694","CCD_TEMPERATURE","CCD_TEMPERATURE_VALUE")
                except Exception: return 'Unable to check CCD temperature for some reason'
                return 'CCD temperature is '+str(temp)+' degrees C'
        
        def cmd_setTemperature(self,the_command):
		'''this command sets the temperature of the imaging CCD, input is in degrees C.'''
		commands = str.split(the_command)
		if len(commands) < 2 : return 'error: no input value'
                if len(commands) > 2 : return 'Too many inputs. Just give us the temperature in degrees C.'
                try: dummy=indi.set_and_send_float("SX CCD SXVR-H694","CCD_TEMPERATURE","CCD_TEMPERATURE_VALUE",float(commands[1]))
                except Exception: return 'Unable to set camera temperature'
                return 'Successfully set camera temperature'

        def cmd_establishLink(self,the_command):
                '''This command can be used to establish connection with the camera in case that link has been broken. By default, when the class is defined, connection with the camera is achieved anyway, so this should be used sparringly. No inputs to this function'''
                try: 
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","CONNECT","On")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","DISCONNECT","Off")
                        #set the camera saving images locally instead of sending them onto some sort of client. This is not designed to have a client. 
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_CLIENT","Off")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_BOTH","Off")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_LOCAL","On")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","CONNECT_COOLER","On")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","COOLER_CONNECTION","DISCONNECT_COOLER","Off")
                except Exception: return 'Unable to connect to CCD camera'
                return 'Successfully coneected to camera'

        def cmd_closeLink(self,the_command):
                '''This command can be used to break connection with the camera. No inputs to this function'''
                try: 
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","CONNECT","Off")
                        dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","DISCONNECT","On")
                except Exception: return 'Unable to disconnect CCD camera'
                return 'Successfully disconeected to camera'
        
        def cmd_getCCDParams(self,the_command):
                ''' No argument - this function gets the CCD parameters. '''
                #try to acquire all the ccd paramteres that may be useful to know
		try: 
                        name=indi.get_text("SX CCD SXVR-H694","DRIVER_INFO","NAME")
                        driver=indi.get_text("SX CCD SXVR-H694","DRIVER_INFO","EXEC")
                        version=indi.get_text("SX CCD SXVR-H694","DRIVER_INFO","VERSION")
                        image_dir=indi.get_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_DIR")
                        image_prefix=indi.get_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_PREFIX")
                        cooling=indi.get_text("SX CCD SXVR-H694","COOLER_CONNECTION","CONNECT_COOLER")
                        left=indi.get_float("SX CCD SXVR-H694","CCD_FRAME","X")
                        top=indi.get_float("SX CCD SXVR-H694","CCD_FRAME","Y")
                        width=indi.get_float("SX CCD SXVR-H694","CCD_FRAME","WIDTH")
                        height=indi.get_float("SX CCD SXVR-H694","CCD_FRAME","HEIGHT")
                        hor_bin=indi.get_float("SX CCD SXVR-H694","CCD_BINNING","HOR_BIN")
                        ver_bin=indi.get_float("SX CCD SXVR-H694","CCD_BINNING","VER_BIN")
                        temp=indi.get_float("SX CCD SXVR-H694","CCD_TEMPERATURE","CCD_TEMPERATURE_VALUE")
                        resx=indi.get_float("SX CCD SXVR-H694","CCD_INFO","CCD_MAX_X")
                        resy=indi.get_float("SX CCD SXVR-H694","CCD_INFO","CCD_MAX_Y")
                        sizex=indi.get_float("SX CCD SXVR-H694","CCD_INFO","CCD_PIXEL_SIZE_X")
                        sizey=indi.get_float("SX CCD SXVR-H694","CCD_INFO","CCD_PIXEL_SIZE_Y")
                        bitspix=indi.get_float("SX CCD SXVR-H694","CCD_INFO","CCD_BITSPERPIXEL")
                        for i in self.frame_types:
                                if indi.get_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i)=='On':
                                        frame_type=i
                except Exception: return 'Unable to query CCD camera parameters'
                return 'Name: '+name+'\n'+'Driver: '+driver+'\n'+'Version: '+version+'\n'+'Image Destination: '+image_dir+'\n'+'Image Prefix: '+image_prefix+'\n'+'Cooling Status: '+cooling+'\n'+'Temperature: '+str(temp)+' degrees C'+'\n'+'Left Pixel Coordinate: '+str(left)+'\n'+'Top Pixel Coordinate: '+str(top)+'\n'+'Frame Width: '+str(width)+' Pixels'+'\n'+'Frame Height: '+str(height)+' Pixels'+'\n'+'Horizontal Binning: '+str(hor_bin)+' Pixels'+'\n'+'Vertical Binning: '+str(ver_bin)+' Pixels'+'\n'+'X Resolution: ' +str(resx)+'\n'+'Y Resolution: '+str(resy)+'\n'+'X Pixel Size:'+str(sizex)+' Microns'+'\n'+'Y Pixel Size: '+str(sizey)+' Microns'+'\n'+'Bits per Pixel: '+str(bitspix)

