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
    the_functions = dict(captureImages=m.cmd_captureImages,brightStarCoords=m.cmd_brightStarCoords,adjustExposure=m.cmd_adjustExposure,setCameraValues=m.cmd_setCameraValues,starDistanceFromCenter=m.cmd_starDistanceFromCenter,orientationCapture=m.cmd_orientationCapture,calculateCameraOrientation=m.cmd_calculateCameraOrientation,Chop=m.cmd_Chop,imageCube=m.cmd_imageCube,defineCenter=m.cmd_defineCenter,centerIsHere=m.cmd_centerIsHere,currentExposure=m.cmd_currentExposure,changeExposure=m.cmd_changeExposure)
    commands = string.split(the_command)
    if len(commands) == 0:
        return ""
    if commands[0] == "help":
        if (len(commands) == 1):
            return 'captureImages\nbrightStarCoords\nadjustExposure\nsetCameraValues\nstarDistanceFromCenter\norientationCapture\ncalculateCameraOrientation\nChop\nimageCube\ndefineCenter\ncenterIsHere\ncurrentExposure\nchangeExposure'
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

