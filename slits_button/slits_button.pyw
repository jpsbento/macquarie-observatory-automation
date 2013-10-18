#!/usr/bin/env python

#python script that shows a GUI with a radiobutton and a submit button that opens and  closes the telescope slits for the 16" dome. Useful for the windows machine as a GUI for some useful tools of the python software. Requires at least for the labjack server to be running, but if the uber server is on as well, then the capability of the script is enhanced.

#Import the Tkinter and client socket modules
import Tkinter,sys,ttk
import tkMessageBox
#sys.path.append('../common/')
import client_socket

client='uber'
#Setup the connection to the servers. This script can only be ran from inside campus
uber_client = client_socket.ClientSocket("uber","bisquemount")
result1= uber_client.send_command('setDomeTracking off')
result2= uber_client.send_command('override_wx')
#If the uber is not on, then connect to the labjack server. Only slits control here...
if ('Error' in result1) or ('Error' in result2):
    labjack_client = client_socket.ClientSocket("labjack","bisquemount")
    client='labjack'
    result=labjack_client.send_command('ok')
    if 'Error' in result:
        tkMessageBox.showinfo('ERROR','Unsucessful attempt connecting to any server')
        client='None'
        sys.exit()

#print 'Connected to the '+client+' client'

#function to quit program
def quit_command():
    if client=='uber':
        uber_client.send_command('setDomeTracking off')
        uber_client.send_command('override_wx off')
        uber_client.send_command('labjack dome home')
    else:
        labjack_client.send_command('labjack dome home')
    sys.exit()
    


#Define class with the window properties
class Application(Tkinter.Frame):
    def __init__(self, master=None):
        Tkinter.Frame.__init__(self, master)
        self.grid(sticky=Tkinter.N+Tkinter.S+Tkinter.E+Tkinter.W)
        self.createWidgets()
        

    def createWidgets(self):
        top=self.winfo_toplevel()
        top.rowconfigure(0,weight=1)
        top.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
        self.columnconfigure(0,weight=1)
        #Radiobuttons for open and closed slits.
        self.slitsframe=Tkinter.LabelFrame(self, text='Slits control',labelanchor='n')
        self.slitsvar=Tkinter.IntVar()
        self.ROpen=Tkinter.Radiobutton(self.slitsframe, text='Open slits',value=1,variable=self.slitsvar)
        self.ROpen.grid()
        self.RClose=Tkinter.Radiobutton(self.slitsframe, text='Close slits',value=2,variable=self.slitsvar)
        self.RClose.grid()
        self.l=Tkinter.Label(self.slitsframe)
        self.l.grid()
        self.Bsubmit=Tkinter.Button(self.slitsframe, text='Submit',command=self.slits_command)
        self.Bsubmit.grid()
        self.slitsframe.grid(sticky=Tkinter.NW)
        #Radiobuttons for open and closed slits.
        self.domeframe=Tkinter.LabelFrame(self, text='Dome Sync',labelanchor='n')
        self.trackvar=Tkinter.IntVar()
        self.ROpen=Tkinter.Radiobutton(self.domeframe, text='Dome Tracking on',value=1,variable=self.trackvar)
        self.ROpen.grid()
        self.RClose=Tkinter.Radiobutton(self.domeframe, text='Dome Tracking off',value=2,variable=self.trackvar)
        self.RClose.grid()
        self.label=Tkinter.Label(self.domeframe)
        self.label.grid()
        self.Csubmit=Tkinter.Button(self.domeframe, text='Submit',command=self.dometrack_command)
        self.Csubmit.grid()
        self.domeframe.grid(sticky=Tkinter.SW)
        #quit button
        self.quitButton=Tkinter.Button(self, text='Quit',command=quit_command)
        self.quitButton.grid(row=10)

    #Function that is triggered upon pressing the 'submit' button
    def slits_command(self):
        v=self.slitsvar.get()
        if v ==1:
            t='open'
        else:
            t='close'
        #talk to labjack, send intructions
        if client=='labjack': 
            response = labjack_client.send_command('slits '+t)
        else: response = uber_client.send_command('labjack slits '+t)
        #if the word 'slits' is not on the response, something went wrong
        if 'slits' not in response:
            tkMessageBox.showinfo('ERROR','Unsucessful attempt at changing the slits position. Check if labjack server is on and that the slits are powered up')
        else:
            self.l.config(text='Instruction to '+t+' slits sent!')

    #Function that is triggered upon pressing the 'submit' button
    def dometrack_command(self):
        v=self.trackvar.get()
        if v ==1:
            t='on'
        else:
            t='off'
        #talk to labjack, send intructions
        response = uber_client.send_command('setDomeTracking '+t)
        #if the word 'slits' is not on the response, something went wrong
        if 'Tracking' not in response:
            tkMessageBox.showinfo('ERROR','Unsucessful attempt at setting the dome tracking status. Check if the uber server is on.')
        else:
            self.label.config(text='Instruction to turn '+t+' dome tracking sent!')



#go!
app= Application()
app.master.title('Dome slits control')
app.mainloop()



