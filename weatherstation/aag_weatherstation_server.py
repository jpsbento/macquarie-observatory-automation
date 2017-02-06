#****************************************************************************#
#               Code to open and read from the weather station               #
#****************************************************************************#
import sys
sys.path.append('../common/')
from indiclient import *
import time,subprocess,os
from datetime import datetime

import parameterfile
try: 
        indi=indiclient('localhost',7780)
        dummy=indi.set_and_send_text("AAG Cloud Watcher","CONNECTION","CONNECT","On")
        dummy=indi.set_and_send_text("AAG Cloud Watcher","CONNECTION","DISCONNECT","Off")
except Exception: print 'Unable to connect to weatherstation'


class WeatherstationServer:
        
        #Global variables

        running = 1
        tempair = 0
        tempsky = 0
        clarity = 0
        light = 0
        rain = 0
        wind=0
        alertstate = 0
        slitvariable = 0 #This is the variable to send to the slits to tell them whether
                         #it's okay to be open or not. 0 to close, 1 to open.
        time_delay=5 #time delay between each reading of the 
        nreadings=0
        nreadings_temp=0
        maximum_delay=90

        rain_conditions='unknown'
        cloud_conditions='unknown'
        brightness_conditions='unknown'
        wind_conditions='unknown'
        logged=True #Boolean for the logging routine.
        
        #set some variables that can be adjusted to redefine which limits are used for cloudy, rainy, light etc.
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsCloud.clear=-5\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsCloud.cloudy=0\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsCloud.overcast=30\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsRain.dry=2000\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsRain.wet=1700\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsRain.rain=400\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsBrightness.dark=2100\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsBrightness.light=100\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsBrightness.veryLight=0\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsWind.calm=10\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.limitsWind.moderateWind=40\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.skyCorrection.k1=33\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.skyCorrection.k2=0\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.skyCorrection.k3=4\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.skyCorrection.k4=100\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.skyCorrection.k5=100\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.heaterParameters.tempLow=0\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.heaterParameters.tempHigh=20\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.heaterParameters.deltaLow=6\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.heaterParameters.deltaHigh=4\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.heaterParameters.min=10\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.heaterParameters.heatImpulseTemp=10\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.heaterParameters.heatImpulseDuration=60\"')
        dummy=os.system('indi_setprop -p 7780 \"AAG Cloud Watcher.heaterParameters.heatImpulseCycle=600\"')


#A list of user commands:

        def cmd_clarity(self,the_command):
                '''Returns the clarity reading from the weather station. This is the difference between 
                the air temperature and the sky temperature.'''
                return str(self.clarity)

        def cmd_light(self,the_command):
                '''Returns the light reading from the weather station. Uncalibrated value, normal range: 0 to 30.'''
                return str(self.light)

        def cmd_rain(self,the_command):
                '''Returns the rain reading from the weather station. Uncalibrated value, normal range: 0 to 30.'''
                return str(self.rain)

        def cmd_tempair(self,the_command):
                '''Returns the air temperature reading from the weather station. Units are in degrees C.'''
                return str(self.tempair)

        def cmd_tempsky(self,the_command):
                '''Returns the sky temperature reading from the weather station. Units are in degrees C.'''
                return str(self.tempsky)

        def cmd_status(self,the_command):
                '''Returns all the latest data output from the weather station.'''
                return "Clarity: "+str(self.clarity)+"\nLight: "+str(self.light)+"\nRain: "+str(self.rain)+"\nAir temperature: "+str(self.tempair)+"\nSky temperature: "+str(self.tempsky)+"\nWind Speed: "+str(self.wind)+"\nNumber of readings: "+str(self.nreadings)+"\nCloud Status: "+self.cloud_conditions+"\nRain Status: "+self.rain_conditions+"\nBrightness Status: "+self.brightness_conditions+"\nWind Status: "+self.wind_conditions

        def cmd_safe(self, the_command):
                '''Returns a 1 if it is safe to open the dome slits, and returns a zero otherwise.'''
                return str(self.slitvariable)

        def run_indigetprop(self):
                '''Since the indiclient does not seem to work well with the AAG, we are using 
                   indi_getprop to grab the weatherstation details'''
                process = subprocess.Popen(['indi_getprop', '-p','7780'], stdout=subprocess.PIPE)
                out, err = process.communicate()
                if len(out):
                        return out.split('\n')
                else:
                        return 0

#************************* End of user commands ********************************#

