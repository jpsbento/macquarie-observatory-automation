 # This will do EVERYTHING
# will make a way to give it a script

import os, sys
sys.path.append('../common/')
import client_socket
import time, math, datetime, csv
import numpy
from apscheduler.scheduler import Scheduler
from apscheduler.jobstores.shelve_store import ShelveJobStore
import logging
logging.basicConfig()
from timeout import timeout

class SchedServer:
	
	# A list of the telescopes we have, comment out all but the telescope you wish to connect with:
	telescope_type = 'bisquemount'
	#telescope_type = 'meademount'

	# We set clients, one for each device we are talking to
	uber_client = client_socket.ClientSocket("uber",telescope_type)

	#Scheduler parameters
	sched=Scheduler()
	sched.add_jobstore(ShelveJobStore('schedfile'),'schedfile')
	Target='None'
	RA='None'
	DEC='None'
	Mode='None'
	ExposureTime='0'
	NExps='0'
	Filter='None'
	
	def cmd_uber(self,the_command):
		'''A user can still access the low level commands from the imaging source camera using this command. ie
		type 'camera help' to get all the available commands for the imaging source camera server.'''
		commands = str.split(the_command)
		if len(commands) > 1:
			del commands[0]
			command_for_uber = ' '.join(commands)
			response = self.uber_client.send_command(command_for_uber)
			return str(response)
		else: return 'To get a list of commands for the camera type "camera help".'
	
