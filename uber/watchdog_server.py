 # This will do EVERYTHING
# will make a way to give it a script

import os, sys
sys.path.append('../common/')
import client_socket
import time, math, datetime, csv, ippower
import scipy, pickle
import pyfits
import pylab as pl
import numpy, commands, os

class Watchdog:
    #import all the parameterfile.py parameters
    import parameterfile
    #define system variable to the root directory of the code.
    os.environ['MQOBSSOFT']=commands.getoutput('pwd')[:-5]

    #this lists the servers that are supposed to be active at any given time. It is used by the function that tries to connect to them if any die.
    servers=parameterfile.servers

    # A list of the telescopes we have, comment out all but the telescope you wish to connect with:
    telescope_type = parameterfile.telescope_id


    #email addresses of recepients of email alerts:
    toaddrs = parameterfile.toaddrs

    #reconnect to servers counter. This exists such that if the script is currently trying to reconnect to a server repeatidly and failing, an email alert is sent.
    reconnection_counter=0

    def cmd_reconnect(self,the_command):
        '''Command to force a reconnection to a server. The server options are "labjack", "telescope", "sidecam", "camera", "fiberfeed", "labjacku6" and "weatherstation"'''
        commands=str.split(the_command)
        if len(commands)==2:
            if commands[1]=='labjack':
                self.labjack_client = client_socket.ClientSocket("labjack",self.telescope_type) #23456 <- port number
            elif commands[1]=='telescope':
                self.telescope_client = client_socket.ClientSocket("telescope",self.telescope_type)  #23458 <- port number
            elif commands[1]=='sidecam':
                self.sidecam_client = client_socket.ClientSocket("sidecamera",self.telescope_type) #23459 <- port number
            elif commands[1]=='camera':
                self.camera_client = client_socket.ClientSocket("sx",self.telescope_type) #23460 <- port number
            elif commands[1]=='fiberfeed':
                self.fiberfeed_client = client_socket.ClientSocket("fiberfeed",self.telescope_type) #23459 <- port number
            elif commands[1]=='labjacku6':
                self.labjacku6_client = client_socket.ClientSocket("labjacku6",self.telescope_type) #23462 <- port number
            elif commands[1]=='weatherstation':
                self.weatherstation_client = client_socket.ClientSocket("weatherstation",self.telescope_type) #23457 <- port number
            else: return 'Unknown server name to reconnect to'
            logging.info('Successfully reconnected to server')
            return 'Successfully reconnected to server'
        else:
            logging.error('Need a server name to connect to')
            return 'ERROR: Need a server name to connect to'



    def server_check(self):
        #This function will take care of making sure all servers are on at all times and that the uber server is connected to them in case they fail. See list of servers at the top of the class definition.
        #servers=['labjack','labjacku6','bisquemount','sidecamera','fiberfeed','sbigudrv']
        dead_servers=[]
        if self.reconnection_counter==15:
            dummy=self.email_alert('Failure in function server_check','Uber server is failing to successfully reconnect to one or more servers. Please check!')
        for s in self.servers:
            if not 'python ./'+s+'_main' in os.popen("ps aux").read():
                dead_servers.append(s)
        #print dead_servers, self.servers
        if len(dead_servers)!=0:
            #print 'Actually trying this'
            self.reconnection_counter+=1
            if 'labjack' in dead_servers:
                print 'labjack server dead, restarting and reconnecting'
                logging.info('labjack server dead, restarting and reconnecting')
                try:
                    dummy=os.system('screen -X -S labjack quit')
                    dummy=os.system('screen -dmS labjack bash -c "cd $MQOBSSOFT/labjack/; ./labjack_main; exec bash"')
                except Exception:
                    logging.error('Could not restart the labjack server')
                    return 'Could not restart the labjack server'
                time.sleep(3)
                result=self.cmd_reconnect('reconnect labjack')
                if 'Successfully' not in result:
                    logging.error('Could not reconnect to labjack server')
                    return 'Could not reconnect the labjack server'
            if 'labjacku6' in dead_servers:
                print 'labjacku6 server dead, restarting and reconnecting'
                logging.info('labjacku6 server dead, restarting and reconnecting')
                try:
                    dummy=os.system('screen -X -S u6 quit')
                    dummy=os.system('screen -dmS u6 bash -c "cd $MQOBSSOFT/labjacku6/; ./labjacku6_main; exec bash"')
                except Exception:
                    logging.error('Could not restart the labjacku6 server')
                    return 'Could not restart the labjacku6 server'
                time.sleep(3)
                result=self.cmd_reconnect('reconnect labjacku6')
                if 'Successfully' not in result:
                    logging.error('Could not reconnect to labjacku6 server')
                    return 'Could not reconnect the labjacku6 server'
            if 'bisquemount' in dead_servers:
                print 'telescope server dead, restarting and reconnecting'
                logging.info('telescope server dead, restarting and reconnecting')
                try:
                    dummy=os.system('screen -X -S telescope quit')
                    dummy=os.system('screen -dmS telescope bash -c "cd $MQOBSSOFT/bisquemount/; ./bisquemount_main; exec bash"')
                except Exception:
                    logging.error('Could not restart the telescope server')
                    return 'Could not restart the telescope server'
                time.sleep(3)
                result=self.cmd_reconnect('reconnect telescope')
                if 'Successfully' not in result:
                    logging.error('Could not reconnect to telescope server')
                    return 'Could not reconnect the telescope server'
            if 'sidecamera' in dead_servers:
                print 'sidecamera server dead, restarting and reconnecting'
                logging.info('sidecamera server dead, restarting and reconnecting')
                try:
                    dummy=os.system('screen -X -S sidecamera am quit')
                    dummy=os.system('screen -dmS sidecamera bash -c "cd $MQOBSSOFT/sidecamera/; ./sidecamera_main; exec bash"')
                except Exception:
                    logging.error('Could not restart the sidecamera server')
                    return 'Could not restart the sidecamera server'
                time.sleep(5)
                result=self.cmd_reconnect('reconnect sidecamera')
                if 'Successfully' not in result:
                    logging.error('Could not reconnect to sidecamera server')
                    return 'Could not reconnect the sidecamera server'
            if 'fiberfeed' in dead_servers:
                print 'fiberfeed server dead, restarting and reconnecting'
                logging.info('fiberfeed server dead, restarting and reconnecting')
                try:
                    dummy=os.system('screen -X -S fiberfeed quit')
                    dummy=os.system('screen -dmS fiberfeed bash -c "cd $MQOBSSOFT/fiberfeed/; ./fiberfeed_main; exec bash"')
                except Exception:
                    logging.error('Could not restart the fiberfeed server')
                    return 'Could not restart the fiberfeed server'
                time.sleep(3)
                result=self.cmd_reconnect('reconnect fiberfeed')
                if 'Successfully' not in result:
                    logging.error('Could not reconnect to fiberfeed server')
                    return 'Could not reconnect the fiberfeed server'
            if 'sbigudrv' in dead_servers:
                print 'camera server dead, restarting and reconnecting'
                logging.info('camera server dead, restarting and reconnecting')
                try:
                    dummy=os.system('screen -X -S camera quit')
                    dummy=os.system('screen -dmS camera bash -c "cd $MQOBSSOFT/sbig/; ./sbigudrv_main; exec bash"')
                except Exception:
                    logging.error('Could not restart the camera server')
                    return 'Could not restart the camera server'
                time.sleep(3)
                result=self.cmd_reconnect('reconnect camera')
                if 'Successfully' not in result:
                    logging.error('Could not reconnect to camera server')
                    return 'Could not reconnect the camera server'
            if 'weatherstation' in dead_servers:
                print 'weatherstation server dead, restarting and reconnecting'
                logging.info('weatherstation server dead, restarting and reconnecting')
                try:
                    dummy=os.system('screen -X -S weatherstation quit')
                    dummy=os.system('screen -dmS weatherstation bash -c "cd $MQOBSSOFT/weatherstation/; ./weatherstation_main; exec bash"')
                except Exception:
                    logging.error('Could not restart the weatherstation server')
                    return 'Could not restart the weatherstation server'
                time.sleep(3)
                result=self.cmd_reconnect('reconnect weatherstation')
                if 'Successfully' not in result:
                    logging.error('Could not reconnect to weatherstation server')
                    return 'Could not reconnect the weatherstation server'
        else: self.reconnection_counter=0



    def email_alert(self,subject,body):
        #function that gets called when an email alert is to be sent
        # Credentials (if needed)
        try:
            username = 'mqobservatory'
            password = 'macquarieobservatory'
            message = "From: From MQ Obs <mqobservatory@gmail.com>\nTo: %s\nSubject: %s\n\n%s" % (', '.join(self.toaddrs),subject,self.telescope_type+': '+body)
            # The actual mail send
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login(username,password)
            server.sendmail('mqobservatory@gmail.com', self.toaddrs, message)
            server.quit()
        except Exception: logging.error('Could not send email alert'); print 'Could not send email alert'
        return 'Successfully emailed contacts'