#Background task that reads data from the weather station and records it to a file

        #definition to read from the serial port
        #I am assuming that only the rainsensortemp and heaterPWM are in hexadecimal
        #I'll know for sure when the aurora guys email me back
        currentTime=time.time()
        last_successful=1E20
        def main(self):
                if time.time()-self.currentTime > self.time_delay:
                        #run the function to grab the details.
                        time.sleep(6)
                        lines=self.run_indigetprop()
                        if not lines:
                                if time.time() - self.last_successful > self.maximum_delay:
                                        self.slitvariable = 0
                                        self.tempair = 0
                                        self.tempsky = 0
                                        self.clarity = 0
                                        self.light = 0
                                        self.rain = 0
                                        self.wind=0
                                        self.alertstate = 0
                                        self.rain_conditions='unknown'
                                        self.cloud_conditions='unknown'
                                        self.brightness_conditions='unknown'
                                        self.wind_conditions='unknown'

                        if 'AAG' in lines[0]:
                                self.last_successful=time.time()
                                self.currentTime=time.time()
                                #Initally set the alert variable to 0 (= Unsafe)
                                #cloudvariable = 0 #this will be set to 1 if it is clear
                                #rainvariable = 0  #this will be set to 1 if it is dry
                                #lightvariable = 0 #this will be set to 1 if it is dark
                                message = ''
                                self.logged=False
                                print 'Logging'
                                for i in lines:
                                        if "ambientTemperatureSensor" in i:
                                                self.tempair=float(i.split('=')[1])
                                        elif "correctedInfraredSky" in i:
                                                self.tempsky=float(i.split('=')[1])
                                        elif "brightnessSensor" in i:
                                                self.light=float(i.split('=')[1])
                                        elif "rainSensor" in i:
                                                self.rain=float(i.split('=')[1])
                                        elif "windSpeed" in i:
                                                self.wind=float(i.split('=')[1])
                                        elif "totalReadings" in i:
                                                self.nreadings=float(i.split('=')[1])
                                        elif ("cloudConditions" in i) and ('=On' in i):
                                                self.cloud_conditions=i.split('.')[-1].split('=')[0]
                                                message += self.cloud_conditions+','
                                                if self.cloud_conditions=='clear': 
                                                        cloudvariable=1
                                                else:
                                                        cloudvariable=0
                                        elif ("brightnessConditions" in i) and ('=On' in i):
                                                self.brightness_conditions=i.split('.')[-1].split('=')[0]
                                                message += self.brightness_conditions+','
                                                if self.brightness_conditions=='dark': 
                                                        brightnessvariable=1
                                                else:
                                                        brightnessvariable=0
                                        elif ("rainConditions" in i) and ('=On' in i):
                                                self.rain_conditions=i.split('.')[-1].split('=')[0]
                                                message += self.rain_conditions+','
                                                if self.rain_conditions=='dry': 
                                                        rainvariable=1
                                                else:
                                                        rainvariable=0
                                        elif ("windConditions" in i) and ('=On' in i):
                                                self.wind_conditions=i.split('.')[-1].split('=')[0]
                                                message += self.wind_conditions+','
                                                if self.wind_conditions=='moderateWind' or self.wind_conditions=='calm': 
                                                        windvariable=1
                                                else:
                                                        windvariable=0
                                self.clarity = self.tempair-self.tempsky #is the difference between the air temperature and the sky temperature
                                self.slitvariable = cloudvariable*rainvariable*brightnessvariable*windvariable #if = 1, it's safe for slits to be open! Unsafe otherwise.
                                #except Exception: print 'Unable to define slit variable'
                        return

        #definition to log the output, stores all data in a file
        def log(self):
                if not self.logged:
                        dir='/media/pi/USB/'
                        if self.slitvariable: message=' Safe for dome to open.'
                        else: message=' NOT safe for dome to open.************' 
                        f = open(dir+'weatherlog.txt','a')
                        f.write(str(time.time())+" "+str(datetime.now())+" "+str(message)+'\n')
                        f.close()
                        h = open(dir+'weatherlog_detailed.txt','a')
                        detailed_message=str(time.time())+";"+str(datetime.now())+";"+"Clarity: "+str(self.clarity)+";Light: "+str(self.light)+";Rain: "+str(self.rain)+";Air temperature: "+str(self.tempair)+";Sky temperature: "+str(self.tempsky)+";"+";Wind Speed: "+str(self.wind)+";Cloud Conditions: "+str(self.cloud_conditions)+";Brightness Conditions: "+str(self.brightness_conditions)+";Rain Conditions: "+str(self.rain_conditions)+";Wind Conditions: "+str(self.wind_conditions)+"\n"
                        h.write(detailed_message)
                        self.logged=True
                        h.close()


