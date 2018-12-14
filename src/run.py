# This is the code that visits the warehouse.
from gatewaytier1 import gatProcess
import Pyro4
import config as constant
import sys

sys.excepthook = Pyro4.util.excepthook

# can be any random node to start the elction process
receiver = constant.constants.tempSensorID

nameServer = Pyro4.locateNS() # locating name server
uri = nameServer.lookup(str(receiver)) # looking for registered object
recProc = Pyro4.Proxy(uri)
recProc.init_election()

uri = nameServer.lookup(str(constant.constants.userID)) # looking for registered object
recProc = Pyro4.Proxy(uri)

# TEST CASES
# Uncomment one of these 3 test cases files to run that particular case

recProc.start('../test/test1')
#recProc.start('../test/test2')
#recProc.start('../test/test3')