#!/usr/bin/env python

#python script that shows a GUI with a radiobutton and a submit button that opens and  closes the telescope slits for the 16" dome.

#Import the Tkinter and client socket modules
import Tkinter,sys
import tkMessageBox
#sys.path.append('../common/')
import client_socket

client='uber'
#Setup the connection for the labjack. This script can only be ran from inside campus
try: 
    uber_client = client_socket.ClientSocket("uber","bisquemount")
    uber_client.send_command('setDomeTracking off')
    uber_client.send_command('override_wx')
    print 'Successfully connected to the uber server'
except Exception: 
    try: 
        labjack_client = client_socket.ClientSocket("labjack","bisquemount")
        client='labjack'
        labjack_client.send_command('ok')
        print 'Successfully connected to the labjack server'
    except Exception:
        tkMessageBox.showinfo('ERROR','Unsucessful attempt connecting to any server')
        client='None'
        sys.exit()


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
def slits_command():
    v=radiovar.get()
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
        label.config(text='Instruction to '+t+' slits sent!')

#function to quit program
def quit_command():
    if client=='uber':
        uber_client.send_command('setDomeTracking off')
        uber_client.send_command('override_wx off')
        uber_client.send_command('labjack dome home')
    else:
        labjack_client.send_command('dome home')
    sys.exit()
    

#setup a simple labelling of the last instruction
label=Tkinter.Label(root)
label.pack()

#Submit and quit buttons
Bsubmit=Tkinter.Button(root, text='Submit',command=slits_command)
Bsubmit.pack(side=Tkinter.LEFT)

Bexit=Tkinter.Button(root, text='Quit',command=quit_command)
Bexit.pack(side=Tkinter.RIGHT)

#go!
root.mainloop()
