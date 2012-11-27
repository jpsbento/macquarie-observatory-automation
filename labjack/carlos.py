import u3



LJ=u3.U3()
LJ.configIO(NumberOfTimersEnabled = 2)
LJ.getFeedback(u3.Timer0Config(8), u3.Timer1Config(8))

i=0

while i<16:
	print  str(i)+" - "+str(LJ.readRegister(i))+" (FIO"+str(i/2)+")"
	i=i+1
	#print " "
	pass

print LJ.configIO()
