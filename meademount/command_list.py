# Given a list of functions and a list of strings, this program 
# is designed to find the function matching a given string.
# As this has to be done in principle when "compiling", the C way
# to do this is to have a list of functions and a list of strings.
#
# Function lists may have to be imported from many places, but
# within the same global scope. With the "simple server" mentality, 
# this can be passed a single object that contains the function 
# definitions, as a single object should be enough to contain all
# pieces of hardware (which should be 1).
#
# The idea is that a single call to:
# execute_command(command)
# ... returns a string for successful execution, or a useful string
#
# Try: 
# ./make_command_list dummy_functions.py 
# import dummy_functions as d
# import command_list as cl
# print cl.execute_command("one",d)
# print cl.execute_command("help",d)
# print cl.execute_command("oops",d)

import string
import pydoc

def execute_command(the_command, m):
    '''Find the_command amongst the list of commands like cmd_one in module m
    
    This returns a string containing the response, or a -1 if a quit is commanded.'''
    the_functions = dict(getRA=m.cmd_getRA,getDec=m.cmd_getDec,getAlt=m.cmd_getAlt,getAz=m.cmd_getAz,move=m.cmd_move,slewToRaDec=m.cmd_slewToRaDec,jog=m.cmd_jog,s=m.cmd_s,getAlignmentMenuEntry=m.cmd_getAlignmentMenuEntry,getCalanderDate=m.cmd_getCalanderDate,setCalanderDate=m.cmd_setCalanderDate,getDistBars=m.cmd_getDistBars,setFan=m.cmd_setFan,setFocus=m.cmd_setFocus,fs=m.cmd_fs,fieldOperation=m.cmd_fieldOperation,getFieldRadius=m.cmd_getFieldRadius,setFieldRadius=m.cmd_setFieldRadius,setFieldDerotator=m.cmd_setFieldDerotator,getFindMin=m.cmd_getFindMin,nextFindMin=m.cmd_nextFindMin,getFindType=m.cmd_getFindType,setFindType=m.cmd_setFindType,startFind=m.cmd_startFind,getGMToffset=m.cmd_getGMToffset,setGMToffset=m.cmd_setGMToffset,setGPS=m.cmd_setGPS,getLimit=m.cmd_getLimit,setLimit=m.cmd_setLimit,getLocalTime24=m.cmd_getLocalTime24,getLocalTime12=m.cmd_getLocalTime12,setLocalTime=m.cmd_setLocalTime,getMagLimit=m.cmd_getMagLimit,setMagLimit=m.cmd_setMagLimit,setMaxSlewRate=m.cmd_setMaxSlewRate,setMotionRate=m.cmd_setMotionRate,findObject=m.cmd_findObject,setObjectAlt=m.cmd_setObjectAlt,setObjectAz=m.cmd_setObjectAz,getObjectDec=m.cmd_getObjectDec,setObjectDec=m.cmd_setObjectDec,getObjectRA=m.cmd_getObjectRA,setObjectRA=m.cmd_setObjectRA,getObjectInfo=m.cmd_getObjectInfo,setObjectMessier=m.cmd_setObjectMessier,setObjectNGC=m.cmd_setObjectNGC,setObjectStar=m.cmd_setObjectStar,getSiderealTime=m.cmd_getSiderealTime,setSiderealTime=m.cmd_setSiderealTime,getSiteName=m.cmd_getSiteName,setSiteName=m.cmd_setSiteName,getSiteLatitude=m.cmd_getSiteLatitude,setSiteLatitude=m.cmd_setSiteLatitude,getSiteLongitude=m.cmd_getSiteLongitude,setSiteLongitude=m.cmd_setSiteLongitude,getSizeLimit=m.cmd_getSizeLimit,setSizeLimit=m.cmd_setSizeLimit,getTrackFreq=m.cmd_getTrackFreq,setTrackFreq=m.cmd_setTrackFreq,setNGCType=m.cmd_setNGCType,setReticleBrightness=m.cmd_setReticleBrightness,setStarType=m.cmd_setStarType,setTelescopeAlignment=m.cmd_setTelescopeAlignment,changeManualFreq=m.cmd_changeManualFreq,goHome=m.cmd_goHome,homeSearchSavePos=m.cmd_homeSearchSavePos,homeSearchSaveVal=m.cmd_homeSearchSaveVal,homeStatus=m.cmd_homeStatus,highPrecisionToggle=m.cmd_highPrecisionToggle,sleep=m.cmd_sleep,wakeUp=m.cmd_wakeUp,slewAltAz=m.cmd_slewAltAz,slewObjectCoord=m.cmd_slewObjectCoord,startTelescopeAutomaticAlignmentSequence=m.cmd_startTelescopeAutomaticAlignmentSequence,switchManual=m.cmd_switchManual,switchQuartz=m.cmd_switchQuartz,sync=m.cmd_sync,syncSelenopgraphic=m.cmd_syncSelenopgraphic,meademountHelp=m.cmd_meademountHelp)
    commands = string.split(the_command)
    if len(commands) == 0:
        return ""
    if commands[0] == "help":
        if (len(commands) == 1):
            return 'getRA\ngetDec\ngetAlt\ngetAz\nmove\nslewToRaDec\njog\ns\ngetAlignmentMenuEntry\ngetCalanderDate\nsetCalanderDate\ngetDistBars\nsetFan\nsetFocus\nfs\nfieldOperation\ngetFieldRadius\nsetFieldRadius\nsetFieldDerotator\ngetFindMin\nnextFindMin\ngetFindType\nsetFindType\nstartFind\ngetGMToffset\nsetGMToffset\nsetGPS\ngetLimit\nsetLimit\ngetLocalTime24\ngetLocalTime12\nsetLocalTime\ngetMagLimit\nsetMagLimit\nsetMaxSlewRate\nsetMotionRate\nfindObject\nsetObjectAlt\nsetObjectAz\ngetObjectDec\nsetObjectDec\ngetObjectRA\nsetObjectRA\ngetObjectInfo\nsetObjectMessier\nsetObjectNGC\nsetObjectStar\ngetSiderealTime\nsetSiderealTime\ngetSiteName\nsetSiteName\ngetSiteLatitude\nsetSiteLatitude\ngetSiteLongitude\nsetSiteLongitude\ngetSizeLimit\nsetSizeLimit\ngetTrackFreq\nsetTrackFreq\nsetNGCType\nsetReticleBrightness\nsetStarType\nsetTelescopeAlignment\nchangeManualFreq\ngoHome\nhomeSearchSavePos\nhomeSearchSaveVal\nhomeStatus\nhighPrecisionToggle\nsleep\nwakeUp\nslewAltAz\nslewObjectCoord\nstartTelescopeAutomaticAlignmentSequence\nswitchManual\nswitchQuartz\nsync\nsyncSelenopgraphic\nmeademountHelp'
        elif commands[1] in the_functions:
            td=pydoc.TextDoc()
            return td.docroutine(the_functions[commands[1]])
        else:
            return "ERROR: "+commands[1]+" is not a valid command."
    elif commands[0] == 'exit' or commands[0] == 'bye' or commands[0] == 'quit':
        return -1
    elif commands[0] in the_functions:
        return the_functions[commands[0]](the_command)
    else:
        return "ERROR: Command not found."

