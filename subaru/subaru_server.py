import sys,string,u6,math,copy
sys.path.append('../common/')
from indiclient import *
import numpy as np
import matplotlib.pyplot as plt
import commands
try:
    import pyfits
except:
    import astropy.io.fits as pyfits
import time
import ctypes
import os,subprocess
import ippower
import json
import pdb
#import the tools to do time and coordinate transforms
import ctx
import client_zmq_socket as client_socket
from astropy.time import Time
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroplan import Observer
from astroplan import FixedTarget

subaru = Observer.at_site('subaru')
#Definitions
CCD_TEMP_CHECK_PERIOD=20
LJ_TEMP_CHECK_PERIOD=5
INJECT_STATUS_PERIOD=2
LOG_PERIOD=5
LED_PULSE_TIME=0.1
LONGITUDE=-155.4681 #Mauna Kea
INITIAL_T_TARG = 17.5

failed=False
#Try to connect to the camera
def new_timeout(devicename,vectorname,indi):
    print 'This is a custom timeout. Possibly connection with the device has not been established successfully'
    raise Exception

try:
    indi=indiclient("localhost",7777)
    print 'Got here'
    dummy=indi.set_timeout_handler(new_timeout)
    dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","CONNECT","On")
    dummy=indi.set_and_send_text("SX CCD SXVR-H694","CONNECTION","DISCONNECT","Off")
    #set the camera saving images locally instead of sending them onto some sort of client. This is not designed to have a client.
    print 'successfully connected to camera'
except Exception:
    print 'Can not connect to camera'
    failed=True
time.sleep(1)
#Check connection
try:
    result=indi.get_text("SX CCD SXVR-H694","CONNECTION","CONNECT")
    if result=='Off':
        print 'Unable to connect to SX camera'
        failed=True
except Exception:
    print 'Unable to check camera connection'
    failed=True

try:
    os.system('rm images/TEMPIMAGE.fits')
except:
    pass


if failed==False:
    #set up some options that should not change often
    dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_CLIENT","Off")
    dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_BOTH","Off")
    dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_MODE","UPLOAD_LOCAL","On")
    dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_ON","On")
    dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_OFF","Off")
#   Default binning is 1x1. Not need to set this as it is a CCD default.
#    dummy=indi.set_and_send_float("SX CCD SXVR-H694","CCD_BINNING","VER_BIN",2)
    if not os.path.exists('./images/'):
        dummy=subprocess.call('mkdir ./images', shell=True)
    dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_DIR","images")
    dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_PREFIX","TEMPIMAGE")
    
try:
    LJ=u6.U6()
    #Need to set up fancy DAC here for the temperature control
    #LJ.configIO(NumberOfTimersEnabled = 2, EnableCounter0 = 1, TimerCounterPinOffset=8)
    #LJ.getFeedback(u3.Timer0Config(8), u3.Timer1Config(8)) #Sets up the dome tracking wheel

    #Start off with no current:
    LJ.getFeedback(u6.BitStateWrite(1,0)) #H-Bridge bit 1
    LJ.getFeedback(u6.BitStateWrite(2,0)) #H-Bridge bit 2
    LJ.getFeedback(u6.BitStateWrite(3,0)) #Back-LED Off
except Exception:
    print 'Unable to connect to the labjack.'


