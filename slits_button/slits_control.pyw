#!c:/Python27/python

#python script that shows a GUI with a radiobutton and a submit button that opens and  closes the telescope slits for the 16" dome. Useful for the windows machine as a GUI for some useful tools of the python software. Requires at least for the labjack server to be running, but if the uber server is on as well, then the capability of the script is enhanced.

#Import the Tkinter and client socket modules
import Tkinter,sys,ttk, time
import tkMessageBox
sys.path.append('../common/')
import client_socket

#import all the parameterfile.py parameters
import parameterfile
# A list of the telescopes we have, comment out all but the telescope you wish to connect with:
telescope_type = parameterfile.telescope_type


#Define class with the window properties
class Application(Tkinter.Frame):
    def __init__(self, master=None):
        root=Tkinter.Tk()
        root.update()
        root.minsize(300,250)
        Tkinter.Frame.__init__(self, master)
        self.grid(sticky=Tkinter.N+Tkinter.S+Tkinter.E+Tkinter.W)
        self.createWidgets()

    client='uber'
    #Setup the connection to the servers. This script can only be ran from inside campus
    uber_client = client_socket.ClientSocket("uber",telescope_type)
    result1= uber_client.send_command('setDomeTracking off')
    result2= uber_client.send_command('override_wx')
    #If the uber is not on, then connect to the labjack server. Only slits control here...
    if ('Error' in result1) or ('Error' in result2):
        labjack_client = client_socket.ClientSocket("labjack",telescope_type)
        client='labjack'
        result=labjack_client.send_command('ok')
        if 'Error' in result:
            tkMessageBox.showinfo('ERROR','Unsucessful attempt connecting to any server')
            self.client='None'
            sys.exit()
    
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
        #self.l=Tkinter.Label(self.slitsframe)
        #self.l.grid()
        self.Bsubmit=Tkinter.Button(self.slitsframe, text='Submit',command=self.slits_command)
        self.Bsubmit.grid()
        self.slitsframe.grid(column=0,row=0, columnspan=1,rowspan=1)#sticky=Tkinter.NW)
        
        #Radiobuttons for open and closed slits.
        self.domeframe=Tkinter.LabelFrame(self, text='Dome Sync',labelanchor='n')
        self.trackvar=Tkinter.IntVar()
        self.ROpen=Tkinter.Radiobutton(self.domeframe, text='Dome Tracking on',value=1,variable=self.trackvar)
        self.ROpen.grid()
        self.RClose=Tkinter.Radiobutton(self.domeframe, text='Dome Tracking off',value=2,variable=self.trackvar)
        self.RClose.grid()
        #self.label=Tkinter.Label(self.domeframe)
        #self.label.grid()
        self.Csubmit=Tkinter.Button(self.domeframe, text='Submit',command=self.dometrack_command)
        self.Csubmit.grid()
        self.domeframe.grid(column=0,row=1, columnspan=1,rowspan=1)#sticky=Tkinter.SW)
        
        #Radiobuttons for improved pointing slits.
        self.domefixframe=Tkinter.LabelFrame(self, text='Stop/Fix Dome',labelanchor='n')
        self.moreinfo=Tkinter.Label(self.domefixframe)
        self.moreinfo.grid()
        self.moreinfo.config(text='Push this button\nif dome does\nnot stop rotating')
        self.Psubmit=Tkinter.Button(self.domefixframe, text='Submit',command=self.domestop_command)
        self.Psubmit.grid()
        self.domefixframe.grid(column=1,row=0, columnspan=1,rowspan=1)#sticky=Tkinter.NE)

        #focuser button
        self.focusButton=Tkinter.Button(self, text='Reset Focuser',command=self.focuser_command)
        self.focusButton.grid(column=1,row=2)
        #reconnection button
        self.reconnectButton=Tkinter.Button(self, text='Reconnect to server',command=self.reconnect_command)
        self.reconnectButton.grid(column=1,row=1)
        #quit button
        #self.quitButton=Tkinter.Button(self, text='Quit',command=self.quit_command)
        #self.quitButton.grid(column=1,row=2)
        #help button
        self.helpButton=Tkinter.Button(self, text='Help',command=self.help_command)
        self.helpButton.grid(column=0,row=2)
        #global label
        self.outputmessage=Tkinter.LabelFrame(self, text='Output Messages',labelanchor='n')
        self.globallabel=Tkinter.Label(self.outputmessage)
        self.globallabel.grid()
        self.outputmessage.grid(sticky=Tkinter.S,columnspan=2)

    #function to quit program
    def quit_command(self):
        if self.client=='uber':
            self.uber_client.send_command('setDomeTracking off')
            time.sleep(1)
            self.uber_client.send_command('labjack dome home')
            time.sleep(1)
            self.uber_client.send_command('override_wx off')
        else:
            self.labjack_client.send_command('labjack dome home')
        sys.exit()
    #Function that is triggered upon pressing the 'submit' button on the Slits control frame
    def slits_command(self):
        v=self.slitsvar.get()
        if v ==1:
            t='open'
        else:
            t='close'
        #talk to labjack, send intructions
        if self.client=='labjack': 
            response = self.labjack_client.send_command('slits '+t)
        else: response = self.uber_client.send_command('labjack slits '+t)
        #if the word 'slits' is not on the response, something went wrong
        print response
        if 'slits' not in response:
            self.uber_client = client_socket.ClientSocket("uber",telescope_type)
            response_after = self.uber_client.send_command('labjack slits'+t)
            if 'slits' not in response_after:
                tkMessageBox.showinfo('ERROR','Unsucessful attempt at changing the slits position. Check if labjack server is on and that the slits are powered up')
        else:
            self.globallabel.config(text='Instruction to '+t+' slits sent!')

    #Function that is triggered upon pressing the 'submit' button on the Dome Sync frame
    def dometrack_command(self):
        v=self.trackvar.get()
        if v ==1:
            t='on'
        else:
            t='off'
        #talk to labjack, send intructions
        try: response = self.uber_client.send_command('setDomeTracking '+t)
        except Exception: pass
        #if the word 'slits' is not on the response, something went wrong
        if 'Tracking' not in response:
            self.uber_client = client_socket.ClientSocket("uber",telescope_type)
            response_after = self.uber_client.send_command('setDomeTracking '+t)
            if 'Tracking' not in response_after:         
                tkMessageBox.showinfo('ERROR','Unsucessful attempt at setting the dome tracking status. Check if the uber server is on.')
        else:
            self.globallabel.config(text='Instruction to turn '+t+' dome tracking sent!')

     #Function that is triggered upon pressing the 'Reset Focuser' button
    def help_command(self):
        tkMessageBox.showinfo('Help','The current version of this software allows the use of particular bits of the linux software to aid the telescope user.\n\nThe parts of the software in place require specific scripts to be working in the linux machine and therefore may fail if they are not. This is particularly true if TheSkyX has been restarted.\n\nIn most option boxes, just select an option and click "Submit".\n\nThe focuser reset option will set the electronic focuser to its default position for the camera/fiberfeed installation. The dome tracking option will use a bunch of tools to couple the dome to the telescope pointing, such that the user never has to mode the dome manually. The pointing improvement will use the camera on the side of the telescope to find the nearest bright object the telescope is pointing at and put it in the centre of the field of view.  ')



    #Function that is triggered upon pressing the 'Reset Focuser' button
    def focuser_command(self):
        #talk to uber, send intructions
        response = self.uber_client.send_command('telescope focusGoToPosition 1000')
        #if the word 'slits' is not on the response, something went wrong
        if 'complete' not in response:
            self.uber_client = client_socket.ClientSocket("uber",telescope_type)
            response_after = self.uber_client.send_command('telescope focusGoToPosition 1000')
            if 'complete' not in response_after:
                tkMessageBox.showinfo('ERROR','Unsucessful attempt at resetting the focuser. Check if the uber server is on.')
        else:
            self.globallabel.config(text='Instruction to reset the focuser sent!')

    #Function that is triggered upon pressing the 'submit' button on the pointing frame
    def domestop_command(self):
        #talk to labjack, send intructions
        response = self.uber_client.send_command('labjack dome stop')
        #if the word 'slits' is not on the response, something went wrong
        if 'stopped' not in response:
            self.uber_client = client_socket.ClientSocket("uber",telescope_type)
            response_after = self.uber_client.send_command('labjack dome stop')
            if 'stopped' not in response_after:
                tkMessageBox.showinfo('ERROR','Unsucessful attempt at stopping dome. Check if the uber server is on.')
        else:
            self.globallabel.config(text='Instruction to stop dome sent!')
    
    def reconnect_command(self):
        #try reconnecting to the servers
        try: self.uber_client = client_socket.ClientSocket("uber",telescope_type)
        except Exception: pass
        response = self.uber_client.send_command('labjack ok')
        if 'reset' in response:
            self.globallabel.config(text='Successfully reconnected to the uber server')
            self.uber_client.send_command('override_wx')
        else:
            self.globallabel.config(text='Can not connect to uber server. Check that it is working.')

#go!
app= Application()
app.master.title('Dome slits control')
app.mainloop()



