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
    the_functions = dict(finishSession=m.cmd_finishSession,startSession=m.cmd_startSession,reconnect=m.cmd_reconnect,labjack=m.cmd_labjack,telescope=m.cmd_telescope,weatherstation=m.cmd_weatherstation,camera=m.cmd_camera,sidecam=m.cmd_sidecam,fiberfeed=m.cmd_fiberfeed,labjacku6=m.cmd_labjacku6,ippower=m.cmd_ippower,setDomeTracking=m.cmd_setDomeTracking,orientateCamera=m.cmd_orientateCamera,offset=m.cmd_offset,focusStar=m.cmd_focusStar,override_wx=m.cmd_override_wx,defGuidingPos=m.cmd_defGuidingPos,guiding=m.cmd_guiding,spiral=m.cmd_spiral,centerStar=m.cmd_centerStar,masterAlign=m.cmd_masterAlign,Imaging=m.cmd_Imaging,Imsettings=m.cmd_Imsettings,checkIfReady=m.cmd_checkIfReady)
    commands = string.split(the_command)
    if len(commands) == 0:
        return ""
    if commands[0] == "help":
        if (len(commands) == 1):
            return 'finishSession\nstartSession\nreconnect\nlabjack\ntelescope\nweatherstation\ncamera\nsidecam\nfiberfeed\nlabjacku6\nippower\nsetDomeTracking\norientateCamera\noffset\nfocusStar\noverride_wx\ndefGuidingPos\nguiding\nspiral\ncenterStar\nmasterAlign\nImaging\nImsettings\ncheckIfReady'
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