class Subaru():
    """As this server class controls several pieces of hardware at once, d
      defaults for this class are in blocks, in the order below... 
      
        SX CAMERA
        Labjack
        IPPower
        Micro Maestro
        
    """
    #Communications with the injection unit. NB this should really all be in an __init__
    inject = client_socket.ClientSocket(device="subaru_inject")
    
    #------------------------------------SX CAMERA----------------------------#
    #Some parameters for the default stats of the camera
    frame_types=['LIGHT','BIAS','DARK','FLAT']

    #parameters related to the exposure settings and whether there is an image being taken at any given time.
    exposing=False
    exposureTime=0
    shutter_position='Closed'
    filename=None
    imtype='none'
    gain=0.3
    exposure_active=False
    #FUNCTIONS: the following two functions are used in the imaging process, they relate to filenames and prevet crashes
    #when there are typos in directories or duplicate filenames

    #parameters relating to the imaging and exposure characteristics
    startTime=0
    endTime=0
    camtemp=-5
    try: 
        print self.cmd_setTemperature('setTemperature '+str(self.camtemp))
    except Exception: print 'Unable to set the camera temperature to default - set manually!'
    #imtype='None'
    shutter=None
    imaging=False
    dithering=False
    filename=None
    nexps=None
    #PArameters to return in the status.
    CCDTemp = 99
    cooling = "Unknown"
    hor_bin=1
    ver_bin=1
    last_CCD_temp_check = 0
    previous_LED_status=False

    toaddrs=['jpsbento@gmail.com','michael.ireland@anu.edu.au']

    #This sort of thing really shows why we need an __init__ !!!
    if os.path.isfile('images/TEMPIMAGE.fits'):
        os.remove('images/TEMPIMAGE.fits')

    #Checks to see if the filename given exists and prompts for overight or rename if it does
    def checkFile (self,file_to_check):
        presence = os.path.exists('./images/'+file_to_check+'.fits')
        if presence == True:
            print 'file already exists, would you like to overwrite existing file? (yes/no)'
            selection = raw_input()
            while selection != 'yes' and selection != 'no' and selection != 'n' and selection !='y':
                print 'please enter yes or no, note if you do choose to not\
                         overwrite you will be promted to enter an alternate file name'
                selection = raw_input()
            if selection == 'yes' or selection == 'y':
                os.remove('./images/'+file_to_check+'.fits')
            elif selection == 'no' or selection == 'n':
                print 'please enter a new filename, if an identical filename is entered it will overwrite the previous one'
                #offers a new name (or directory for input)
                fileInput2 = raw_input()
                self.filename= fileInput2.partition('.fits')[0]

    def cmd_checkTemperature(self,the_command):
        '''This command checks the temperature at the time it is run. No inputs for this function'''
        self.last_CCD_temp_check = time.time()
        try:
            self.CCDTemp=float(commands.getoutput('indi_getprop -p 7777 "SX CCD SXVR-H694.CCD_TEMPERATURE.CCD_TEMPERATURE_VALUE"').split('=')[1])
            self.cooling= indi.get_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_ON")
        except Exception: return 'Unable to check CCD temperature for some reason'
        return 'CCD temperature is '+str(self.CCDTemp)+' degrees C'

    def cmd_setTemperature(self,the_command):
        '''this command sets the temperature of the imaging CCD, input is in degrees C.'''
        commands = str.split(the_command)
        if len(commands) < 2 : return 'error: no input value'
        if len(commands) > 2 : return 'Too many inputs. Just give us the temperature in degrees C.'
        try:
            dummy=indi.set_and_send_float("SX CCD SXVR-H694","CCD_TEMPERATURE","CCD_TEMPERATURE_VALUE",float(commands[1]))
            self.ccdSetpoint=float(commands[1])
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
            dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_ON","On")
            dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_OFF","Off")
            dummy=indi.set_and_send_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_DIR","images")
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
            name=indi.get_text("SX CCD SXVR-H694","DRIVER_INFO","DRIVER_NAME")
            driver=indi.get_text("SX CCD SXVR-H694","DRIVER_INFO","DRIVER_EXEC")
            version=indi.get_text("SX CCD SXVR-H694","DRIVER_INFO","DRIVER_VERSION")
            image_dir=indi.get_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_DIR")
            image_prefix=indi.get_text("SX CCD SXVR-H694","UPLOAD_SETTINGS","UPLOAD_PREFIX")
            cooling=indi.get_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_ON")
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
        return 'Name: '+name+'\n'+'Driver: '+driver+'\n'+'Version: '+version+'\n'+'Image Destination: '+image_dir+'\n'+'Image Prefix: '+image_prefix+'\n'+'Exposure Type :'+frame_type+'\n'+'Cooling Status: '+cooling+'\n'+'Temperature: '+str(temp)+' degrees C'+'\n'+'Left Pixel Coordinate: '+str(left)+'\n'+'Top Pixel Coordinate: '+str(top)+'\n'+'Frame Width: '+str(width)+' Pixels'+'\n'+'Frame Height: '+str(height)+' Pixels'+'\n'+'Horizontal Binning: '+str(hor_bin)+' Pixels'+'\n'+'Vertical Binning: '+str(ver_bin)+' Pixels'+'\n'+'X Resolution: ' +str(resx)+'\n'+'Y Resolution: '+str(resy)+'\n'+'X Pixel Size:'+str(sizex)+' Microns'+'\n'+'Y Pixel Size: '+str(sizey)+' Microns'+'\n'+'Bits per Pixel: '+str(bitspix)

    def cmd_enableRegulation(self,the_command):
        ''' No arguments on this function, just enable cooling if it is not on yet.'''
        try:
            dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_ON","On")
            dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_OFF","Off")
        except Exception: return 'Unable to enable cooling on the camera. Check connection'
        return 'Successfully enabled cooling of the CCD'


    def cmd_disableRegulation(self,the_command):
        ''' No arguments on this function, just disable cooling of CCD.'''
        try:
            dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_ON","Off")
            dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_COOLER","COOLER_OFF","On")
        except Exception: return 'Unable to disable cooling on the camera. Check connection'
        return 'Successfully disabled cooling of the CCD'

    def cmd_changeBinning(self,the_command):
        '''This function is used to change the binning settings of the camera readout. Input horizontal binning, then vertical binning. Example: changeBinning 2 1   This will make it such that the camera readout in 2x1 mode.'''
        commands = str.split(the_command)
        if len(commands)!=3: return 'Invalid inputs, please input both horizontal and vertical binning modes, separated by spaces'
        try:
            horbin=int(commands[1])
            verbin=int(commands[2])
        except Exception: return 'Unable to convert binning values to integers. Did you input numbers for the binning factors?'
        try:
            dummy=indi.set_and_send_float("SX CCD SXVR-H694","CCD_BINNING","HOR_BIN",horbin)
            dummy=indi.set_and_send_float("SX CCD SXVR-H694","CCD_BINNING","VER_BIN",verbin)
        except Exception: return 'Unable to change the binning factor on the camera. Check connection'
        return 'Successfully changed binning factors of the CCD readout.'

    def cmd_imageType(self,the_command):
        '''This function changes the image type of the readout. This will change the image type in the indi library to a suitable state, as well as change the global variable that will populate the images to the indicated type. So, for light images, the image type will be LIGHT and this same keyword will populate the header file. For arc images, the image type will still be LIGHT, but the header keywork will be ARC. '''
        commands=str.split(the_command)
        if len(commands)!=2: return 'Invalid number of arguments. Just put an image type here'
        try:
            self.imtype=commands[1].upper()
            if self.imtype in self.frame_types:
                for i in self.frame_types:
                    if i==self.imtype: dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i,'On')
                    else: dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i,'Off')
            else:
                for i in self.frame_types:
                    if i=='LIGHT': dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i,'On')
                    else: dummy=indi.set_and_send_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i,'Off')
        except Exception: return 'Unable to change image type'
        for i in self.frame_types:
            if indi.get_text("SX CCD SXVR-H694","CCD_FRAME_TYPE","FRAME_"+i)=='On':
                frame_type=i
        return 'Image type changed to '+self.imtype+' with the indi server image type changed to '+frame_type


    def cmd_exp(self,command):
        return self.cmd_exposeAndWait(command)

    def cmd_exposeAndWait(self,command):
        ''' This function takes a full frame image and waits for the image to be read out prior to ending. Usage: exposeAndWait <exptime> <nexps> <filename (optional)> <imtype=light (optional, if not bias or light)>'''
        commands = str.split(command)
        if len(commands) < 3 : return 'error: require 2 input values (exposure time and number of exposures or dither pattern. optional argument is the filename and/or imtype for header keyword if image type is not bias or light. Use "imtype=<image type>" and equaly for filename without spaces'
        #Tests to see if the first command is a float (exposure time) and the second command is a number of images
        try: 
            self.exposureTime = float(commands[1])
            if self.exposureTime==0.0: self.exposureTime=0.01
        except Exception: return 'invalid input, first input must be a value in seconds'
        if commands[2].isdigit():
            self.nexps= int(commands[2])
        else:
            try:
                dither_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"dithers/"+commands[2])
                self.dither_pattern = np.loadtxt(dither_file)
                self.nexps = self.dither_pattern.shape[0]
                self.dithering=True
            except Exception: 
                return 'invalid input: second input must be a number of exposures or dither pattern file'
        response=self.cmd_imageType('imageType Light')
        #if loop to determine if command[2] is open or closed or invalid
        if len(commands)==4:
            if 'filename' in commands[3]: self.filename = str(commands[3]).split('=')[1]
            elif 'imtype' in commands[3]: 
                imtype = str(commands[3]).split('=')[1]
                response=self.cmd_imageType('imageType '+imtype)
            else: return 'Invalid option. Use either imtype=<image type> or filename=<file name>'
        elif len(commands)==5:
            if 'filename' in commands[3]: self.filename = str(commands[3]).split('=')[1]
            elif 'imtype' in commands[3]: 
                imtype = str(commands[3]).split('=')[1]
                response=self.cmd_imageType('imageType '+imtype)
            if 'filename' in commands[4]: self.filename = str(commands[4]).split('=')[1]
            elif 'imtype' in commands[4]: 
                imtype = str(commands[4]).split('=')[1]
                response=self.cmd_imageType('imageType '+imtype)
            if 'filename' in commands[4]: self.filename = str(commands[4]).split('=')[1]                          
            else: return 'Invalid option. Use either imtype=<image type> or filename=<file name>'
        elif len(commands)>5: return 'Invalid number of inputs'
        self.imaging=True
        #Turn the backLED off if it is on.
        self.previous_LED_status = self.backLED
        if (self.backLED):
            self.cmd_backLED("backLED off") 
        return 'Starting the image loop'


    def imaging_loop(self):
        if self.imaging and (not self.exposure_active):
            #print 'Got here'
            try:
                self.capture()
            except Exception: 
                return 'Unable to start exposure, check connection to CCD'
                self.imaging=False
            return 'Exposure Initiated'
        if os.path.isfile('images/TEMPIMAGE.fits'):
            try:
                result=self.finish_exposure('Normal')
                print 'Finished exposure'
                #Dither if we have to
                if self.dithering:
                    try:
                        inject_command = "inject xy {0:.1f} {1:.1f}".format(self.dither_pattern[-self.nexps,0], self.dither_pattern[-self.nexps,1])
                        print inject_command
                        print self.cmd_inject(inject_command)
                    except:
                        #For bugshooting... !!! When tested, neaten this !!!
                        pdb.set_trace()
                self.nexps-=1
                time.sleep(0.1) #How much of a sleep is really needed???
                self.exposure_active=False
                self.filename=None
                if self.nexps==0:
                    self.nexps=None
                    self.imaging=False
                    self.dithering=False
                    print 'Imaging loop finished'
                    if self.previous_LED_status:
                        self.cmd_backLED("backLED on")
                print 'number of exps left',self.nexps
            except: 
                return 'Unable to finish exposure'

    #command that takes an image
    def capture(self):
        self.startTime = time.time()
        #sets up file name
        if not self.filename:
            localtime=time.localtime(time.time())
            self.filename=str(localtime[0])+str(localtime[1]).zfill(2)+str(localtime[2]).zfill(2)+str(localtime[3]).zfill(2)+str(localtime[4]).zfill(2)+str(localtime[5]).zfill(2)
        #calls checking functions
        self.checkFile(self.filename)
        #print 'Got this far'
        #try:
        indi.set_and_send_float("SX CCD SXVR-H694","CCD_EXPOSURE","CCD_EXPOSURE_VALUE",self.exposureTime)
        #print 'Got THIS far'
        #except Exception: return 0
        self.exposure_active=True


    def cmd_abortLoop(self,the_command):
        #Function used to abort the current loop, once the current exposure is completed.
        commands = str.split(the_command)
        if (len(commands)==1 & self.nexps>1):
            self.nexps=1
            return 'Aborted Loop'
        else: return 'This function takes no arguments'

    def cmd_abortExposure(self,the_command):
        #Function used to stop the current exposure
        commands = str.split(the_command)
        if len(commands)==1:
            self.exposure_active=False
            result=indi.set_and_send_float("SX CCD SXVR-H694","CCD_ABORT_EXPOSURE","ABORT",'On')
            self.imaging=False
            self.filename=None
            return 'Aborted exposure'
        else: return 'This function takes no arguments'

    def finish_exposure(self,finishstatus):
        #gets end time
        self.endTime = time.time()
        im=pyfits.open('images/TEMPIMAGE.fits',mode='update')
        hdu=im[0]
        
        print "Adding main header items..."
        #sets up fits header. Most things are self explanatory
        #This ensures that any headers that can be populated at this time are actually done.
        #hdu.header.update('EXPTIME', self.endTime-self.startTime, comment='The frame exposure time in seconds')
        hdu.header.update('ETINSTRU',float(self.exposureTime), 'Instructed exposure time in seconds')
        hdu.header.update('NAXIS1', indi.get_float("SX CCD SXVR-H694","CCD_FRAME","WIDTH"), comment='Width of the CCD in pixels')
        hdu.header.update('NAXIS2', indi.get_float("SX CCD SXVR-H694","CCD_FRAME","HEIGHT"), comment='Height of the CCD in pixels')
        hdu.header.update('GAIN', self.gain, comment='CCD gain in e-/ADU')
        hdu.header.update('XFACTOR', indi.get_float("SX CCD SXVR-H694","CCD_BINNING","HOR_BIN"), 'Camera x binning factor')
        hdu.header.update('YFACTOR', indi.get_float("SX CCD SXVR-H694","CCD_BINNING","VER_BIN"), 'Camera y binning factor')
        #UTC time header keywords
        start=time.gmtime(self.startTime)
        dateobs=str(start[0])+'-'+str(start[1]).zfill(2)+'-'+str(start[2]).zfill(2)
        hdu.header.update('DATE-OBS', dateobs, 'UTC YYYY-MM-DD')
        starttime=str(start[3]).zfill(2)+':'+str(start[4]).zfill(2)+':'+str(start[5]).zfill(2)
        hdu.header.update('UTSTART', starttime , 'UTC HH:MM:SS.ss Exp. Start')
        middleTime=self.startTime+(self.endTime-self.startTime)/2.
        middle=time.gmtime(middleTime)
        midtime=str(middle[3]).zfill(2)+':'+str(middle[4]).zfill(2)+':'+str(middle[5]).zfill(2)
        hdu.header.update('UTMIDDLE', midtime , 'UTC HH:MM:SS.ss Exp. Midpoint')
        end=time.gmtime(self.endTime)
        endtime=str(end[3]).zfill(2)+':'+str(end[4]).zfill(2)+':'+str(end[5]).zfill(2)
        hdu.header.update('UTEND', endtime , 'UTC HH:MM:SS.ss Exp. End')
        ut=str(middle[2]).zfill(2)+'/'+str(middle[1]).zfill(2)+'/'+str(middle[0])+':'+str(middle[3]).zfill(2)+':'+str(middle[4]).zfill(2)+':'+str(middle[5]).zfill(2)
        hdu.header.update('JD', ctx.ut2jd(ut), 'Julian date of Midpoint of exposure')
        lst = ctx.ut2lst(ut,LONGITUDE,flag=1)
        hdu.header.update('LST', lst, 'Local sidereal time of Midpoint')

        print "Adding object ..."
        #Add object keywords. TODO:Add HA, elevation etc using astropy.coord.
        hdu.header.update('OBJECT', self.tgt_name,'Target name')
        if self.tgt_RA:
            hdu.header.update('RA', self.tgt_RA,'Target RA')
            hdu.header.update('DEC', self.tgt_Dec,'Target Dec')
            hdu.header.update('SIMBAD', self.tgt_Simbad,'Target Simbad Name')

	print "Adding Time..."
        #local time header keywords
        start=time.localtime(self.startTime)
        dateobs=str(start[0])+'-'+str(start[1]).zfill(2)+'-'+str(start[2]).zfill(2)
        hdu.header.update('LDATEOBS', dateobs , 'LOCAL YYYY-MM-DD')
        starttime=str(start[3]).zfill(2)+':'+str(start[4]).zfill(2)+':'+str(start[5]).zfill(2)
        hdu.header.update('LTSTART', starttime , 'Local HH:MM:SS.ss Exp. Start')
        middleTime=self.startTime+(self.endTime-self.startTime)/2.
        middle=time.localtime(middleTime)
        midtime=str(middle[3]).zfill(2)+':'+str(middle[4]).zfill(2)+':'+str(middle[5]).zfill(2)
        hdu.header.update('LTMIDDLE', midtime , 'Local HH:MM:SS.ss Exp. Midpoint')
        end=time.localtime(self.endTime)
        endtime=str(end[3]).zfill(2)+':'+str(end[4]).zfill(2)+':'+str(end[5]).zfill(2)
        hdu.header.update('LTEND', endtime , 'Local HH:MM:SS.ss Exp. End')

	print "Adding Camera Temperature"
        hdu.header.update('CAMTEMP', self.CCDTemp, 'Camera temperature (C)')
        #WARNING: The following line causes a CRASH !!! (Maybe)
        #hdu.header.update('CAMTEMP', float(commands.getoutput('indi_getprop -p 7777 "SX CCD SXVR-H694.CCD_TEMPERATURE.CCD_TEMPERATURE_VALUE"').split('=')[1]), 'Camera temperature (C)')
        hdu.header.update('SETPOINT', self.ccdSetpoint, 'Camera temperature setpoint (C)')
        hdu.header.update('COOLING', self.cooling, 'Camera cooling enabled?')
        if self.exposureTime==0.01:
            self.imtype='Bias'
        print 'Current image type just before populating header is:',self.imtype
        hdu.header.update('IMGTYPE', self.imtype, 'Image type')

        print "Adding ZABER and IPPOWER..."
        #Add Zaber keywords
        try:
            hdu.header.update('ZABERY', self.inject_status['pos'][0], "Zaber y-axis position")
            hdu.header.update('ZABERX', self.inject_status['pos'][1], "Zaber x-axis position")
            hdu.header.update('ZABERF', self.inject_status['pos'][2], "Zaber focus axis position")
        except:
            print "Error updating header with injection unit keywords" 

        #Add ippower keywords
        try:
            hdu.header.update('ARC', self.ippower_status['Arc'], "Arc Lamp status (T/F)")
            hdu.header.update('FLAT', self.ippower_status['Flat'], "Flat Lamp status (T/F)")
            hdu.header.update('SXPWR', self.ippower_status['SX'], "SX Power status (T/F)")
        except:
            print "Error updating header with IPPower keywords"
        #Add agitator keyword
        hdu.header.update('AGITATE', self.agitator_status, "Agitator status (T/F)")


        #if finishstatus=='Aborted':
        #       hdu.header.update('EXPSTAT','Aborted', 'This exposure was aborted by the user')
        '''
        hdu.header.update('FILTER', , 'NEED to query this')
        '''
        #hdu.writeto(self.fullpath)
        self.startTime=0
        #self.exposureTime=0
        im.flush()
        os.system('mv images/TEMPIMAGE.fits images/'+self.filename+'.fits')
        print 'Exposure finished'

    #--------------------------------------LABJACK-------------------------------#
    loop_count=0
    loop_fibre=0      #counter for the fibre loop activation
    loop_maxval=0
    log_loop = 0

    feedback_freq=2   #how often to update the feedback loop parameters
    pcm_time=0.5     #total heating cycle time. probably in seconds
    heater_frac=0.0     #fraction of the pcm_time that the heater is on
    delT_int = 0.0
    T_targ = INITIAL_T_TARG
    heater_gain=5
    integral_gain=0.05
    T1=0
    T2=0
    T3=0
    T4=0
    T5=0
    T6=0
    T7=0
    T8=0
    P=0
    RH=0
    last_LJ_temp_check = 0
    LJTemp = 99
    Vref=99
    backLED = False
    heater_mid=0.2 
    pulse_led = False
    last_heater_time=0
    apply_servo = False

    nemails=0
    #*************************************** List of user commands ***************************************#
    def cmd_spectemp(self,the_command):
        '''this command sets the temperature of the spectrograph, input is in degrees C.'''
        commands = str.split(the_command)
        if len(commands) < 2 : return 'error: no input value'
        if len(commands) > 2 : return 'Too many inputs. Just give us the temperature in degrees C.'
        try:
            self.T_targ=float(commands[1])
        except Exception: return 'Unable to set spectrograph temperature'
        return 'Successfully set spectrograph temperature'

    def cmd_pulse(self,the_command):
        '''Set the LED to pulsing mode'''
        commands = str.split(the_command)
        if len(commands) != 2: return "Useage: pulse [on|off]"
        if commands[1] == 'on':
            self.pulse_led=True
        elif commands[1] == 'off':
            self.pulse_led=False
            self.inject.send_command("led 2") 
            if self.backLED:
                self.cmd_backLED("backLED on")
        else:
            return "Useage: led [on|off]"
        return commands[1]
            

    def cmd_ljtemp(self,the_command):
        ''' Get the temperature of the labjack in Kelvin'''
        self.last_LJ_temp_check = time.time()
        self.LJTemp = LJ.getTemperature()-273.15
        return str(self.LJTemp)

    def cmd_heater(self,the_command):
        '''Set the Heater PCM current'''
        commands=str.split(the_command)
        if len(commands) == 2:
            try: heater_frac_temp = float(commands[1])
            except Exception: return 'ERROR: Requires a number between 0 and 1'
            self.heater_frac=heater_frac_temp
        else: return 'ERROR: Requires a number between 0 and 1'

    def cmd_backLED(self, the_command):
        '''Command to control IR LED backfeed.'''
        commands = str.split(the_command)
        if len(commands) != 2: return 'ERROR'
        if commands[1] == 'on':
            LJ.getFeedback(u6.BitStateWrite(3,1))
            self.backLED=True
            return 'backLED on'
        elif commands[1] == 'off':
            LJ.getFeedback(u6.BitStateWrite(3,0))
            self.backLED=False
            return 'backLED off'
        else: return 'ERROR'

    def cmd_servo(self, the_command):
        '''Command to turn servo on or off.'''
        commands = str.split(the_command)
        if len(commands) != 2: return 'ERROR: useage servo [on|off]'
        if commands[1] == 'on':
            self.apply_servo=True
            return 'servo on'
        elif commands[1] == 'off':
            self.apply_servo=False
            return 'servo off'
        else: return 'ERROR'
