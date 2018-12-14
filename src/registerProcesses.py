import Pyro4
import config as constants
from doorsense import door
from tempsense import temperature
from motionsense import motion
from presencesense import presence
from smartbulb import bulb
from smartoutlet import outlet
from gatewaytier1 import gatProcess
from gatewaytier2 import gatDatabase
from user import user


daemon = Pyro4.Daemon()

nameServer = Pyro4.locateNS(constants.constants.serverAddress, constants.constants.serverPort)

door(constants.constants.doorSensorID, daemon, nameServer)
temperature(constants.constants.tempSensorID, daemon, nameServer)
motion(constants.constants.motionSensorID, daemon, nameServer)
presence(constants.constants.presenceSensorID, daemon, nameServer)
bulb(constants.constants.smartBulbID, daemon, nameServer)
outlet(constants.constants.smartOutletID, daemon, nameServer)
gatProcess(constants.constants.processingTierID, daemon, nameServer)
gatDatabase(constants.constants.databaseTierID, daemon, nameServer)
user(constants.constants.userID, daemon, nameServer)

print("All processes have been registered.")
daemon.requestLoop()