#**************************** Scheduler specific commands ***********************#
	def cmd_Sched(self,the_command):
		'''function to act upon the Scheduler. 
		USAGE: "Sched" returns the status of the scheduler, "Sched <option>" acts upon the scheduler. 
		Type "Sched on" to start the scheduler, "Sched off" to shut it down, and "Sched print" to view the current jobs and indices'''
		commands=str.split(the_command)
		if len(commands)==1:
			return str(self.sched.running)
		if len(commands)==2:
			if commands[1]=='on':
				try: self.sched.start()
				except Exception: return 'Scheduler already running'
				return 'Scheduler active'
			elif commands[1]=='off':
				try: self.sched.shutdown()
				except Exception: return 'Scheduler already shutdown'
				return 'Scheduler stopped'
			elif commands[1]=='print':
				jobs=self.sched.get_jobs()
				l=0
				for i in jobs:
					print str(l), i
					l+=1
			else: return 'Invalid option'

	def cmd_AddJob(self,the_command):
		'''Function to Adds jobs to the scheduler. 
		   USAGE: 
		           Option 1: "AddJob file <filename>" where the filename parameter is the name of the file containing a job list (see example_sched.txt for format)
			   Option 2: "AddJob <Type> <date> <time> <Target> <RA> <DEC> <Mode> <ExposureTime> <NExps> <Filter>"  See example_sched.txt for formats'''
		commands=str.split(the_command)
		if commands[1]=='file':
			#do whatever you need to get the file in
			try: ifile=open(commands[2])
			except Exception: return 'Could not open the file.'
			reader=csv.reader(ifile)
			try: 
				for row in reader:
					print row
					if not '#' in row[0] and len(row)>1:
						print row
						c=[]
						for i in row:
							#get rid of any spaces or tabs
							c.append("".join(i.split()))
						l=c[3:]
						if c[0]=='Cal':
							try: self.sched.add_date_job(self.SchedCalibration,c[1]+' '+c[2],l)
							except Exception: return 'unable to add this calibration job to the queue. Check the help for the correct syntax.'
						if c[0]=='Obj':
							try: self.sched.add_date_job(self.SchedObject,c[1]+' '+c[2],l)
							except Exception: return 'unable to add this object job to the queue. Check the help for the correct syntax.'
						else: return 'Invalid job type. It should either be "Cal" or "Obj"'
			except Exception: return 'Unable to add jobs in file to the queue.'
			return 'Sucessfully imported schedule file and updated the queue'
		else:
			l=commands[4:]
			if commands[1]=='Cal':
				try: self.sched.add_date_job(self.SchedCalibration,commands[2]+' '+commands[3],l)
				except Exception: return 'unable to add this calibration job to the queue. Check the help for the correct syntax.'
			if commands[1]=='Obj':
				try: self.sched.add_date_job(self.SchedObject,commands[2]+' '+commands[3],l)
				except Exception: return 'unable to add this object job to the queue. Check the help for the correct syntax.'
			else: return 'Invalid job type. It should either be "Cal" or "Obj"'
			return 'Successfully added the job to the queue.'
	
	def SchedObject(self,target,ra,dec,mode,exp,nexps,f):
		print time.asctime(),'Started job'
		#Routine that triggers the telescope to move to an object and start stuff. 
		dummy=self.uber_client.send_command('Imaging off')
		dummy=self.uber_client.send_command('guiding off')
		try: self.Target,self.RA,self.DEC,self.Mode,self.ExposureTime,self.NExps,self.Filter=target,ra,dec,mode,exp,nexps,f
		except Exception: print 'Unable to define the job settings' 
		if self.Mode=='RheaGuiding':
			try: 
				response = self.uber_client.send_command('labjack slits')
				if not 'True' in response: dummy=self.uber_client.send_command('labjack slits open')
				response = self.uber_client.send_command('telescope telescopeConnect')
				response = self.uber_client.send_command('checkIfReady Weather Dome Telescope Fiberfeed Sidecam Focuser')
			except Exception: print 'Something went wrong with checking if the slits are open or the telescope is connected'
			response = self.uber_client.send_command('checkIfReady Weather Dome Telescope Fiberfeed Sidecam Focuser')
			if not 'Ready' in response: 
				print response
				return 0
			try: response = self.uber_client.send_command('telescope SlewToObject '+self.Target)
			except Exception: 
				print 'Something went wrong with trying to slew directly to target name'
			if not 'Telescope Slewing' in response:
				if ':' in self.RA:
					#convert the hh:mm:ss.s and dd:mm:sec format to decimal hours and degrees for the slewToRaDec function
					temp=numpy.float64(self.RA.split(':'))
					newRA=str(temp[0]+temp[1]/60.+temp[2]/3600.)
					temp=numpy.float64(self.DEC.split(':'))
					newDEC=str(temp[0]+temp[1]/60.+temp[2]/3600.)
					try: response=self.uber_client.send_command('telescope slewToRaDec '+newRA+' '+newDEC)
					except Exception: return 'Unable to intruct to telescope to slew to an RA and DEC'
				else:
					try: response=self.uber_client.send_command('telescope slewToRaDec '+self.RA+' '+self.DEC)
					except Exception: return 'Unable to intruct to telescope to slew to an RA and DEC'
			#Wait for slew
			while not 'Done' in self.uber_client.send_command('telescope IsSlewComplete'): time.sleep(1)
			#Slew dome to telescope
			while abs(float(str.split(self.uber_client.send_command('labjack dome location'))[0]) - float(str.split(self.uber_client.send_command('telescope SkyDomeGetAz'),'|')[0])) > 3.5: time.sleep(1)
			while not 'Ready' in self.uber_client.send_command('checkIfReady Weather Dome Telescope Fiberfeed Sidecam Focuser'): time.sleep(1)
			try: response=self.uber_client.send_command('masterAlign')
			except Exception: return 'For some reason could not get the master Align routine to work'
			if not 'Finished the master' in response: return 'Failed the master align with the error: '+response
			else: time.sleep(1)
			while not 'Ready' in self.uber_client.send_command('checkIfReady Weather Dome Telescope Fiberfeed Sidecam Focuser'): time.sleep(1)
			try: response = self.uber_client.send_command('guiding on')
			except Exception: return 'Something went wrong with activating the guiding'
			if not 'enabled' in response: return 'Guiding loop not enabled'
			return 'Successfully got a RHEA guiding test going'

		elif self.Mode=='RheaFull':
			try: 
				response = self.uber_client.send_command('labjack slits')
				if not 'True' in response: dummy=self.uber_client.send_command('labjack slits open')
				response = self.uber_client.send_command('telescope telescopeConnect')
				response = self.uber_client.send_command('checkIfReady Weather Dome Telescope Fiberfeed Sidecam Focuser')
			except Exception: print 'Something went wrong with checking if the slits are open or the telescope is connected'
			while not 'Ready' in self.uber_client.send_command('checkIfReady Weather Dome Telescope Fiberfeed Sidecam Focuser Camera LabjackU6'):
				print response
				time.sleep(1)
			try: response = self.telescope_client.send_command('SlewToObject '+self.Target)
			except Exception: 
				print 'Something went wrong with trying to slew directly to target name'
			if not 'Telescope Slewing' in response:
				if ':' in self.RA:
					#convert the hh:mm:ss.s and dd:mm:sec format to decimal hours and degrees for the slewToRaDec function
					temp=numpy.float64(self.RA.split(':'))
					newRA=str(temp[0]+temp[1]/60.+temp[2]/3600.)
					temp=numpy.float64(self.DEC.split(':'))
					newDEC=str(temp[0]+temp[1]/60.+temp[2]/3600.)
					try: response=self.telescope_client.send_command('slewToRaDec '+newRA+' '+newDEC)
					except Exception: return 'Unable to intruct to telescope to slew to an RA and DEC'
				else:
					try: response=self.telescope_client.send_command('slewToRaDec '+self.RA+' '+self.DEC)
					except Exception: return 'Unable to intruct to telescope to slew to an RA and DEC'
			while not 'Done' in self.telescope_client.send_command('IsSlewComplete'): time.sleep(1)
			while abs(float(str.split(self.uber_client.send_command('labjack dome location'))[0]) - float(str.split(self.uber_client.send_command('telescope SkyDomeGetAz'),'|')[0])) > 3.5: time.sleep(1)
			while not 'Ready' in self.uber_client.send_command('checkIfReady Weather Dome Telescope Fiberfeed Sidecam Focuser'): time.sleep(1)
			try: response=self.cmd_masterAlign('masterAlign')
			except Exception: return 'For some reason could not get the master Align routine to work'
			if not 'Finished the master' in response: return 'Failed the master align with the error: '+response
			try: response = self.uber_client.send_command('focusStar')
			except Exception: return 'ERROR: could not focus star'
			if not 'Successfully optimised' in response: return response 
			try: response = self.cmd_guiding('guiding on')
			except Exception: return 'Something went wrong with activating the guiding'
			if not 'enabled' in response: return 'Guiding loop not enabled'
			#Now activate the imaging
			try: dummy=self.uber_client.send_command('Imsettings '+str(self.ExposureTime)+' open')
			except Exception: return 'Something failed when trying to set the exposure settings'
			if not 'Finished' in dummy: return 'ERROR: could not set the exposure settings'
			try: dummy=self.uber_client.send_command('Imaging on lamp')
			except Exception: return 'Something failed when trying to start exposing with RHEA'
			if not 'Finished' in dummy: return 'ERROR: could not start exposing.'
			return 'Successfully got a Full RHEA steup going.'
		elif self.Mode=='Phot':
			#THIS PART IS NOT FINISHED YET. NEED TO UPDATE WHEN OTHER THINGS BECOME DECIDED
			response = self.cmd_checkIfReady(Weather=True,Dome=True,Telescope=True,Sidecam=True,Camera=True)
			if not 'Ready' in response: 
				print response
				return 0
			try: response = self.telescope_client.send_command('SlewToObject '+self.Target)
			except Exception: 
				print 'Something went wrong with trying to slew directly to target name'
			if not 'Telescope Slewing' in response:
				if ':' in self.RA:
					#convert the hh:mm:ss.s and dd:mm:sec format to decimal hours and degrees for the slewToRaDec function
					temp=numpy.float64(self.RA.split(':'))
					newRA=str(temp[0]+temp[1]/60.+temp[2]/3600.)
					temp=numpy.float64(self.DEC.split(':'))
					newDEC=str(temp[0]+temp[1]/60.+temp[2]/3600.)
					try: response=self.telescope_client.send_command('slewToRaDec '+newRA+' '+newDEC)
					except Exception: return 'Unable to intruct to telescope to slew to an RA and DEC'
				else:
					try: response=self.telescope_client.send_command('slewToRaDec '+self.RA+' '+self.DEC)
					except Exception: return 'Unable to intruct to telescope to slew to an RA and DEC'
			while not 'Done' in self.telescope_client.send_command('IsSlewComplete'): time.sleep(1)
			#ADD STUFF HERE ABOUT HOW THE CAMERA IS GOING TO RUN
		else: return 'Unrecognised observing object mode specified'
		return 'Succesfull Object job executed.'

	def SchedCalibration(self,options):
		#Routine to take calibration frames, depending on the options.
		return 1

