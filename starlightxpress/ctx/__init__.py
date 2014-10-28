# -*- coding: utf-8 -*-


"""
from http://www.cosmichiss.com/ctx.py
"""

import numpy as num
import exceptions

pi = num.pi
sin = num.sin
cos = num.cos
arcsin = num.arcsin
arccos = num.arccos
arctan = num.arctan
arctan2 = num.arctan2
floor = num.floor

# Exception class
class ctxError(exceptions.Exception):
    """For throwing exceptions from the ctx module"""
    pass

def jd2gmst(jd):
	"""
	# Converts a Julian date into Greenwich Mean Sidereal Time (as an angle)
	# Implements the instructions found at:
	# http://www.astro.uu.nl/~strous/AA/en/reken/sterrentijd.html#1
	"""
	L0 = 99.967794687
	L1 = 360.98564736628603
	L2 = 2.907879e-13
	L3 = -5.302e-22
	dJ = jd - 2451544.5 # Difference from 1 Jan 2000 at 00:00:00.0
	th = (L0 + L1*dJ + L2*(dJ**2) + L3*(dJ**3))%360
	return th

def ut2jd(ut):
	"""The input is in the form: 'dd/mm/yyyy:hh:mm:ss.s'"""
	dd = float(ut[0:ut.find('/')])
	ut = ut[ut.find('/')+1:]
	mm = float(ut[0:ut.find('/')])
	ut = ut[ut.find('/')+1:]
	yyyy = float(ut[0:ut.find(':')])
	tm = ut[ut.find(':')+1:]
	h = float(tm[0:tm.find(':')])
	tm = tm[tm.find(':')+1:]
	m = float(tm[0:tm.find(':')])
	s = float(tm[tm.find(':')+1:])
	# What is the Julian date? Instructions at http://quasar.as.utexas.edu/BillInfo/JulianDatesG.html
	# Convert the day
	if mm <= 2:
		yyyy = yyyy-1
		mm = mm+12
	A = floor(yyyy/100.0)
	B = floor(A/4.0)
	C = 2-A+B
	E = floor(365.25*(yyyy+4716))
	F = floor(30.6001*(mm+1))
	JD = C+dd+E+F-1524.5
	# Add the time fraction
	JD = JD + (h+m/60.0+s/3600.0)/24.0
	return JD

def angle2time(ang):
	"""
	# Converts a decimal angle into a time string 'hh:mm:ss.s'
	"""
	# Convert angle to seconds:
	ang = ang/15.0*3600.0
	h = int(ang/3600.0)
	m = int((ang-h*3600)/60)
	s = ang-h*3600-m*60
	time = repr(h)+':'+repr(m)+':'+repr(s)
	return time

def ut2st(time,flag=0):
	"""
	# Converts universal time to universal sidereal time. Returns siderial time in the form of an angle or a time.
	# Angle is in degrees (0 to 360), time is in 'hh:mm:ss.s' string format
	# Returns angle if flag = 0 (default), time if any other value
	# The input is in the form: 'dd/mm/yyyy:hh:mm:ss.s'
	"""
	# What is the Julian date?
	jd = ut2jd(time)
	th = jd2gmst(jd)
	if flag != 0:
		th = angle2time(th)
	return th
	
def ut2lst(time,longitude,flag=0):
	"""
	# Converts universal time to local sidereal time.
	# Accepts decimal degree longitude
	# Returns siderial time in the form of an angle or a time.
	# Angle is in degrees (0 to 360), time is in 'hh:mm:ss.s' string format
	# Returns angle if flag = 0 (default), time if any other value
	# The input is in the form: 'dd/mm/yyyy:hh:mm:ss.s'
	"""
	# What is the Greenwich siderial time?
	th = ut2st(time,0)
	# Convert to local siderial time and modulo if necessary
	th = (th + longitude)%360
	if flag != 0:
		th = angle2time(th)
	return th
	
def time2angle(ST):
	"""
	# Converts a time (in the format 'hh:mm:ss.s') into an angle
	# By the formula angle = 15*(hh + mm/60 + ss.s/3600)
	"""
	h = float(ST[0:ST.find(':')])
	ST = ST[ST.find(':')+1:]
	m = float(ST[0:ST.find(':')])
	s = float(ST[ST.find(':')+1:])
	ang = 15.0*(h+m/60.0+s/3600.0)
	return ang
	
def hms2deg(RA,DEC):
	"""
	# Takes in the RA and DEC in hours minutes seconds (string) and returns it in decimal degrees
	# Must be in the format RA='XXhYYmZZ.Zs' and DEC='XXdYYmZZ.Zs'
	"""
	ra = 15*(float(RA[0:RA.find('h')])+float(RA[RA.find('h')+1:RA.find('m')])/60+float(RA[RA.find('m')+1:RA.find('s')])/3600)
	dec=(abs(float(DEC[0:DEC.find('d')]))+float(DEC[DEC.find('d')+1:DEC.find('m')])/60+float(DEC[DEC.find('m')+1:DEC.find('s')])/3600)
	if float(DEC[0:DEC.find('d')]) < 0: dec = -1*dec
	return (ra,dec)

