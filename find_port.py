import os

class FindPort:

	def __init__(self,device):
		self.device = device
		try: devicefile = open('device_list.txt')
		except Exception: print 'ERROR file "device_list.txt" not found'
		device_list = devicefile.readlines()
		Port = ''
		Port_column = ''
		if device_list[0][0] == '#':
			items = str.split(device_list[0])
			for i in range(0, len(items)):
				if items[i] == 'Port': Port_column = i
				#print items[i]
		else: return 'ERROR 1'
		if IP_column == '' or Port_column == '': print 'ERROR 2'
		for line in device_list:
			item = str.split(line)
			if item[0][0] != '#' and device == item[0]:
				try:
					IP = item[IP_column]
					Port = int(item[Port_column])
				except Exception: print 'ERROR3'
		return str(Port)

