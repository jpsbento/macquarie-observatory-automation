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
    the_functions = dict(checkTemperature=m.cmd_checkTemperature,setTemperature=m.cmd_setTemperature,establishLink=m.cmd_establishLink,closeLink=m.cmd_closeLink,getCCDParams=m.cmd_getCCDParams,enableRegulation=m.cmd_enableRegulation,disableRegulation=m.cmd_disableRegulation,changeBinning=m.cmd_changeBinning,imageType=m.cmd_imageType,exp=m.cmd_exp,exposeAndWait=m.cmd_exposeAndWait,abortExposure=m.cmd_abortExposure,ljtemp=m.cmd_ljtemp,heater=m.cmd_heater,backLED=m.cmd_backLED,ippower=m.cmd_ippower,agitator=m.cmd_agitator,status=m.cmd_status,inject=m.cmd_inject,abortLoop=m.cmd_abortLoop,pulse=m.cmd_pulse,object=m.cmd_object,servo=m.cmd_servo,spectemp=m.cmd_spectemp,pa=m.cmd_pa,mov_rhoth=m.cmd_mov_rhoth)
    commands = string.split(the_command)
    if len(commands) == 0:
        return ""
    if commands[0] == "help":
        if (len(commands) == 1):
            return 'checkTemperature\nsetTemperature\nestablishLink\ncloseLink\ngetCCDParams\nenableRegulation\ndisableRegulation\nchangeBinning\nimageType\nexp\nexposeAndWait\nabortExposure\nljtemp\nheater\nbackLED\nippower\nagitator\nstatus\ninject\nabortLoop\nled\npulse\nobject\nservo\nspectemp\npa\nmov_rhoth'
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
        return "ERROR: Command not found - {0:s} ".format(commands[0])