def rt_matrix(a,b,g):
	"""
	# Returns the ZXZ Euler rotation matrix for euler angles a,b,g (all in radians)
	"""
	A = num.mat([[cos(a),sin(a),0],[-sin(a),cos(a),0],[0,0,1]])
	B = num.mat([[1,0,0],[0,cos(b),sin(b)],[0,-sin(b),cos(b)]])
	G = num.mat([[cos(g),sin(g),0],[-sin(g),cos(g),0],[0,0,1]])
	R = G*(B*A)
	return R
	
def rotate(R,a,d):
	"""
	# Applies the rotation matrix R to the coordinate (a,d), where a and d are in radians
	"""
	# Calculate the sky cosines
	ld = cos(d)*cos(a)
	md = cos(d)*sin(a)
	nd = sin(d)
	L = R*num.mat([[ld],[md],[nd]])
	l = L[0,0]
	m = L[1,0]
	n = L[2,0]
	# Extract the angles
	t = arcsin(n)
	p = arctan2(m,l)
	return (p,t)

def j20002gal(RA,DEC):
	"""
	# Accepts RA and DEC in decimal degrees, and returns (l,b) in decimal Galactic coordinates
	# NOTE: assumes lII,bII galactic coordinates
	"""
	# The position of the galactic north pole in J2000 coordinates used to define the Galactic coordinate system
	ap = 192.8594813
	#ap = 192.25
	dp = 27.1282511
	#dp = 27.4
	# Euler angles are:
	a = (ap+90)*pi/180
	b = (90-dp)*pi/180
	g = -33*pi/180
	# Get the Euler rotation matrix
	R = rt_matrix(a,b,g)
	# Call the function which actually performs the rotation
	(l,b) = rotate(R,RA*pi/180,DEC*pi/180)
	# Do some neatening if the angles are in the wrong range
	if l<0: l = l+2*pi
	return (l*180/pi,b*180/pi)

def gal2j2000(l_0,b_0):
	"""
	# Accepts galactic coordinates l and b in decimal degrees, returns celestial coordinates (a,d) in decimal degrees
	"""
	# The position of the galactic north pole in J2000 coordinates
	ap = 192.8594813
	dp = 27.1282511
	# Euler angles are:
	a = (ap+90)*pi/180
	b = (90-dp)*pi/180
	g = -33*pi/180
	# Get the Euler rotation matrix
	R = rt_matrix(a,b,g)
	# Call the function which actually performs the rotation (using the inverse[transpose] matrix)
	(a,d) = rotate(R.T,l_0*pi/180,b_0*pi/180)
	# Do some neatening if the angles are in the wrong range
	if a<0: a = a+2*pi
	return (a*180/pi,d*180/pi)

def altaz2j2000(alt,az,lat,st):
	"""
	# Converts horizon coordinates to equatorial (J2000) coordinates. Uses Euler rotation of spheres - with matrices (slow)
	# Accepts:
	#	alt:	altitude 	[deg]
	#	az:		azimuth		[deg]
	#	lat:	latitude	[deg]
	#	st:		local siderial time of observation
	# Returns:
	#	(RA,DEC):	Right Ascension and Delination	[deg,deg]
	"""
	# What are the coordinates of the north celestial pole in alt-az at this time?
	# First Euler angle is 90, to get lined up with nodes
	a = 90.0*pi/180
	# Next, the NCP is at the latitude of the observing site in azimuth
	b = (90.0-lat)*pi/180.0
	# Finally, rotate the meridian by 90 degrees
	g = 90*pi/180.0
	# Do this
	R = rt_matrix(a,b,g)
	(ha,dec) = rotate(R,az*pi/180.0,alt*pi/180.0)

	# And now convert HA to RA using local sidereal time
	ra = st*pi/180-ha
	if ra<0: ra = ra+2*pi
	
	return (ra*180.0/pi,dec*180.0/pi)
	
def altaz2j2000_f(alt,az,lat,st):
	"""
	# Converts horizon coordinates to equatorial (J2000) coordinates. Hard-coded, no matrices (faster)
	# Accepts:
	#	alt:	altitude 	[deg]
	#	az:		azimuth		[deg]
	#	lat:	latitude	[deg]
	#	st:		local siderial time of observation [deg]
	# Returns:
	#	(RA,DEC):	Right Ascension and Delination	[deg,deg]
	"""

	b = (90.0-lat)*pi/180.0
	
	alt = alt*pi/180
	az = az*pi/180
	
	ld = cos(alt)*cos(az)
	md = cos(alt)*sin(az)
	nd = sin(alt)
	ha = arctan2(-md,-cos(b)*ld + sin(b)*nd)
	dec= arcsin(sin(b)*ld + cos(b)*nd)
	ra = st*pi/180-ha
	
	return (ra*180.0/pi,dec*180.0/pi)
	
