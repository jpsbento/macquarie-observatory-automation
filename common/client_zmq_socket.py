import sys, time
import string
import zmq
from datetime import datetime
from astropy.table import Table
import numpy as np
import pdb

class ClientSocket:
    MAX_BUFFER = 65536
#    def __init__(self,IP="133.40.162.192", Port=3001):
#    def __init__(self,IP="150.203.89.12",Port=3001):
    def __init__(self,device="subaru_inject",telescope_type="mtstromlo"): 
        t = Table.read('../common/device_list.txt',format="ascii")
        ix = np.where(t['Hardware_Object'] == device)[0][0]
        IP   = t[telescope_type+"IP"][ix]
        Port = t["Port"][ix]
        #NB See the prototype in macquarie-university-automation for a slightly neater start.
        ADS = (IP,Port)
        self.count=0
        try:
            self.context = zmq.Context()
            self.client = self.context.socket(zmq.REQ)
            tcpstring = "tcp://"+IP+":"+str(Port)
            print(tcpstring)
            self.client.connect(tcpstring)
            self.client.RCVTIMEO = 2000
            self.connected=True
        except: 
            print("ERROR: Could not connect to server {0:s}. Please check that the server is running.".format(device))
            self.connected=False

    def send_command(self, command):
        """Try to send a command. If we're not connected, try to receive an old command
        first (and trash it) """
        if self.connected==False:
            try:
                response = self.client.recv(self.MAX_BUFFER,zmq.NOBLOCK)
            except:
                self.count += 1
                return "Could not receive buffered response - connection still lost ({0:d} times).".format(self.count)
            self.connected=True
        
        #Send a command to the client.
        try: 
            self.client.send(command,zmq.NOBLOCK)
        except:
            self.connected=False 
            self.count += 1
            return 'Error sending command, connection lost ({0:d} times).'.format(self.count)
        
        #Receive the response
        try:
            response = self.client.recv(self.MAX_BUFFER,zmq.NOBLOCK)
            self.connected=True
            return response
        except:
            self.connected=False 
            self.count += 1
            return 'Error receiving response, connection lost ({0:d} times)\n'.format(self.count)





