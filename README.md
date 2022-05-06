# NeST-AQM-Tests
NeST tests for comparative analysis of AQM algorithms

Steps to run code using commandline arguements

	$sudo python3 testTopology.py --RtoRdelay 50 --RtoRbandwidth 12 --HtoRdelay 6 --HtoRbandwidth 90 --AppArmorFlag 1

RtoRdelay : Delay in bottleneck link between routers in 'ms' (default : '40ms')
RtoRbandwidth : Bandwidth of bottleneck link between routers in 'mbit' (default : '10mbit')
HtoRdelay : Delay in link between hosts and router in 'ms' (default : '5ms')
HtoRbandwidth : Bandwidth of link between host and router in 'mbit' (defualt : '100mbit')
AppArmorFlag : equals 1 then run script to disable app armor (default : 0)

git clone --recursive https://github.com/meme/myRepo.git FOLDER_NAME
