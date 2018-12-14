# How to Run

Note: A pre-req is Pyro4 installed in any standard Linux machine

1. Pyro Nameserver needs to be up
2. Process should be registered 
3. Start the process with specific test cases

1. Start the name server using 

> pyro4-ns

In a diff terminal/machine:
run the registerProcesses.py to register all the processes
*Note: All the output will also come in this terminal/machine*

> cd src
> python registerProcesses.py


In a diff terminal/machine:
use the run.py file to start the process...

> cd src
> python run.py

**Note: some threads run as daemon in background, so when all events done use Ctrl+C to exit the registerProcess terminal**

# Different Test Cases Switch

The script run.py has 3 lines referring to 3 test files. Uncomment the one you would like to test
Description of test cases is in doc/testcases.pdf

**Note: For testcase 2 the initial home state is empty. To do that open src/config.py and set initialHomeState to 'occupied'.**
**For testcases 1 and 3 it initialHomeState should be empty. Both lines present in src/config.py. Uncomment appropriately**

# Switch Between Diff Clock Mechanisms

The default choice is to use logical clocks as the timestamp.
It can be changes using the useLogicalClock attribute in src/config.py
1 denoted using logical clocks and 0 denoted clock sync mechanism

Note that clock sync algorithm continues to run as a daemon, but is not used for event ordering is that flag is set to 1

# Database Structure

2 Database files

 ./database - logs all the events according the timestamps, used in ordering events by fetchinf last timestamped event

 ./state_database - has rows corresponding the each device whose state is of interest, used for recording current state of each device


# Running on Diff Machines

The code is tested and able to run on multiple machines. The object of interest is the pyro Name Server

Set the host-address and port number of the Pyro Name Server Process in src/config.py using the serverAddress and serverPort attributes

