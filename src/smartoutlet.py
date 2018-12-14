# this is smart outlet file.
import Pyro4
import config as constant
from multiprocessing import Lock
import time
import helpers
import threading

@Pyro4.expose
class outlet:
	def __init__(self, ID, daemon, nameServer):
		self.ID = ID 
		self.name = "Smart outlet"
		self.nameServer = nameServer
		self._registerProcess(daemon, nameServer)
		self.outletState = constant.constants.turnOff


		self.recv_ok = False
		#self.is_leader = False
		self.election_done = False
		self.election_lock = Lock()
		self.leader = -1

		self.time_dict = {}
		self.offset = 0.0

		self.logicalCounter = 0

	def init_election(self):		
		helpers.init_election(self)
		
	def process_election(self,msg):		
		helpers.process_election(self,msg)		

	def set_leader(self,msg):
		helpers.set_leader(self,msg)

	def ok(self):
		helpers.ok(self)

	def poll_clocks(self):
		print "Running Clock Sync Thread"
	    	th = threading.Thread(target=helpers.poll_clocks, args=(self,))
        	th.daemon = True   # Daemonize thread
	        th.start()


	def send_timestamp(self,msg):
		helpers.send_timestamp(self,msg)

	def set_offset(self,msg):
		offset_dict = msg[3]
		self.offset = offset_dict[self.ID]
		#print "id ", self.ID, "  offset = ", self.offset
		return


	def leader_recv_timestamp(self,msg):
		#senders_time = msg[3]
		from_ = msg[1]
		self.time_dict[from_] = msg[3]
		return

	def logicalClock(self, msg):
		'''
		if (msg[2] == constant.constants.initLogCloclMsg):
			print("event happened elsewehere, send ack to others")
		elif(msg[2] == constant.constants.ackLogClockMsg):
			print("wait for acks from all of the processes and then increase counter")
		'''	
		self.sendMessage(msg)


	def receiveMessage(self, msg):
		# this function is called by the push-based sensors 
		# to send their state to the gateway
		#print("{} with ID {} is getting data").format(self.name, self.ID)
		msgType = msg[0]
		if msgType == constant.constants.leaderElectionMsg:
			self.process_election(msg)
		elif msgType == constant.constants.leaderWinMsg:
			self.set_leader(msg)
		elif msgType==constant.constants.clockSyncMsg:
			self.leader_recv_timestamp(msg)
		elif msgType==constant.constants.clockSyncOffsetMsg:
			self.set_offset(msg)
		elif msgType==constant.constants.clockSyncPollMsg:
			self.send_timestamp(msg)
		elif msgType== constant.constants.userActivityMsg:
			self.controlState(msg)
		elif msgType == constant.constants.logicalClockMsg:
			if (self.logicalCounter < msg[4]):    # this is done to avoid increasing the counter twice even if 
				self.logicalCounter += 1    	  # the two events have the same time stamp
				#print ("Event update received, increasing counter by 1 to {}").format(self.logicalCounter)



	def controlState(self,msg):
		# this function can be called by the 
		# gateway or the user to change the state of 
		# appliance. sets a global value

		if (constant.constants.useLogicalClock):
			self.logicalCounter += 1
			timestamp = self.logicalCounter
			lClockMsg = [constant.constants.logicalClockMsg, self.ID, constant.constants.broadcastRcvID, '', self.logicalCounter]
			self.logicalClock(lClockMsg)
		else:
			timestamp = time.time() + self.offset


		if (msg[3] == constant.constants.turnOn):
			self.outletState = constant.constants.turnOn
			if (msg[1] == constant.constants.userID):
				print("Event {}: User plugged in a device to the outlet.").format(timestamp)
			else: 
				print("Event {}: Smart outlet was powered on by the gateway.").format(timestamp)
		elif(msg[3] == constant.constants.turnOff):
			self.outletState = constant.constants.turnOff
			if (msg[1] == constant.constants.userID):
				print("Event {}: User plugged out a device from the outlet.").format(timestamp)
			else: 
				print("Event {}: Smart outlet was powered off by the gateway.").format(timestamp)
		
		msg = [constant.constants.pushMsg, self.ID, constant.constants.processingTierID, self.outletState, timestamp]
		self.sendMessage(msg)

	def getState(self):
		# this function is called by the gateway to 
		# get the state of the smart outlet
		print("Responding the outlet state to the gateway.")
		if (constant.constants.useLogicalClock):
			timestamp = self.logicalCounter
		else:
			timestamp = time.time() + self.offset

		msg = [constant.constants.responseMsg, self.ID, constant.constants.processingTierID, self.outletState, timestamp]
		self.sendMessage(msg)


	def sendMessage(self, msg):
		# if the message is push or response then, msg format = [msgType, sender, receiver, msg]
		# if the message type is selective then, msg format = [msgType, sender, [receivers 1-N], msg]
		# in the selective msg type, receivers should be inside an array even if there is only one
		# if the message is broadcast type, then msg format is msg format = [msgType, sender, receiver, msg]
		# you can put anything at receivers place, it doesn't matter as broadcast mechanism sends msg to everyone
		# except the node itself
		helpers.sendMessage(self,msg)

	def _registerProcess(self, daemon, nameServer):
		processUri = daemon.register(self)
		nameServer.register(str(self.ID), processUri)
		print("{} has been registered with ID: {}").format(self.name, self.ID)
