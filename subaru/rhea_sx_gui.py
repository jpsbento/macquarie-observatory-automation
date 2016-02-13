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
import json

class ClientSocket:
    """ This class aims to be the simplest possible class to act as a client in 
    simple client-server communication. The protocol is: command (a string with no
    spaces), then a space, then data. A returned string begins with the same command
    if it is the kind of response that needs action. Otherwise just a message."""
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
            self.client.RCVTIMEO = 20000
            self.connected=True
        except: 
            print('ERROR: Could not connect to server. Please check that the server is running.')
            self.connected=False

    def send_command(self, command):
        """The main send-command routine for the client.
        
        TODO: If there is a timeout, we maybe just need to record that there has 
        been a timeout, and try recv later. BUT - the server should never 
        take a long time to return."""
        try: 
            self.client.send(command,zmq.NOBLOCK)
            return self.client.recv(self.MAX_BUFFER,zmq.NOBLOCK)
        except:
#           The commands below should only be part of a "reconnect" function 
#           (NOT YET IMPLEMENTED, NEEDS A PING FUNCTION, MAYBE CALLED PING)
#            self.connected=False 
#            self.client.close()
            return 'Error sending command, connection lost or excessive command time.'

class RHEASXGui(QWidget):
    current_image=0;
    def __init__(self, IP='127.0.0.1', parent=None):
        super(RHEASXGui,self).__init__(parent)
        self.client_socket = ClientSocket(IP=IP) 
        self.wl_button = QPushButton('SX', self)
        self.wl_button.clicked.connect(self.ippower_button_click)
        self.wl_button.setCheckable(True)
        self.arc_button = QPushButton('Arc', self)
        self.arc_button.clicked.connect(self.ippower_button_click)
        self.arc_button.setCheckable(True)
        self.sx_button = QPushButton('WhiteLight', self)
        self.sx_button.clicked.connect(self.ippower_button_click)
        self.sx_button.setCheckable(True)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.wl_button)
        hbox2.addWidget(self.arc_button)
        hbox2.addWidget(self.sx_button)
        
        
        lbl1 = QLabel('Command: ', self)
        self.lineedit = QLineEdit("")
        self.connect(self.lineedit, SIGNAL("returnPressed()"),
                        self.send_to_server)
        self.response_label = QTextEdit('[No Sever Response Yet]', self)
        self.response_label.setReadOnly(True)
#        self.response_label.setTextColor(QColor("lime"))
#        self.response_label.setTextBackgroundColor(QColor("black"))
        self.response_label.setStyleSheet("QTextEdit { background-color : black; color : lime; }")
        self.response_label.setFixedWidth(400)
        self.response_label.setFixedHeight(160)
       
        hbox1 = QHBoxLayout()
        hbox1.addWidget(lbl1)
        hbox1.addWidget(self.lineedit)
       
        self.status_label = QLabel("", self)
 
        layout = QVBoxLayout()
        layout.addLayout(hbox2)
        layout.addLayout(hbox1)
        layout.addWidget(self.response_label)
        layout.addWidget(self.status_label)
        self.setLayout(layout)
        self.setWindowTitle("RHEA@Subaru Spectrograph")
        self.stimer = QTimer()
        self.ask_for_status()

    def ippower_button_click(self):
        command = "ippower "+str(self.sender().text())
        if self.sender().isChecked():
            command += " on"
        else:
            command += " off"
        print(command)
        response = self.client_socket.send_command(command)
        self.response_label.setText(response)
        return

    def ask_for_status(self):
        command = "status"
        if (self.client_socket.connected):
            response = self.client_socket.send_command(command)
            split_response = response.split(" ", 1)
            if (split_response[0]=="status"):
                self.update_status(split_response[1])
            else:
                self.response_label.setText(response)
        self.stimer.singleShot(2000, self.ask_for_status)

    def update_status(self,response):
        try:
            self.status=json.loads(response)
        except:
            pdb.set_trace()
        #!!! Make this better.
        self.status_label.setText("CCDTemp:{0:5.1f} LJTemp:{1:4.1f} T1:{2:7.4f} T2:{3:6.3f} RH:{4:4.1f} P:{5:6.1f}".\
            format(self.status["CCDTemp"],self.status["LJTemp"],
            self.status["T1"],self.status["T2"],self.status["RH"],self.status["P"]))
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
            


