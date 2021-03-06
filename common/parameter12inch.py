#This is a simple python parameter file. Make a copy named to 'parameterfile.py' to activate this as the required file for the software.
#The point of this file is that in principle a casual user of the software should only have to edit this parameter file and not touch any of the _server.py files to operate the observatory.


###### UBER SERVER PARAMETERS ########
servers=['labjack','bisquemount','weatherstation']    #List of active servers. example: servers=['labjack','labjacku6','bisquemount','sidecamera','fiberfeed','sbigudrv','weatherstation']

# A list of the telescopes we have, comment out all but the telescope you wish to connect with:
#telescope_id = 'mq_northdome'
telescope_id = 'mq_southdome'
#telescope_id = 'mtstromlo'



guiding_camera='fiberfeed'     #This can either be sidecam, fiberfeed, or later some guiding package.

#this parameter corresponds to an approximate ratio between the exposure times of the sidecamera and the fiberfeed camera for a given star (or all stars). 
side_fiber_exp_ratio=5.

#ipPower options. This is a unit that is used to control power to units.
#This dictionary contains which device is plugged into each port. If the connections change, this needs to be changed too! 
power_order={'HgAr':1,'none':2,'none':3,'none':4}

#email addresses of recepients of email alerts:
toaddrs = ['jpsbento@gmail.com']

dome_park_position= 250.   # The azimuth of the position the dome is supposed to be at when parked at the end of the night. Should be a good position for charging up the battery with the solar panel. 30 for 16" dome and 250 for 12" dome.

#######################################

####### LABJACK SERVER PARAMETERS ######
labjack_model='U3'      #which model of labjack we are using for the dome+slit control determines which ports need to be activated and the way the RF transmitter works
slits_opening_duration=45  #Time it takes for the slits to open (Irrelevant for this server)
counts_per_degree = 10.9   	# how many counts from the wheel encoder there is to a degree. 11.83 for 16" dome. 10.9 for 12" dome. 


slitoffset = 85.93    # The position, in degrees, of the slits when the home switch is activated. 68.83 for 16" dome. 85.93 for 12" dome.


########################################

########################################

####### BISQUEMOUNT SERVER PARAMETERS #######

ipaddress="10.238.16.14"         #This is the ip address of the windows machine

############################################
###########DOME ALIGNMENT PARAMETERS##################

#These refer to the dimensions of the dome, the position of the mount with respect to the dome and the position of the optical assembly axis to the mount.

#position of the cross over point of the two axes of the mount. Either alt and az or RA and DEC.
mountCenterX = 0 #Positive to North. Dimensions in metres
mountCenterY = 0 #Positive to East. Dimensions in metres
mountCenterZ = -0.7 #Positive Up. Dimensions in metres

otaOffset = 0.46    #Distance between axis intersect and the optical axis. Dimensions in metres
domeRadius = 1.900  #Radius of dome in metres
slitsWidth = 0.80  #Slit width 
latitude = -33.8 #Telescope latitude
longitude = 151.1 #Telescope longitude

#############################################

########## IMAGING SOURCE CAMERAS PARAMETERS#####

sidecamera_model='21AU04.AS'
fiberfeed_model='21AU618.AS'

#############################################

################ SIDECAM PARAMETERS #########

sc_oneArcmininPixelsN = 1/2.  # This tells us how many pixels there are to one arcsecond in the North/South direction
sc_oneArcmininPixelsE = 1/2.  # This tells us how many pixels there are to one arcsecond in the East/West direction

############################################

################ FIBERFEEED PARAMETERS #########

ff_oneArcmininPixelsN = 100  # This tells us how many pixels there are to one arcsecond in the North/South direction
ff_oneArcmininPixelsE = 100  # This tells us how many pixels there are to one arcsecond in the East/West direction

#############################################

################ WEATHERSTATION PARAMETERS #########

weatherstation = 'aurora'   #Variable that defines which weatherstation this is connected to. Use 'aag' for the AAG Cloud Watcher (Stromlo) and 'aurora' for the 'Aurora Cloud Sensor' (MQ)

###############################################
