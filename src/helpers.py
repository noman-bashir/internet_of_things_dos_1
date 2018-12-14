import Pyro4
import time
from multiprocessing import Lock
import config as constant

# common functions mostly relating to clock mechanism
# or leader election seperated to avoid redundancies

# different msg types with similar sending behavious grouped together
selective_msgs = [constant.constants.selectiveMsg, constant.constants.leaderElectionMsg, constant.constants.clockSyncMsg]
response_msgs = [constant.constants.pushMsg, constant.constants.responseMsg]
broadcast_msgs = [constant.constants.broadCastMsg, constant.constants.leaderWinMsg, constant.constants.logicalClockMsg]
clock_msgs = [constant.constants.clockSyncOffsetMsg,constant.constants.clockSyncPollMsg]



def init_election(self):
	#self.is_leader = False
	#self.recv_ok = False
	if self.election_done:
		return

	idList = constant.constants.idList
	recv_list = []
	for i in idList:
		if (self.ID<i):
			recv_list.append(i)

	msgType = constant.constants.leaderElectionMsg
	sender = self.ID
	msgPayLoad = ''
	msg = [msgType, sender, recv_list, msgPayLoad]
	#print "election msg from", self.ID, " -> ", recv_list
	self.sendMessage(msg)
	# send election message to all nodes whose id is less than self

	# time to allow ok signals to come in
	time.sleep(1)

	# if no ok signal received - elect leader
	if not self.recv_ok and not self.election_done:
		# set leader vars
		self.leader = self.ID
		self.election_done = True

		msgType = constant.constants.leaderWinMsg
		sender = self.ID
		msgPayLoad = self.ID
		msg = [msgType, sender, [], msgPayLoad]
		self.sendMessage(msg)
		print "ELECTION DONE: Leader is ", self.name

		time.sleep(1)

		# start clock sync polling
		self.poll_clocks()


	# process election receive msg by sending ok back and calling init_election
def process_election(self,msg):

	sender = msg[1]
	# send ok back 
	recURI = self.nameServer.lookup(str(sender))
	recProxy = Pyro4.Proxy(recURI)
	recProxy.ok()
	# send more elctions

	# or lock here ?
	self.election_lock.acquire()
	self.init_election()
	self.election_lock.release()
	#helpers.process_election()

	

def set_leader(self,msg):
	payload = msg[3]
	leader_id = payload
	self.leader = leader_id
	self.election_done = True


def ok(self):
	if self.election_done:
		return
	self.recv_ok = True



######################################################

def poll_clocks(self):
	
	if not (self.ID == self.leader):
		print "ERORR - polling not done by leader"
		return
	idList = constant.constants.idList

	# keep continuing as a daemon
	while (True):
		self.time_dict = {}

		msgType = constant.constants.clockSyncPollMsg
		sender = self.ID
		msgPayLoad = ''
		msg = [msgType, sender, [], msgPayLoad]
		self.sendMessage(msg)
		self.time_dict[self.ID] = time.time()
		#print "time dict  ", self.time_dict

		# time.sleep(1) ## will it cause un-sync ??	
		# print "22 ", self.time_dict

		if (len(self.time_dict)==len(idList)-1): # no db tier
		# avg calc
			time_dict = self.time_dict
			time_sum = 0.0
			for k in time_dict:
				time_sum += time_dict[k]
			avg_time = time_sum/float(len(idList)-1)

		# send offset
			offsets = {}
			for k in time_dict:
				offsets[k] = avg_time - time_dict[k]

			msgType = constant.constants.clockSyncOffsetMsg
			sender = self.ID
			msgPayLoad = offsets
			msg = [msgType, sender, [], msgPayLoad]

			# set leader's offset
			self.offset = offsets[self.ID]
			#print offsets
			self.sendMessage(msg)

		time.sleep(5)


def send_timestamp(self,msg):
	from_ = msg[1]
	if from_ != self.leader:
		print "ERORR! Leader is not equal to Time Poller"
		return

		# send current time back to leader

	msgType = constant.constants.clockSyncMsg
	recv_list = [from_]
	msg = [msgType, self.ID, recv_list, time.time()]
	self.sendMessage(msg)
	return


#################################

def sendMessage(self, msg):
		# if the message is push or response then, msg format = [msgType, sender, receiver, msg]
		# if the message type is selective then, msg format = [msgType, sender, [receivers 1-N], msg]
		# in the selective msg type, receivers should be inside an array even if there is only one
		# if the message is broadcast type, then msg format is msg format = [msgType, sender, receiver, msg]
		# you can put anything at receivers place, it doesn't matter as broadcast mechanism sends msg to everyone
		# except the node itself
		msgType = msg[0]
		msgSender = msg[1]
		msgReceiver = msg[2]
		if msgType in selective_msgs :
			for i in range(len(msgReceiver)):
				recURI = self.nameServer.lookup(str(msgReceiver[i]))
				recProxy = Pyro4.Proxy(recURI)
				recProxy.receiveMessage(msg)

		elif msgType in response_msgs:
			recURI = self.nameServer.lookup(str(msgReceiver))
			recProxy = Pyro4.Proxy(recURI)
			recProxy.receiveMessage(msg)

		elif msgType == constant.constants.controlStateMsg:
			recURI = self.nameServer.lookup(str(msgReceiver))
			recProxy = Pyro4.Proxy(recURI)
			recProxy.controlState(msg)

		elif msgType == constant.constants.pullMsg:
			recURI = self.nameServer.lookup(str(msgReceiver))
			recProxy = Pyro4.Proxy(recURI)
			recProxy.getState()

		elif msgType in broadcast_msgs:
			procList = constant.constants.idList # list of all the processes
			for i in range(len(procList)):
				if (procList[i] != self.ID):
					recURI = self.nameServer.lookup(str(procList[i]))
					recProxy = Pyro4.Proxy(recURI)
					recProxy.receiveMessage(msg)

		elif msgType in clock_msgs:
			send_time = time.time()
			# TODO send start, end time --- RTT
			procList = constant.constants.idList
			for i in range(len(procList)):
				if (procList[i] != self.ID) and (procList[i] != constant.constants.databaseTierID):
					recURI = self.nameServer.lookup(str(procList[i]))
					recProxy = Pyro4.Proxy(recURI)
					recProxy.receiveMessage(msg)

#################################################

def logicalClock(msg):
	self.sendMessage(self, msg)