#******************************* End of user commands ********************************#

    def heaterControl(self):
        '''Pulse positive for heater_frac fraction of a pcm_time time'''
        if time.time() > self.last_heater_time + self.pcm_time:
            self.last_heater_time=time.time()
          #These lines prevents an endless sleep!
            if (self.heater_frac < 0): self.heater_frac=0
            if (self.heater_frac > 1): self.heater_frac=1
          #Switch the heater on...
            if (self.heater_frac==0): LJ.getFeedback(u6.DAC0_8(0))
            else: LJ.getFeedback(u6.DAC0_8(255))

          #Wait
            time.sleep(self.pcm_time*self.heater_frac)
          #Switch the heater off...
            if (self.heater_frac==1): LJ.getFeedback(u6.DAC0_8(255))
            else: LJ.getFeedback(u6.DAC0_8(0))
          #Wait
           # time.sleep(self.pcm_time*(1.0 - self.heater_frac))

    def pulse_led_task(self):
        """LED Should be off before this is called."""
        if ( (self.pulse_led) & (self.backLED) ):
            LJ.getFeedback(u6.BitStateWrite(3,1))
            self.inject.send_command("led 1") 
            time.sleep(LED_PULSE_TIME)   
            LJ.getFeedback(u6.BitStateWrite(3,0))
            self.inject.send_command("led 0") 

