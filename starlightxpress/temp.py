# cmdindialta - INDI alta camera version

# this version uses dcd except to capture blob (getINDI for this)

# to do - pass this from pars in acquire.py
indicamhost = "localhost"

# all hardware dependent code should be here

import time
import sys
import os, os.path
sys.path.append("../lib")
from indiclient import *

# create thread lock to ensure that blob is not missed
import thread
noimage = thread.allocate_lock()

# -----------------support functions--------------------------------

def CamSetGeometry (binX,binY,roiStartX,roiStartY,roiPixelsX,roiPixelsY):
#
   indicam=indiclient(indicamhost,7624)
# setting binning and image size to zero leaves values unchanged
#  (need to add error-checking!!)

   expvect = indicam.get_vector("CCDCam","ExpValues")
# hardwire overscan
   element = "OSW"
   value="48" #set to 0 for now since ProcessFitsImage in acquire doesn't handle colbias yet
#   value="0"
   expvect.get_element(element).set_float(float(value))

# set roiStartX,Y     
   element = "ROIX"
   value = roiStartX
   expvect.get_element(element).set_float(float(value))
   element = "ROIY"
   value = roiStartY
   expvect.get_element(element).set_float(float(value))

# binning and size
   if (binX != 0):      
      element = "BinW"
      value = binX
      expvect.get_element(element).set_float(float(value))

   if (binY != 0):      
      element = "BinH"
      value = binY
      expvect.get_element(element).set_float(float(value))

   if (roiPixelsX != 0):                 # unbinned pixels
      element = "ROIW"
      value = int(binX)*int(roiPixelsX)
      expvect.get_element(element).set_float(float(value))

   if (roiPixelsY != 0):      
      element = "ROIH"
      value = int(binY)*int(roiPixelsY)
      expvect.get_element(element).set_float(float(value))

   indicam.send_vector(expvect)
   indicam.quit()

# when error checking added, put in non-zero return value   
   return 0

# ------------primary camera functions------------------------------

def CamInit(cameraID , tempSetPoint,camprops):

   try: 
      indicam=indiclient(indicamhost,7624)
      print "Link Established to Camera."
      linked=True
   except:
      print "ERROR: Link failed to Camera "+str(cameraID)+" ."
      return 1

# get some camera properties and fill camprops
   try:
      propsvect = indicam.get_vector("CCDCam","MaxValues")
      camprops["minexposure"] = propsvect.get_element("ExpTime").get_float()
      camprops["arrayx"]      = propsvect.get_element("ROIW").get_float()
      camprops["arrayy"]      = propsvect.get_element("ROIH").get_float() 
      camprops["overscanx"]   = propsvect.get_element("OSW").get_float()
      camprops["maxbinx"]     = propsvect.get_element("BinW").get_float()
      camprops["maxbiny"]     = propsvect.get_element("BinH").get_float()
#  min temp not necessarily correct from driver - set manually
#      camprops["mintemp"]     = propsvect.get_element("MinTemp").get_float()
      camprops["mintemp"]     = -100.0


      print "Camera Name:  " + str(cameraID)
      print "X Array Size: %-4d" % camprops["arrayx"]
      print "Y Array Size: %-4d" % camprops["arrayy"]
#??      print "X Pixel Size: %6.1f" % cam.PixelSizeX   
#??      print "Y Pixel Size: %6.1f" % cam.PixelSizeY   

   except: 
      print "ERROR. Timeout getting camera props."
      return 1

#fan speed set
   try: 
      fanvect=indicam.get_vector("CCDCam","FanSpeed")
      fanvect.set_by_elementname("Fast")
      indicam.send_vector(fanvect)
      time.sleep(1)
      fanvect=indicam.get_vector("CCDCam","FanSpeed")
      if fanvect.get_active_index() == 3:
         print "Camera fan speed set to fast."
      else:
         print "WARNING. Could not set fan speed to fast."
   except:
      print "WARNING. Could not get fan speed info."
      
   if linked: indicam.quit()
   
   # temp setpoint
   if CamSetTemp (cameraID,tempSetPoint) > 0:
      print "ERROR. Failed to set camera temperature."
      return 1

   return 0

# get image thread functions --------------------------
def getindiblob():
    noimage.acquire()
    print noimage.locked()
    print "DEBUG: getindiblob: getting fits file blob . . . "
    getstring = "getINDI -h " + indicamhost+ " -t 0  \"CCDCam.Pixels.Img\""
    os.system(getstring)
    if noimage.locked():   # may have been killed by blobquit()
       noimage.release()
       print "DEBUG: got blob!"

def blobquit():
# need to actually kill images and cleanup

   while noimage.locked():
      if raw_input()=='q':
