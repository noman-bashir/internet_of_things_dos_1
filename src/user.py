import Pyro4
import config as constant
import time
import os

# User process which reads the test case files and starts the entire process
# by calling the appropriate functions in each device

@Pyro4.expose
class user:
	def __init__(self, ID, daemon, nameServer):
		self.ID = ID
		self.name = "User"
		self.nameServer = nameServer
		self._registerProcess(daemon, nameServer)

	def read_file(self,filename):
    #l = []
	    with open(filename, 'r') as fobj:
	        for line in fobj:
	            events = [ch for ch in line.split()]
	    return events

	def start(self,filename):
		try:
	    		os.remove('./database')
		except OSError:
    			pass

		events = self.read_file(filename)
		print 'Events >> ',events

		# events ordered as a timeline
		# with digits indicating time gap
		# D 2 M == door and after 2 seconds motion
		for e in events:
			if e.isdigit():
				t = int(e)
				time.sleep(t)
			elif e[0] == 'T':
				self.get_temp()
			elif e[0] == 'P':
				self.trigger_presence()
			elif e[0] == 'M':
				self.trigger_motion()
			elif e[0] == 'D':
				self.trigger_door()
			elif e[0] == 'B':				
				self.trigger_bulb(int(e[1]))
			elif e[0] == 'O':
				self.trigger_outlet(int(e[1]))

	# direct RPC calls to the approriate sensors for the event
	# which will lead to gateway comm and start the process

	def trigger_motion(self):
		recURI = self.nameServer.lookup(str(constant.constants.motionSensorID))
		recProxy = Pyro4.Proxy(recURI)
		recProxy.triggerMotion()

	def trigger_presence(self):
		recURI = self.nameServer.lookup(str(constant.constants.presenceSensorID))
		recProxy = Pyro4.Proxy(recURI)
		recProxy.detect_presence()

	def trigger_door(self):
		entranceID = constant.constants.validID
		recURI = self.nameServer.lookup(str(constant.constants.doorSensorID))
		recProxy = Pyro4.Proxy(recURI)
		recProxy.openDoor(entranceID)

		# switch on or off the smart devices

		# something like B0 == Bulb turn OFF
		# O1 == outlet turn ON

	def trigger_bulb(self,state):
		if state == 1:
			payload = constant.constants.turnOn
		elif state == 0 :
			payload = constant.constants.turnOff
		else:
			print "Wrong bulb state in user file"

		msgType = constant.constants.userActivityMsg
		msg = [msgType, self.ID, constant.constants.smartBulbID, payload]
		recURI = self.nameServer.lookup(str(constant.constants.smartBulbID))
		recProxy = Pyro4.Proxy(recURI)
		recProxy.controlState(msg)


	def trigger_outlet(self,state):
		if state == 1:
			payload = constant.constants.turnOn
		elif state == 0 :
			payload = constant.constants.turnOff
		else:
			print "Wrong outlet state in user file"

		msgType = constant.constants.userActivityMsg
		msg = [msgType, self.ID, constant.constants.smartOutletID, payload]
		recURI = self.nameServer.lookup(str(constant.constants.smartOutletID))
		recProxy = Pyro4.Proxy(recURI)
		recProxy.controlState(msg)

		# go through the gateway to sense the temperature
		# demonstraing gateways query state ability
	def get_temp(self):
		#entranceID = constant.constants.tempSensorID
		recURI = self.nameServer.lookup(str(constant.constants.processingTierID))
		recProxy = Pyro4.Proxy(recURI)
		#t = recProxy.senseTemperature()
		t = recProxy.queryState(constant.constants.tempSensorID)
		print("Temp is {} - sensed by Gateway").format(t)
		return

		

	def _registerProcess(self, daemon, nameServer):
		processUri = daemon.register(self)
		nameServer.register(str(self.ID), processUri)
		print("{} has been registered with ID: {}").format(self.name, self.ID)