#********************************** Feedback loops ***********************************#
    def feedbackLoop(self):
        '''Execute the feedback loop every feedback_freq times. There is no need
        for this loop to be run too often... so feedback_freq should be 2 or more.
        if it is changed, the loop has to be re-tuned.'''

        if self.feedback_freq==0: return

        if (self.loop_count == 0):
        #Firstly, compute temperatures.
        #ResolutionIndex: 0=default, 1-8 for high-speed ADC, 9-13 for high-res ADC on U6-Pro.
        #GainIndex: 0=x1, 1=x10, 2=x100, 3=x1000, 15=autorange.
        #SettlingFactor: 0=Auto, 1=20us, 2=50us, 3=100us, 4=200us, 5=500us, 6=1ms, 7=2ms, 8=5ms, 9=10ms.
                a0 = LJ.getAIN(0,resolutionIndex=8,gainIndex=1,settlingFactor=9,differential=1)
                a1 = LJ.getAIN(1,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #T1: optical bench
                #--> Differential measurement is made between a0 and a1!

                a2 = LJ.getAIN(2,resolutionIndex=8,gainIndex=0,settlingFactor=9)        #chamber
                a3 = LJ.getAIN(3,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #Voltage output humidity sensor
                a8 = LJ.getAIN(8,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #Voltage output pressure sensor
                #a5 = LJ.getAIN(5,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #icebox_2
                #a6 = LJ.getAIN(6,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #wooden_box
                #a7 = LJ.getAIN(7,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #external
                #a8 = LJ.getAIN(8,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #CCD heat sink
                #a4 = LJ.getAIN(4,resolutionIndex=8,gainIndex=0,settlingFactor=0)        #humidity
                #a6 = LJ.getAIN(6,resolutionIndex=8,gainIndex=0,settlingFactor=0)      #pressure
                Vref = LJ.getAIN(5,resolutionIndex=8,gainIndex=0,settlingFactor=0)     #Reference voltage (5V)
                #Use the actual Vref for settings
                self.Vref=Vref

                #Now modify Vref as seen by the thermistor. NB This *doesn't* work.
                #if self.backLED:
                #    Vref += 0#0.09
                #print "Vref: {0:5.3f}".format(Vref)

                R0 = 10 #10KOhm at 25deg!
                Rref = 16

#                dR_B1 = 2*R0*a0/(Vref-a0)     #differential change
#                R1 = R0 + dR_B1                #value of R2 in bridge

                #A wheatstone bridge with Vref-R1-Rref-Gnd on one side, and 
                # Vref-Rref-R1-Gnd on the other side
                R1 = Rref * (Vref + a0) / (Vref - a0)

                #No Wheatstone bridge here - just a voltage divider with
                # Vref - R_therm - R0 - Gnd.
                # a2 / R0 = (Vref - a2) / R_therm
                R2 = R0 * (Vref-a2)/a2        


                T0 = 298
                B = 3920


                #NTC resistors (see Wikipedia Steinhart-Hart equation)

                #Spectrograph bench:
                T1 = 1.0/T0 + math.log(R1/R0)/B   
                self.T1 = 1/T1 - 273

                #Echelle grating temperature
                T2  = 1.0/T0 + math.log(R2/R0)/B
                self.T2 = 1/T2 - 273

                if self.T2>(self.T_targ+5) or self.T1>(self.T_targ+5):
                    if self.nemails==0:
                        try:
                            dummy=self.email_alert('Failure in function feedbackLoop','Bench or Echelle temperature exceeded the safe threshold. Waiting 10 seconds then killing power to camera, heater and computer.')
                            time.sleep(10)
                            dummy=self.ippower('ippower SX off')
                            dummy=self.ippower('ippower NUC off')
                        except Exception: 
                            dummy=self.email_alert('Failure in function feedbackLoop','Bench or Echelle temperature exceeded the safe threshold but unable to kill power to items. CHECK THIS NOW!!!!!')
                        self.nemails=1
                #A Hack for the backLED... no idea why both T1 and T2 change so much.
                #It can't be a Vref change.
                if self.backLED:
                    self.T1 -= 0.1
                    self.T2 -= 0.1

                self.RH = a3/(Vref*0.00636)-(0.1515/0.00636)
                self.P = (a8+0.095*Vref)/(Vref*0.009)*10

                #Spectrograph temperature servo:
                delT = self.T1 - self.T_targ            #delta_T = average of both sensors - T_set    
                self.delT_int += delT              #start: deltT_int = 0 --> add delT to deltT_int per cycle
                if (self.delT_int > 0.5/self.integral_gain): self.delT_int = 0.5/self.integral_gain      # = +5
                elif (self.delT_int < -0.5/self.integral_gain): self.delT_int = -0.5/self.integral_gain  # = -5
                integral_term = self.integral_gain*self.delT_int #integral term (int_gain * delta_T)
                #Full range is 0.7 mK/s. So a gain of 10 will set
                #0.7 mK/s for a 100mK temperature difference.
                if self.apply_servo:
                    self.heater_frac =  self.heater_mid - self.heater_gain*delT - integral_term   #see equation in notebook
                    #This is an attempt to prevent an electrical problem with the heater power supply.
                    if (self.heater_frac < 0.002): self.heater_frac=0
                    if (self.heater_frac > 1): self.heater_frac=1

        #Add to and reset the loop counter if needed.
        self.loop_count += 1
        if (self.loop_count == self.feedback_freq):
                self.loop_count=0


       
    #-----------------------ippower-------------------------------------#
    #ipPower options. This is a unit that is used to control power to units.
    #This dictionary contains which device is plugged into each port. If the connections change, this needs to be changed too!
    power_order={'SX':2,'NUC':1,'Arc':3,'Flat':4}
    ippower_status = dict( (k,False) for k,v in power_order.items() )
    ippower.Options.ipaddr='rhea-ippower'
    #ippower.Options.ipaddr='150.203.89.62'
    #ippower.Options.ipaddr='150.203.91.138'
    ippower.Options.login = 'admin'
    ippower.Options.passwd = '12345678'
    ippower.Options.port = 80

    def cmd_ippower(self,the_command):
        '''Function to control the ippower unit. The first argument is either the name of the device or the port number of the relevant device or "show" for the device list. The second argument is optional, either "on" or "off". Leave blank for power status of device.'''
        commands = str.split(the_command)
        skip_word_check=False
        if len(commands)<2:
            return 'Useage: ippower show or ippower status or ippower [device] [on|off]]'
        if commands[1]=='show': return str(self.power_order)
        if commands[1]=='status':
            IPstatus = ippower.get_power(ippower.Options)
            self.ippower_status = dict( (k,IPstatus[v]) for k,v in self.power_order.items() )
            return json.dumps(self.ippower_status)
        try:
            port=int(commands[1])
            if port > 4 or port <1: return 'Invalid port number'
            skip_word_check=True
        except Exception: pass
        if not skip_word_check:
            if commands[1] in self.power_order.keys():
                for unit,number in self.power_order.iteritems():
                    if unit == commands[1]:
                        port=number
            else: return 'Invalid device. type "ippower show" for a list of devices.'
        if len(commands) == 2:
            try:
                retstr = str( ippower.get_power(ippower.Options,port) )
            except:
                return "IPPower Error"
            return 'The power status of the port into which the '+commands[1]+' is connected is '+ retstr
        elif len(commands) == 3:
            if commands[2]=='on': s=True
            elif commands[2]=='off': s=False
            else: return 'Invalid power status option'
            try: 
                ippower.set_power(ippower.Options,port,s)
                self.ippower_status[port]=s
            except Exception:
                #logging.error('Unable to set power status for port')
                return 'Unable to set power status for port'
            #logging.info(commands[1]+' successfully switched '+commands[2])
            return commands[1]+' successfully switched '+commands[2]
        else: return 'Invalid ippower command'
        if len(commands)>3: return 'Too many arguments'

 


   #-------------------Micro Maestro 6 channel USB servo controller-----------------------#
    #Fibre Agitator options. This controls the fibre agitator servo motor via the USB controller.
    agitator_status=False
    agitator_process=None
    def cmd_agitator(self,the_command):
        '''Function to control the agitator motor/microcontroller. The first argument is either "on" or "off". Leave blank for current status of device.'''
        commands = str.split(the_command)
        #First check if the device is connected
        if not os.path.exists('/dev/ttyACM0'):
            return 'Servo controller is unavailable. Check if it is connected.'
        if len(commands)==1:
            return 'The agitator is currently '+str(self.agitator_status)
        elif len(commands) == 2:
            if str.lower(commands[1])=='on':
                try: 
                    self.agitator_process=subprocess.Popen(['bash','servo_motion.sh'],stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                    return 'Successfully started the agitator'
                    self.agitator_status=True
                except:
                    return 'Failed to start the servo motor controller motion'
            if str.lower(commands[1])=='off':
                try: 
                    self.agitator_process.terminate()
                    returncode=self.agitator_process.wait()
                    self.agitator_process=None
                    return 'Successfully stopped the agitator'
                    self.agitator_status=False
                except:
                    return 'Could not stop the agitator. Check for problems in the hardware.'
        else: 
            return 'This function takes only one argument. Use the help for more info.'
            
    #---------- Additional methods that apply to all submodules/hardware ------------
    last_inject_status=0
    last_log_time =0
    log_filename='TLog' 
    tgt_RA="0 0 0.0"
    tgt_Dec="0 0 0.0"
    tgt_Simbad=None
    tgt_name="None"

    def cmd_pa(self,the_command):
        """Find the position angle of vertical"""
        now = Time.now()
        print "RA: " + self.tgt_RA
        print "Dec: " + self.tgt_Dec
        try:
            c = SkyCoord(self.tgt_RA + ' ' + self.tgt_Dec,unit=(u.hourangle, u.deg))
            target = FixedTarget(name=self.tgt_name,coord=c) 
            lat = subaru.location.latitude.rad
            ha = subaru.target_hour_angle(now,target).rad
            dec = target.dec.rad
            zd = np.pi/2 - subaru.altaz(now,target).alt.rad
            #See http://www.gb.nrao.edu/~rcreager/GBTMetrology/140ft/l0058/gbtmemo52/memo52.html
            sinp = np.sin(ha)/np.sin(zd)*np.cos(lat)
            cosp = (np.sin(lat) - np.sin(dec)*np.cos(zd))/np.sin(zd)/np.cos(dec)
            parallactic_angle = np.degrees(np.arctan2(sinp,cosp))
            #print str(new_parallactic_angle) 
            #parallactic_angle = subaru.parallactic_angle(now, target).deg
            #print str(parallactic_angle)
        except:
            pdb.set_trace() 
            return "0"
        return str(parallactic_angle + 12.8)

    def cmd_mov_rhoth(self,the_command):
        """Move a given distance in arcsec at a given position angle"""
        commands = the_command.split(None,2)
        if len(commands)!=3:
            return "Useage: mov_rhoth [rho] [th]"
        try:
            pa = float(commands[2]) - float(self.cmd_pa("pa"))
            rho = float(commands[1])
        except:
            return "Error parsing rho and pa"
        xsep = rho*307.1*53.2*np.sin(np.radians(pa))
        ysep = rho*307.1*53.2*np.cos(np.radians(pa))
        return "xy {0:5.0f} {1:5.0f}".format(xsep,ysep)

    def cmd_object(self,the_command):
        """Set the object, RA and Dec fields from Simbad"""
        commands = the_command.split(None,1)
        if len(commands)==1:
            return "Useage: object [NAME]"
        self.tgt_name=commands[1].strip()
        #Pass this along to subaru_inject
        inject_command = "inject object " + self.tgt_name
        print self.cmd_inject(inject_command)
        try:
            tgt = Simbad.query_object(self.tgt_name)
        except:
            tgt = None
            print "Error even executing query_object"
        if not tgt:
            tgt_RA=None
            tgt_Dec=None
            tgt_Simbad=None
            return "Error setting object name!"
        self.tgt_Dec=str(tgt['DEC'][0])        
        self.tgt_RA=str(tgt['RA'][0])
        self.tgt_Simbad=str(tgt['MAIN_ID'][0])
        return "Object name set (Simbad: {0:s}).".format(self.tgt_Simbad)

    def cmd_status(self,the_command):
        """Return a dictionary containing the whole instrument status"""
        status = {"CCDTemp":self.CCDTemp,"T1":self.T1,"Vref":self.Vref,"T2":self.T2,\
                  "RH":self.RH,"P":self.P,"heater_frac":self.heater_frac,\
                  "Cooling":self.cooling,"Exposing":self.exposure_active,"Imaging":self.imaging,\
                  "nexps":self.nexps,"horbin":self.hor_bin,"verbin":self.ver_bin,"filename":self.filename,\
                  "agitator":self.agitator_status, "LJTemp":self.LJTemp, "backLED":self.backLED} 
        try:
            status = "status " + json.dumps(status)
        except:
            print "Bad JSON parsing..."
            return
        return status

    def cmd_inject(self,the_command):
        """Communicate with rhea_inject"""
        subaru_inject_command = the_command.split(None,1)[1]
        return self.inject.send_command(subaru_inject_command)  

    def inject_status(self):
        """Ask the inject server for status"""
        if (time.time() > self.last_inject_status + INJECT_STATUS_PERIOD):
            self.last_inject_status = time.time()
            inject_status = self.inject.send_command("status")
            try:
                self.inject_status = json.loads(inject_status.split(None,1)[1])
            except:
                print "Bad JSON parsing of inject...: {0:s}".format(self.inject_status)
    
    def add_to_log(self):
        """Add to the log file, and periodically check various things.
	The log file is designed to be human readable, or readable with:

	from astropy.io import ascii
	table = ascii.read('TLog')"""
        if (time.time() - self.last_CCD_temp_check > CCD_TEMP_CHECK_PERIOD):
            try:
                self.cmd_checkTemperature("checkTemperature")
                self.hor_bin=indi.get_float("SX CCD SXVR-H694","CCD_BINNING","HOR_BIN")
                self.ver_bin=indi.get_float("SX CCD SXVR-H694","CCD_BINNING","VER_BIN")
            except: 
                print "Unable to query CCD camera status!" 
                self.CCDTemp=99

        if (time.time() - self.last_LJ_temp_check > LJ_TEMP_CHECK_PERIOD):
            try:
                self.cmd_ljtemp("ljtemp")
            except: 
                print "Unable to query Labjack Temperature!" 
                self.LJTemp=99

        if (time.time() > self.last_log_time + LOG_PERIOD):
            self.last_log_time = time.time()
            lineOut = " %.4f %.3f %.3f %.3f %.3f %.3f %.1f %.2f %d" % (self.T1,self.Vref,self.T2, self.RH,\
             self.P,self.heater_frac,self.CCDTemp,self.LJTemp,int(self.backLED))
            if not os.path.exists(self.log_filename):
                f = open(self.log_filename,'w')
                f.write("T1 Vref T2 RH P Heater CCDTemp LJTemp backLED Time\n")
                f.close() 
            f = open(self.log_filename,'a')
            f.write(lineOut+' "'+Time.now().iso+'"\n')
            f.close()

            
    def email_alert(self,subject,body):
        #function that gets called when an email alert is to be sent
        # Credentials (if needed)
        try:
            username = 'mqobservatory'
            password = 'macquarieobservatory'
            message = "From: From Rhea Subaru <mqobservatory@gmail.com>\nTo: %s\nSubject: %s\n\n%s" % (', '.join(self.toaddrs),subject,'rhea_subaru'+': '+body)
            # The actual mail send
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login(username,password)
            server.sendmail('mqobservatory@gmail.com', self.toaddrs, message)
            server.quit()
        except Exception: logging.error('Could not send email alert'); print 'Could not send email alert'
        return 'Successfully emailed contacts'

    