#kill exposure if still exists
         setstring = "setINDI -h " + indicamhost+ "\"CCDCam.ExpGo.Go=Off\""
         os.system(setstring)
         if noimage.locked():   # may have been killed by blobquit()
            noimage.release()
            print "DEBUG. Kill getblob thread by hand."


#------------------------------------------------------------------

def CamObserve(exposureTime,imageFilename,imageTitle,imageType,binX,binY, \
               roiStartX,roiStartY,roiPixelsX,roiPixelsY):


# set image geometry; 0's leave everything as is in camera settings
   if (CamSetGeometry(binX,binY,roiStartX,roiStartY,roiPixelsX,roiPixelsY) != 0):
      print "ERROR (cmdindialta): Invalid image geometry parameters."
      return 
   
   indicam=indiclient(indicamhost,7624)
# set shutter state and exposure time
   expvect = indicam.get_vector("CCDCam","ExpValues")

   if ((imageType == 'object') or (imageType == 'flat')):
      value = 1
   else:      
      value = 0
#   print "DEBUG (cmdindialta): Setting shutter to %f." % float(value)
   expvect.get_element("Shutter").set_float(float(value))
   expvect.get_element("ExpTime").set_float(float(exposureTime))
   indicam.send_vector(expvect)
#   print "DEBUG (cmdindialta): indicam.tell()" 
#   indicam.tell()  

# get temp info
   expvect = indicam.get_vector("CCDCam","TempNow")
   tempcam  = expvect.get_element("Temp").get_float()
   print "Camera temperature: %6.1f" % float(tempcam)
   drivecam = expvect.get_element("Temp").get_float()   
   print "Cooler power: %6.1f percent" % float(drivecam)

   
# prepare to launch image
   govect = indicam.get_vector("CCDCam","ExpGo")
   govect.set_by_elementname("Go")
# use getINDI for now to get blob - find a better way?? also, better time estimate??
#   getstring = "getINDI -h " + indicamhost+ " -t 0  \"CCDCam.Pixels.Img\""

   print "DEBUG: starting get blob thread . . "
#   noimage = thread.allocate_lock()
   thread.start_new_thread(getindiblob, ())


#launch image
   try:
      indicam.send_vector(govect)
   except:
      print "ERROR: Exposure failed to launch."
      return 
   
   print "DEBUG: locked? (before sleep)", noimage.locked()
   waits = 0
   while not noimage.locked():
      waits = waits + 1
      time.sleep(0.01)  #let getblob thread catch up to ensure lock
   print "DEBUG: locked? (after sleep)", noimage.locked()
   print "DEBUG: %d cycles required to get lock." % waits

# leave out for now   thread.start_new_thread(blobquit, ())
   
   t=1
   while noimage.locked():
      print "DEBUG: Exposing %d sec . . q<ret> to quit" % t
      t+= 1
      time.sleep(1)

   indicam.quit()
   
# get image
   lsstring = "ls CCDCam.Pixels.Img.fits"
   if (os.system(lsstring) > 0):
      print "ERROR: Cannot find downloaded image."
      return 
   else:
      if (os.path.exists(imageFilename)):
         print "WARNING: %s exists. Saved image appended with .tmp" % imageFilename
         imageFilename = imageFilename +".tmp"
#todo - put error check to ensure output directory exists
      os.rename('CCDCam.Pixels.Img.fits',imageFilename)
# add back in later, annoying during development
#     os.chmod(imageFilename,0444)
   return os.path.split(imageFilename)[1]

#-----------------------------------------------------------------

def CamSetTemp (cameraID,tempSetPoint):
   
   try:
      indicam=indiclient(indicamhost,7624)
      indicam.set_and_send_float("CCDCam","SetTemp","Target",float(tempSetPoint))
      indicam.quit()
      CamCoolerStatus(cameraID)
      return 0
   except:
      print "WARNING. Program cannot set camera temperature." 
      CamCoolerStatus(cameraID)
      return 1

#-----------------------------------------------------------------

def CamCoolerStatus(cameraID):

   try:
      indicam=indiclient(indicamhost,7624)
      tempsetpt = indicam.get_float("CCDCam","SetTemp","Target")
      print "Temperature setpoint: %6.1f" % tempsetpt
      expvect = indicam.get_vector("CCDCam","TempNow")
      tempcam  = expvect.get_element("Temp").get_float()
      print "Camera temperature: %6.1f" % float(tempcam)
      drivecam = expvect.get_element("Temp").get_float()   
      print "Cooler power: %6.1f percent" % float(drivecam)
      indicam.quit()
   except: 
      print "STATUS: Camera cooler disabled?"

#-----------------------------------------------------------------

def CamShutdown (cameraID):

   print "Shutting down camera %s " % cameraID
   print "Note: Link terminated, but camera still active  - remember to shutdown via another INDI client"   

#----------------------------------------------------------------

