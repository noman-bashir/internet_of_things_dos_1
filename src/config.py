class constants:

	serverAddress = "localhost"
	serverPort = 9090

	# to use logical clock or not
	# if =0 then clock sync will be used
	useLogicalClock = 1

	# to be set according to the scenario being tested
	# uncomment one of these lines
	# in given testcases , test2 should be occupied initially
	initialHomeState = "empty"
	#initialHomeState = "occupied"


	# assigning IDs to the processes

	totalProcesses = 7 			# this doesn't include user process

	userID = 0
	doorSensorID = 1
	tempSensorID = 2
	motionSensorID = 3
	presenceSensorID = 4
	smartBulbID = 5
	smartOutletID = 6
	databaseTierID = 7
	processingTierID = 8 
	broadcastRcvID = 99

	idList = [1, 2, 3, 4, 5, 6, 7, 8] # maintaining the list as IDs can be assigned 
	# by any other sophisticated mechanism


	# different message types

	userActivityMsg = 0
	pushMsg = 1
	controlStateMsg = 2
	pullMsg = 3
	leaderElectionMsg = 40
	leaderWinMsg = 41
	clockSyncMsg = 50
	clockSyncPollMsg = 51
	clockSyncOffsetMsg = 52
	logicalClockMsg = 60
	initLogCloclMsg = 61
	ackLogClockMsg = 62
	responseMsg = 7
	selectiveMsg = 8
	broadCastMsg = 9

	# control signals

	turnOn = 'ON'
	turnOff = 'OFF'

	# burglar vs legit user

	validID = 1
	invalidID = 0

	# motion state

	motionSensed = 1
	motionNotSensed = 0

	# temperature limits

	lowestTemp = 10
	highestTemp = 60

	dummyPayload = 9999

	occupied = 1 # if user is at home
	empty = 0 # if user is outside

	ON = 1
	OFF = 0