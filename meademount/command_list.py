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
    the_functions = dict(getRA=m.cmd_getRA,getDec=m.cmd_getDec,getAlt=m.cmd_getAlt,getAz=m.cmd_getAz,getSiderealTime=m.cmd_getSiderealTime,setSiderealTime=m.cmd_setSiderealTime,getLocalTime24=m.cmd_getLocalTime24,getLocalTime12=m.cmd_getLocalTime12,setLocalTime=m.cmd_setLocalTime,getCalanderDate=m.cmd_getCalanderDate,setCalanderDate=m.cmd_setCalanderDate,getLatSite=m.cmd_getLatSite,setLatSite=m.cmd_setLatSite,getLongSite=m.cmd_getLongSite,setLongSite=m.cmd_setLongSite,getGMToffset=m.cmd_getGMToffset,setGMToffset=m.cmd_setGMToffset,move=m.cmd_move,slewcoord=m.cmd_slewcoord,slewaltaz=m.cmd_slewaltaz,s=m.cmd_s,setMotionRate=m.cmd_setMotionRate,setMaxSlewRate=m.cmd_setMaxSlewRate,homeSearchSavePos=m.cmd_homeSearchSavePos,homeSearchSaveVal=m.cmd_homeSearchSaveVal,goHome=m.cmd_goHome,homeStatus=m.cmd_homeStatus,getObjectRA=m.cmd_getObjectRA,setObjectRA=m.cmd_setObjectRA,getObjectDec=m.cmd_getObjectDec,setObjectDec=m.cmd_setObjectDec,setObjectAlt=m.cmd_setObjectAlt,setObjectAz=m.cmd_setObjectAz,sync=m.cmd_sync,getFindType=m.cmd_getFindType,setFindType=m.cmd_setFindType,getFindMin=m.cmd_getFindMin,nextFindMin=m.cmd_nextFindMin,getHigherLim=m.cmd_getHigherLim,setHigherLim=m.cmd_setHigherLim,getLowerLim=m.cmd_getLowerLim,setLowerLim=m.cmd_setLowerLim,getBrightMagLim=m.cmd_getBrightMagLim,getFaintMagLim=m.cmd_getFaintMagLim,setBrightMagLim=m.cmd_setBrightMagLim,setFaintMagLim=m.cmd_setFaintMagLim,getLargeSizeLim=m.cmd_getLargeSizeLim,getSmallSizeLim=m.cmd_getSmallSizeLim,setLargeSizeLim=m.cmd_setLargeSizeLim,setSmallSizeLim=m.cmd_setSmallSizeLim,getFieldRadius=m.cmd_getFieldRadius,setFieldRadius=m.cmd_setFieldRadius,startFind=m.cmd_startFind,findNextObj=m.cmd_findNextObj,findPrevObj=m.cmd_findPrevObj,fieldOp=m.cmd_fieldOp,setObjNGC=m.cmd_setObjNGC,setObjMessier=m.cmd_setObjMessier,setObjStar=m.cmd_setObjStar,objectInfo=m.cmd_objectInfo,setNGCType=m.cmd_setNGCType,setStarType=m.cmd_setStarType,reticleBrightness=m.cmd_reticleBrightness,focus=m.cmd_focus,getSiteName=m.cmd_getSiteName,setSiteName=m.cmd_setSiteName,getTrackFreq=m.cmd_getTrackFreq,setTrackFreq=m.cmd_setTrackFreq,switchManual=m.cmd_switchManual,switchQuartz=m.cmd_switchQuartz,changeManFreq=m.cmd_changeManFreq,getDistBars=m.cmd_getDistBars,setTelescopeAlignment=m.cmd_setTelescopeAlignment,fieldDerotator=m.cmd_fieldDerotator,fan=m.cmd_fan)
    commands = string.split(the_command)
    if len(commands) == 0:
        return ""
    if commands[0] == "help":
        if (len(commands) == 1):
            return 'getRA\ngetDec\ngetAlt\ngetAz\ngetSiderealTime\nsetSiderealTime\ngetLocalTime24\ngetLocalTime12\nsetLocalTime\ngetCalanderDate\nsetCalanderDate\ngetLatSite\nsetLatSite\ngetLongSite\nsetLongSite\ngetGMToffset\nsetGMToffset\nmove\nslewcoord\nslewaltaz\ns\nsetMotionRate\nsetMaxSlewRate\nhomeSearchSavePos\nhomeSearchSaveVal\ngoHome\nhomeStatus\ngetObjectRA\nsetObjectRA\ngetObjectDec\nsetObjectDec\nsetObjectAlt\nsetObjectAz\nsync\ngetFindType\nsetFindType\ngetFindMin\nnextFindMin\ngetHigherLim\nsetHigherLim\ngetLowerLim\nsetLowerLim\ngetBrightMagLim\ngetFaintMagLim\nsetBrightMagLim\nsetFaintMagLim\ngetLargeSizeLim\ngetSmallSizeLim\nsetLargeSizeLim\nsetSmallSizeLim\ngetFieldRadius\nsetFieldRadius\nstartFind\nfindNextObj\nfindPrevObj\nfieldOp\nsetObjNGC\nsetObjMessier\nsetObjStar\nobjectInfo\nsetNGCType\nsetStarType\nreticleBrightness\nfocus\ngetSiteName\nsetSiteName\ngetTrackFreq\nsetTrackFreq\nswitchManual\nswitchQuartz\nchangeManFreq\ngetDistBars\nsetTelescopeAlignment\nfieldDerotator\nfan'
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

