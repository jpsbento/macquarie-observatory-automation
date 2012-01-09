

class FindPort:

	def findPort(self, device):
		self.device = device
		try: devicefile = open('device_list.txt')
		except Exception: return 'ERROR file "device_list.txt" not found'
		device_list = devicefile.readlines()
		devicefile.close()
		Port = ''
		Port_column = ''
		if device_list[0][0] == '#':
			items = str.split(device_list[0])
			for i in range(0, len(items)):
				if items[i] == 'Port': Port_column = i
				#print items[i]
		else: return 'ERROR 1'
		if IP_column == '' or Port_column == '': return 'ERROR 2'
		for line in device_list:
			item = str.split(line)
			if item[0][0] != '#' and device == item[0]:
				try:
					Port = int(item[Port_column])
				except Exception: print 'ERROR3'
		return int(Port)

