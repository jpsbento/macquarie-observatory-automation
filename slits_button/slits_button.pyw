#!/usr/bin/env python

#python script that shows a GUI with a radiobutton and a submit button that opens and  closes the telescope slits for the 16" dome.

#Import the Tkinter and client socket modules
import Tkinter,sys
import tkMessageBox
#sys.path.append('../common/')
import client_socket

#Setup the connection for the labjack. This script can only be ran from inside campus
labjack_client = client_socket.ClientSocket("labjack","bisquemount")

#Generate the window, with a minimum size and title
root=Tkinter.Tk()
root.minsize(200,100)
root.title('Dome slits control')

#variable that determines which option has been selected
radiovar=Tkinter.IntVar()

#Radiobuttons for open and closed slits.
ROpen=Tkinter.Radiobutton(root, text='Open slits',value=1,variable=radiovar)
ROpen.pack()
RClose=Tkinter.Radiobutton(root, text='Close slits',value=2,variable=radiovar)
RClose.pack()

#Function that is triggered upon pressing the 'submit' button
def submit_command():
    v=radiovar.get()
    if v ==1:
        t='open'
    else:
        t='close'
    #talk to labjack, send intructions
    response = labjack_client.send_command('slits '+t)
    #if the word 'slits' is not on the response, something went wrong
    if 'slits' not in response:
        tkMessageBox.showinfo('ERROR','Unsucessful attempt at changing the slits position. Check if labjack server is on and that the slits are powered up')
    else:
        label.config(text='Instruction to '+t+' slits sent!')

#function to quit program
def quit_command():
    sys.exit()

#setup a simple labelling of the last instruction
label=Tkinter.Label(root)
label.pack()

#Submit and quit buttons
Bsubmit=Tkinter.Button(root, text='Submit',command=submit_command)
Bsubmit.pack(side=Tkinter.LEFT)

Bexit=Tkinter.Button(root, text='Quit',command=quit_command)
Bexit.pack(side=Tkinter.RIGHT)

#go!
root.mainloop()
