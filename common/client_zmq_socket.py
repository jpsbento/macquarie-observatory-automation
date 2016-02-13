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
        try:
            self.context = zmq.Context()
            self.client = self.context.socket(zmq.REQ)
            tcpstring = "tcp://"+IP+":"+str(Port)
            print(tcpstring)
            self.client.connect(tcpstring)
            self.client.RCVTIMEO = 1000
            self.connected=True
        except: 
            print("ERROR: Could not connect to server {0:s}. Please check that the server is running.".format(device))
            self.connected=False

    def send_command(self, command):
        """WARNING: currently a blocking send/recv!"""
        try: 
            self.client.send(command,zmq.NOBLOCK)
            return self.client.recv(self.MAX_BUFFER,zmq.NOBLOCK)
        except:
#            self.connected=False 
#            self.client.close()
            return 'Error sending command, connection lost.'
#        try: return self.client.recv(self.MAX_BUFFER,zmq.NOBLOCK)
#        except Exception: return 'Error receiving response'





