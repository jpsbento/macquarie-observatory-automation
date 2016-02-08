#!/usr/bin/env python
from __future__ import print_function, division
import sys
import string
import select
import socket
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import numpy as np
import zlib
import pdb
import time
import zmq

class ClientSocket:
    MAX_BUFFER = 65536
#    def __init__(self,IP="133.40.162.192", Port=3001):
#    def __init__(self,IP="150.203.89.12",Port=3001):
    def __init__(self,IP="127.0.0.1",Port="3000"): #!!! Set this below - not here !!!
        #NB See the prototype in macquarie-university-automation for a slightly neater start.
        ADS = (IP,Port)
        try:
            self.context = zmq.Context()
            self.client = self.context.socket(zmq.REQ)
            tcpstring = "tcp://"+IP+":"+Port
            print(tcpstring)
            self.client.connect(tcpstring)
            self.client.RCVTIMEO = 1000
            self.connected=True
        except: 
            print('ERROR: Could not connect to server. Please check that the server is running.')
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

class RHEASXGui(QWidget):
    current_image=0;
    def __init__(self, IP='127.0.0.1', parent=None):
        super(RHEASXGui,self).__init__(parent)
        self.client_socket = ClientSocket(IP=IP) 
        lbl1 = QLabel('Command: ', self)
        self.lineedit = QLineEdit("")
        self.connect(self.lineedit, SIGNAL("returnPressed()"),
                        self.send_to_server)
        self.response_label = QLabel('[No Sever Response Yet]', self)
        self.response_label.setStyleSheet("QLabel { background-color : black; color : lime; }")
        self.response_label.setFixedWidth(400)
        self.response_label.setFixedHeight(160)
       
        hbox1 = QHBoxLayout()
        hbox1.addWidget(lbl1)
        hbox1.addWidget(self.lineedit)
        
        layout = QVBoxLayout()
        layout.addLayout(hbox1)
        layout.addWidget(self.response_label)
        self.setLayout(layout)
        self.setWindowTitle("RHEA@Subaru Spectrograph")
        self.stimer = QTimer()
        self.ask_for_status()

    def ask_for_status(self):
        return
        command = "status"
        if (self.client_socket.connected):
            response = self.client_socket.send_command(command)
            if (response.split(" ", 1)[0]=="status"):
                self.update_status(response)
            else:
                self.response_label.setText(response)
        self.stimer.singleShot(200, self.ask_for_image)

    def update_status(self):
        return

    def send_to_server(self):
        if (self.client_socket.connected):
            response = self.client_socket.send_command(str(self.lineedit.text()))
            if (response.split(" ", 1)[0]=="image"):
                self.display_image(response)
            else:
                self.response_label.setText(response)
        else:
            self.response_label.setText("*** Not Connected ***")

        self.lineedit.setText("")

app = QApplication(sys.argv)
if len(sys.argv) > 1:
    myapp = RHEASXGui(IP=sys.argv[1])
else:
    myapp = RHEASXGui()
myapp.show()
sys.exit(app.exec_())      
            


