import Pyro4
import config as constant
from multiprocessing import Lock
import time
import helpers
import threading


@Pyro4.expose
class gatProcess:
	def __init__(self, ID, daemon, nameServer):
		self.ID = ID
		self.name = "Gateway processing tier"
		self.nameServer = nameServer
		self._registerProcess(daemon, nameServer)

		# maintains state of last device to be queried and it's corresponding lock
		# as the gatway has threads to serve multiple requests
		self.last_query_state = 0
		self.state_lock = threading.Lock()

		# thread sync lock for database
		self.db_lock = threading.Lock()

		# ok signal flag during leader election algorithm
		self.recv_ok = False
		# election done flag which stops further processing of messages
		self.election_done = False
		# lock to process multiple incoming election start messages on one node
		self.election_lock = Lock()
		# id of leader
		self.leader = -1

		# berkely clock sync algo data structures
		self.time_dict = {}
		self.offset = 0.0
		# logical clock counter
		self.logicalCounter = 0

		# these are our test case parameters
		if (constant.constants.initialHomeState=="empty"):
			self.homeState = constant.constants.empty
			self.securitySystem = constant.constants.ON
		elif (constant.constants.initialHomeState=="occupied"):
			self.homeState = constant.constants.occupied
			self.securitySystem = constant.constants.OFF

			# initiates election and is also called if the node receives the election start 
			# signal from another node
	def init_election(self):		
		helpers.init_election(self)
	
	# processing the election message once it is received
	# sends ok signal backs and recursively calls init_election again
	def process_election(self,msg):		
		helpers.process_election(self,msg)		

	# after recv win msg from leader  set leader variables
	def set_leader(self,msg):
		helpers.set_leader(self,msg)

	# receive ok msg
	def ok(self):
		helpers.ok(self)

	# poll clocks for the time sync algorithm
	# using a dedicate thread as a daemon in the background
	def poll_clocks(self):
	    	th = threading.Thread(target=helpers.poll_clocks, args=(self,))
        	th.daemon = True   # Daemonize thread
	        th.start()
        	print "Started Clock Sync Thread. Starting events..."

    # send my own timestamp as a response to poll clock from leader
	def send_timestamp(self,msg):
		helpers.send_timestamp(self,msg)
		return

	# receive the offset value from the dict from the leader
	def set_offset(self,msg):
		offset_dict = msg[3]
		self.offset = offset_dict[self.ID]
		return
		#print "id ", self.ID, "  offset = ", self.offset

	# the leader will receive the timesatamp from other and update dict
	def leader_recv_timestamp(self,msg):
		#senders_time = msg[3]
		from_ = msg[1]
		self.time_dict[from_] = msg[3]
		return

	# main process logic to handle receiving messages at gateway
	# leader elections not threaded
	# event processing threaded
	def receiveMessage(self, msg):
		# distinguish type of messages and calling appropriate functions
		msgType = msg[0]
		if msgType == constant.constants.leaderElectionMsg:
			self.process_election(msg)
		elif msgType == constant.constants.leaderWinMsg:
			self.set_leader(msg)
		elif msgType == constant.constants.logicalClockMsg:
			self.logicalCounter += 1
		# this should not be new thread - queryState should wait for this to finish
		elif msgType == constant.constants.responseMsg:
			self.process_state_response(msg)
		else:
			th = threading.Thread(target=self.threaded_receiveMessage, args=(msg,))
	        	th.daemon = True   # Daemonize thread
		        th.start()

	# function called in threaded manner simiar to receiveMessage
	def threaded_receiveMessage(self,msg):
		msgType = msg[0]
		if msgType==constant.constants.clockSyncMsg:
			self.leader_recv_timestamp(msg)
		elif msgType==constant.constants.clockSyncOffsetMsg:
			self.set_offset(msg)
		elif msgType==constant.constants.clockSyncPollMsg:
			self.send_timestamp(msg)

		
		elif msgType == constant.constants.pushMsg:
			self.store(msg)
			self.eventOrderLogic(msg)

			# pull data from sensors based on only the device id
	def queryState(self,deviceID):
		# this function is called by the 
		#  main logic to get the state of pull-based
		# sensors or smart outlet
		if (deviceID==constant.constants.presenceSensorID):
			print "Gateway can't query presence sensor"
			return

		print("pulling data from the sensors")
		recURI = self.nameServer.lookup(str(deviceID))
		recProxy = Pyro4.Proxy(recURI)
		recProxy.getState() 
		state = self.last_query_state
		self.state_lock.release()
		return state

		# for processing the response to the query
		# print to screen and set the last devide queried state - which
		# will be read by queryState
	def process_state_response(self,msg):
		# just for informative printing 
		state = msg[3]
		deviceID = msg[1]
		time = msg[4]

		self.state_lock.acquire()
		self.last_query_state = state

		if (deviceID==constant.constants.motionSensorID):
			print "The motion sensor state is {} at time {}".format(str(state),time)
		elif (deviceID==constant.constants.doorSensorID):
			print "The door sensor state is {} at time {}".format(str(state),time)
		elif (deviceID==constant.constants.tempSensorID):
			print "The current temperature is {} at time {}".format(str(state),time)
		elif (deviceID==constant.constants.smartBulbID):
			print "Smart Bulb is {} at time {}".format(str(state),time)
		elif (deviceID==constant.constants.smartOutletID):
			print "Smart Outlet is {} at time {}".format(str(state),time)

		# controlling the 2 smart devices
	def sendControlMsg(self,deviceID,state):
		# this function changes the state of the appliances
		# device should either be bulb or outlet
		if (deviceID !=  constant.constants.smartBulbID) and (deviceID != constant.constants.smartOutletID):
			print "Gateway trying to control incorrect devices"
			return

		if state == 1:
			payload = constant.constants.turnOn
		elif state == 0 :
			payload = constant.constants.turnOff
		else:
			print "Wrong outlet state by gateway"
			return

		print("Gateway controlling the state of smart appliances")
		msgType = constant.constants.controlStateMsg
		msg = [msgType, self.ID, deviceID, payload]
		recURI = self.nameServer.lookup(str(deviceID))
		recProxy = Pyro4.Proxy(recURI)
		recProxy.controlState(msg) # this will take care of sending logical clock msg and updating db
		
		# store the push based events to a sequential database
		# also call another func to update a 2nd database file to
		# svae state of each device
	def store(self,msg):
		# this message stores the event/value in the database on tier 2
		recURI = self.nameServer.lookup(str(constant.constants.databaseTierID))
		recProxy = Pyro4.Proxy(recURI)
		self.db_lock.acquire()
		recProxy.insert(msg)
		self.db_lock.release()
		print("Storing event on database")

		deviceID = msg[1]
		state = msg[3]
		# update state in 2nd database
		self.update_device_state_db(deviceID,state)

		# the 2nd db - state_database 
		# update the corresponsing row with the latest state
	def update_device_state_db(self,deviceID,new_state):
		print "Updating Device ID {} state on State Database to {}".format(deviceID,new_state)
		recURI = self.nameServer.lookup(str(constant.constants.databaseTierID))
		recProxy = Pyro4.Proxy(recURI)
		self.db_lock.acquire()
		recProxy.update_device_state(deviceID,new_state)
		self.db_lock.release()

		# complimentary function for above function
		# retreives state of a device from the state_datavase file
	def retreive_device_state_db(self,deviceID):
		recURI = self.nameServer.lookup(str(constant.constants.databaseTierID))
		recProxy = Pyro4.Proxy(recURI)
		state_str = recProxy.retreive_device_state(deviceID)
		return state_str

	def retrieve_last(self):
		# this message retrieves the data from the database when needed
		recURI = self.nameServer.lookup(str(constant.constants.databaseTierID))
		recProxy = Pyro4.Proxy(recURI)
		last_e = recProxy.retrieve_last()
		#print("retrieving data from database")
		return last_e


	def sendMessage(self, msg):
		# if the message is push or response then, msg format = [msgType, sender, receiver, msg]
		# if the message type is selective then, msg format = [msgType, sender, [receivers 1-N], msg]
		# in the selective msg type, receivers should be inside an array even if there is only one
		# if the message is broadcast type, then msg format is msg format = [msgType, sender, receiver, msg]
		# you can put anything at receivers place, it doesn't matter as broadcast mechanism sends msg to everyone
		# except the node itself
		helpers.sendMessage(self,msg)

	def eventOrderLogic(self,msg):
		# activated only in case of push messages
		if (msg[1] == constant.constants.doorSensorID):
			last_event = self.retrieve_last()
			last_event_type = int(last_event[0])
			# empty house and door opern after prsence - let user in
			if (self.homeState == constant.constants.empty and last_event_type==constant.constants.presenceSensorID):
				# check if there is no motion sensed in the recent past
				print("GATEWAY: User has just entered the home with presence. Turning off the security system.")
				self.securitySystem = constant.constants.OFF
				self.homeState = constant.constants.occupied

				# empty house and door opens with no beacon = burgler
			elif (self.homeState == constant.constants.empty and last_event_type!=constant.constants.presenceSensorID):
				# check if there is no motion sensed in the recent past
				print("GATEWAY: ALERT! Intruder opened door without presence sensor Ring Alarm ")
				self.sendControlMsg(constant.constants.smartBulbID,1)		# turn on the bulbs because of the alarms

				# occupied house and door operns after motions
				# let use out
				# turn the lights off
			elif (self.homeState == constant.constants.occupied and last_event_type==constant.constants.motionSensorID):
				# check which event happened first
				print ("GATEWAY: User is leaving the home. Turning on the security system and turn off lights.")
				self.securitySystem = constant.constants.ON
				self.homeState = constant.constants.empty
				self.sendControlMsg(constant.constants.smartBulbID,0)	# turn off the bulbs

				# occupied house but door opern with noe beacon = burgler
			elif (self.homeState == constant.constants.occupied and last_event_type!=constant.constants.motionSensorID):
				# check which event happened first
				print("GATEWAY: ALERT! Intruder opened door without presence sensor Ring Alarm ")
				self.sendControlMsg(constant.constants.smartBulbID,1)

				# motion in an empty house meanse a intruder
				# if occupied house then turn the lights on if not already on
		elif (msg[0] == constant.constants.pushMsg and msg[1] == constant.constants.motionSensorID):
			if (self.homeState == constant.constants.empty):
				print "GATEWAY: ALERT! Motion when house empty - ringing alarms"
			elif (self.homeState == constant.constants.occupied):
				# turn on the lights if not already on
				bulb_state = self.queryState(constant.constants.smartBulbID)
				if bulb_state != constant.constants.turnOn:
					print "GATEWAY: Turn on Lights due to Motion"
					self.sendControlMsg(constant.constants.smartBulbID,1)
	

	def _registerProcess(self, daemon, nameServer):
		processUri = daemon.register(self)
		nameServer.register(str(self.ID), processUri)
		print("{} has been registered with ID: {}").format(self.name, self.ID)