def altaz2hd_getR(alt,az,lat):
	"""
	# Returns the rotation matrix that converts horizon coordinates to (HA, dec) coordinates
	# Accepts:
	#	alt:	altitude 	[deg]
	#	az:		azimuth		[deg]
	#	lat:	latitude	[deg]
	# Returns:
	#	R:		the rotation matrix
	"""
	# What are the coordinates of the north celestial pole in alt-az at this time?
	# First Euler angle is 90, to get lined up with nodes
	a = 90.0*pi/180
	# Next, the NCP is at the latitude of the observing site in azimuth
	b = (90.0-lat)*pi/180.0
	# Finally, rotate the meridian by 90 degrees RA
	g = 90*pi/180.0
	# Do this
	R = rt_matrix(a,b,g)
	return R


def jd2gd(JD, fractional_year=False):
    """
    task to convert a list of julian dates to gregorian dates
    description at http://mathforum.org/library/drmath/view/51907.html
    Original algorithm in Jean Meeus, "Astronomical Formulae for Calculators"

    give a julian date or list of JDs
    fractional_year=False ; return year float
    else return string (previous print statement)
    """
    import math, sys, string

    if fractional_year:
        output = []
    else:
        output = ''

    if (type(JD)==int) | (type(JD)==float):
        JD = [JD]

    for x in JD:
        try:
            jd=float(x)
        except ValueError:
            continue
        jd=jd+0.5
        Z=int(jd)
        F=jd-Z
        alpha=int((Z-1867216.25)/36524.25)
        A=Z + 1 + alpha - int(alpha/4)

        B = A + 1524
        C = int( (B-122.1)/365.25)
        D = int( 365.25*C )
        E = int( (B-D)/30.6001 )

        dd = B - D - int(30.6001*E) + F

        if E<13.5:
            mm=E-1

        if E>13.5:
            mm=E-13

        if mm>2.5:
            yyyy=C-4716

        if mm<2.5:
            yyyy=C-4715

        months=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        daylist=[31,28,31,30,31,30,31,31,30,31,30,31]
        daylist2=[31,29,31,30,31,30,31,31,30,31,30,31]

        h=int((dd-int(dd))*24)
        min=int((((dd-int(dd))*24)-h)*60)
        sec=86400*(dd-int(dd))-h*3600-min*60

        # Now calculate the fractional year. Do we have a leap year?
        if (yyyy%4 != 0):
            days=daylist2
        elif (yyyy%400 == 0):
            days=daylist2
        elif (yyyy%100 == 0):
            days=daylist
        else:
            days=daylist2

        if fractional_year:
            daysum=0
            for y in range(mm-1):
                daysum=daysum+days[y]
            daysum=daysum+dd-1

            if days[1]==29:
                fracyear=yyyy+daysum/366
            else:
                fracyear=yyyy+daysum/365
            output.append(fracyear)
        else:
            output += str(x)+" = "+months[mm-1]+" %i, %i, " % (dd, yyyy)
            output += string.zfill(h,2)+":"+string.zfill(min,2)+":"+string.zfill(sec,2)+" UTC" + '\n'

    return output


def deg2HMS(RAin):
    """
    Convert degrees to hh:mm:ss.s
    Give decimal degrees
    """
    if (RAin<0):
        sign=-1
        ra=-RAin
    else:
        sign=1
        ra=RAin
    #
    h=int(ra/15.)
    ra -= h*15.
    m=int(ra*4.)
    ra -= m/4.
    s = ra*240.
    #
    if (sign == -1):
        out='-%02d:%02d:%06.3f'%(h,m,s)
    else:
        out = '+%02d:%02d:%06.3f'%(h,m,s)
    #
    return out


def wd2jd(wd):
    """
    WASP date to Julian Date
    """
    wd = num.array(list(wd))
    #
    jd_ref=2453005.5
    jd=(wd/86400.)+jd_ref
    return jd

def jd2wd(jd):
    """
    Julian Date to WASP Date
    """
    jd = num.array(list(jd))
    #
    jd_ref=2453005.5
    wd=((jd-jd_ref)*86400.)
    return wd

def jd2mjd(jd):
    """
    Julian Date to Modified Julian Date
    """
    jd_ref=2400000.5
    mjd=(jd-jd_ref)
    return mjd

def mjd2jd(mjd):
    """
    Modified Julian Date to Julian Date
    """
    mjd = num.array(list(mjd))
    #
    jd_ref=2400000.5
    jd=(mjd+jd_ref)
    return jd



#