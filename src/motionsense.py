import Pyro4
import config as constant
from multiprocessing import Lock
import time
import helpers
import threading

@Pyro4.expose
class motion:
	def __init__(self, ID, daemon, nameServer):
		# these are the initial values of the variables that are 
		# set when the node register itself with the name server                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
		self.ID = ID
		self.name = "Motion sensor"
		self.nameServer = nameServer
		self._registerProcess(daemon, nameServer)
		# false is no motion, true is motion
		self.motionState = 'MOTION-OFF'
		self.last_motion_time = 0.0

		self.recv_ok = False
		#self.is_leader = False

		# election done flag which stops further processing of messages
		self.election_done = False

		# lock to process multiple incoming election start messages on one node
		self.election_lock = Lock()

		# id of leader
		self.leader = -1

		self.time_dict = {}
		self.offset = 0.0

		self.logicalCounter = 0

	def init_election(self):		
		helpers.init_election(self)

		# processing the election message once it is received
		# sends ok signal backs and recursively calls init_election again
	def process_election(self,msg):		
		helpers.process_election(self,msg)		

		# after recv win msg from leader  set leader variables
	def set_leader(self,msg):
		helpers.set_leader(self,msg)

	def ok(self):
		helpers.ok(self)

		# poll clocks for the time sync algorithm
		# using a dedicate thread as a daemon in the background
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


	def leader_recv_timestamp(self,msg):
		#senders_time = msg[3]
		from_ = msg[1]
		self.time_dict[from_] = msg[3]
		return

	def logicalClock(self, msg):
		self.sendMessage(msg)



	def receiveMessage(self, msg):
		# this function is called by the push-based sensors 
		# to send their state to the gateway
		sender = msg[1]
		#print("{} with ID {} is getting data from {}").format(self.name, self.ID, sender)
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
		elif msgType == constant.constants.logicalClockMsg:
			if (self.logicalCounter < msg[4]):    # this is done to avoid increasing the counter twice even if 
				self.logicalCounter += 1    	  # the two events have the same time stamp
				#print ("Event update received, increasing counter by 1 to {}").format(self.logicalCounter)


	def triggerMotion(self):
		
		# this function is called by the user process 
		# to cause motion. When triggered, it will call
		# send motion signal function
		self.motionState = 'MOTION-ON'
		self.last_motion_time = time.time()

		if (constant.constants.useLogicalClock):
			self.logicalCounter += 1
			timestamp = self.logicalCounter
		else:
			timestamp = time.time() + self.offset
		

		print("Event {}: Sensor has sensed motion.").format(timestamp)		
		msg = [constant.constants.pushMsg, self.ID, constant.constants.processingTierID, self.motionState, timestamp]
		self.sendMessage(msg)

		if constant.constants.useLogicalClock:
			lClockMsg = [constant.constants.logicalClockMsg, self.ID, constant.constants.broadcastRcvID, '', self.logicalCounter]
			self.logicalClock(lClockMsg)

		th = threading.Thread(target=self.revert_state)
	        th.daemon = True   # Daemonize thread
        	th.start()

	def revert_state(self):
		# close motion after 2 seconds of last door open 
		while(self.motionState=='MOTION-ON'):
			t = time.time()
			if (t - self.last_motion_time>=1.0):
				self.motionState = 'MOTION-OFF'
				recURI = self.nameServer.lookup(str(constant.constants.processingTierID))
				recProxy = Pyro4.Proxy(recURI)
				recProxy.update_device_state_db(self.ID,'MOTION-OFF')
		return

	def getState(self):
		# respond state
		print("Responding the motion state to the gateway.")
		if constant.constants.useLogicalClock:
			timestamp = self.logicalCounter
		else:
			timestamp = time.time() + offset

		msg = [constant.constants.responseMsg, self.ID, constant.constants.processingTierID, self.motionState, timestamp]
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
